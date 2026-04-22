from __future__ import annotations

from dataclasses import dataclass

from app.embeddings.providers import EmbeddingProvider
from app.embeddings.similarity import cosine_similarity
from app.retrievers.base import Retriever
from app.schemas import RetrievalResult
from app.vectorstores.chroma_store import ChromaVectorStore, MetadataFilter

SUPPORTED_RETRIEVAL_STRATEGIES = {"similarity", "threshold", "mmr"}


@dataclass(slots=True)
class RetrievalStrategyConfig:
    """Retriever-side controls layered on top of the Phase 4 vector store."""

    strategy_name: str = "similarity"
    candidate_k: int = 8
    score_threshold: float | None = None
    mmr_lambda: float = 0.35
    metadata_filter: MetadataFilter | None = None


@dataclass(slots=True)
class ChromaRetriever(Retriever):
    """Retriever wrapper that turns Chroma queries into stable retrieval policies."""

    store: ChromaVectorStore
    provider: EmbeddingProvider
    config: RetrievalStrategyConfig

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        if top_k <= 0:
            raise ValueError("Top-k must be positive.")
        if self.config.strategy_name not in SUPPORTED_RETRIEVAL_STRATEGIES:
            raise ValueError(
                "Unsupported retrieval strategy. Expected one of: "
                f"{', '.join(sorted(SUPPORTED_RETRIEVAL_STRATEGIES))}."
            )
        if self.config.candidate_k <= 0:
            raise ValueError("Candidate-k must be positive.")
        if not 0.0 <= self.config.mmr_lambda <= 1.0:
            raise ValueError("MMR lambda must be between 0 and 1.")

        if self.config.strategy_name == "similarity":
            return self.store.similarity_search(
                question=question,
                provider=self.provider,
                top_k=top_k,
                where=self.config.metadata_filter,
            )

        query_vector = self.provider.embed_query(question)
        candidates = self.store.similarity_search_by_vector(
            query_vector=query_vector,
            top_k=max(top_k, self.config.candidate_k),
            where=self.config.metadata_filter,
        )
        filtered = _apply_score_threshold(candidates, self.config.score_threshold)

        if self.config.strategy_name == "threshold":
            return filtered[:top_k]

        return maximal_marginal_relevance(
            query_vector=query_vector,
            candidates=filtered,
            provider=self.provider,
            top_k=top_k,
            lambda_multiplier=self.config.mmr_lambda,
        )


def maximal_marginal_relevance(
    query_vector: list[float],
    candidates: list[RetrievalResult],
    provider: EmbeddingProvider,
    top_k: int,
    lambda_multiplier: float = 0.35,
) -> list[RetrievalResult]:
    """Diversify similar candidates while keeping them relevant to the query."""

    if top_k <= 0:
        raise ValueError("Top-k must be positive.")
    if not 0.0 <= lambda_multiplier <= 1.0:
        raise ValueError("MMR lambda must be between 0 and 1.")
    if not candidates:
        return []

    candidate_vectors = provider.embed_documents(
        [item.chunk.content for item in candidates]
    )
    remaining_indices = list(range(len(candidates)))
    selected_indices: list[int] = []

    while remaining_indices and len(selected_indices) < top_k:
        best_index = remaining_indices[0]
        best_score = float("-inf")

        for index in remaining_indices:
            relevance = candidates[index].score
            if relevance is None:
                relevance = cosine_similarity(query_vector, candidate_vectors[index])

            diversity_penalty = 0.0
            if selected_indices:
                diversity_penalty = max(
                    cosine_similarity(candidate_vectors[index], candidate_vectors[selected])
                    for selected in selected_indices
                )

            mmr_score = (
                lambda_multiplier * relevance
                - (1.0 - lambda_multiplier) * diversity_penalty
            )
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        selected_indices.append(best_index)
        remaining_indices.remove(best_index)

    return [candidates[index] for index in selected_indices]


def _apply_score_threshold(
    candidates: list[RetrievalResult],
    score_threshold: float | None,
) -> list[RetrievalResult]:
    if score_threshold is None:
        return candidates
    return [
        item
        for item in candidates
        if item.score is not None and item.score >= score_threshold
    ]
