from __future__ import annotations

from retrieval_basics import (
    EmbeddingProvider,
    RetrievalStrategyConfig,
    SearchHit,
    hits_to_results,
    select_search_hits,
)
from chroma_store import ChromaVectorStore


class ChromaRetriever:
    def __init__(
        self,
        store: ChromaVectorStore,
        provider: EmbeddingProvider,
    ) -> None:
        self.store = store
        self.provider = provider

    def retrieve(
        self,
        question: str,
        strategy: RetrievalStrategyConfig,
    ):
        query_vector = self.provider.embed_query(question)
        candidates = self._search_candidates(
            query_vector=query_vector,
            candidate_k=strategy.candidate_k,
            filename_filter=strategy.filename_filter,
        )
        return hits_to_results(select_search_hits(query_vector, candidates, strategy))

    def _search_candidates(
        self,
        query_vector: list[float],
        candidate_k: int,
        filename_filter: str | None = None,
    ) -> list[SearchHit]:
        where = {"filename": filename_filter} if filename_filter else None
        raw_results = self.store.similarity_search(
            query_vector=query_vector,
            provider=self.provider,
            top_k=candidate_k,
            where=where,
        )
        if not raw_results:
            return []

        embedded_chunks = self.store.load_chunks(where=where)
        chunk_by_id = {chunk.chunk.chunk_id: chunk for chunk in embedded_chunks}
        hits: list[SearchHit] = []
        for result in raw_results:
            embedded_chunk = chunk_by_id.get(result.chunk.chunk_id)
            if embedded_chunk is None:
                raise ValueError(
                    f"Chroma candidate {result.chunk.chunk_id} could not be rehydrated as an EmbeddedChunk."
                )
            hits.append(
                SearchHit(
                    embedded_chunk=embedded_chunk,
                    similarity_score=float(result.score),
                )
            )
        return hits
