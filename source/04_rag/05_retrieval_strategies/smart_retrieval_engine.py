from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, Sequence

from retrieval_basics import (
    BackendName,
    DEFAULT_CANDIDATE_K,
    DEFAULT_CHROMA_DIR,
    DEFAULT_HYBRID_ALPHA,
    DEFAULT_JSON_STORE_PATH,
    DEFAULT_MMR_LAMBDA,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TOP_K,
    EmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleCrossReranker,
    SourceChunk,
    build_demo_retriever,
    demo_source_chunks,
    hybrid_search,
)
from retrieval_metrics import (
    RetrievalEvalCase,
    RetrievalEvaluationReport,
    evaluate_retrieval_cases,
)


SmartStrategyName = Literal["similarity", "threshold", "mmr", "hybrid"]


@dataclass(frozen=True)
class SmartRetrievalConfig:
    strategy: SmartStrategyName = "similarity"
    top_k: int = DEFAULT_TOP_K
    candidate_k: int = DEFAULT_CANDIDATE_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    mmr_lambda: float = DEFAULT_MMR_LAMBDA
    hybrid_alpha: float = DEFAULT_HYBRID_ALPHA
    filename_filter: str | None = None
    rerank: bool = False
    fetch_k: int | None = None
    rerank_top_n: int | None = None

    def __post_init__(self) -> None:
        if self.strategy not in {"similarity", "threshold", "mmr", "hybrid"}:
            raise ValueError(f"Unsupported strategy: {self.strategy}")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive.")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k.")
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0.")
        if not 0.0 <= self.mmr_lambda <= 1.0:
            raise ValueError("mmr_lambda must be between 0.0 and 1.0.")
        if not 0.0 <= self.hybrid_alpha <= 1.0:
            raise ValueError("hybrid_alpha must be between 0.0 and 1.0.")
        if self.fetch_k is not None and self.fetch_k < self.top_k:
            raise ValueError("fetch_k must be greater than or equal to top_k.")
        if self.rerank_top_n is not None and self.rerank_top_n <= 0:
            raise ValueError("rerank_top_n must be positive.")


class SmartRetrievalEngine:
    def __init__(
        self,
        retriever,
        *,
        corpus: Sequence[SourceChunk],
        reranker: SimpleCrossReranker | None = None,
    ) -> None:
        self.retriever = retriever
        self.provider = retriever.provider
        self.corpus = list(corpus)
        self.reranker = reranker or SimpleCrossReranker()

    def retrieve(
        self,
        question: str,
        config: SmartRetrievalConfig,
    ):
        coarse_k = config.fetch_k if config.rerank and config.fetch_k is not None else config.top_k

        if config.strategy == "hybrid":
            results = self._retrieve_hybrid(question, config, coarse_k=coarse_k)
        else:
            results = self.retriever.retrieve(
                question,
                RetrievalStrategyConfig(
                    strategy_name=config.strategy,
                    top_k=coarse_k,
                    candidate_k=max(config.candidate_k, coarse_k),
                    score_threshold=config.score_threshold,
                    mmr_lambda=config.mmr_lambda,
                    filename_filter=config.filename_filter,
                ),
            )

        if config.rerank:
            top_n = config.rerank_top_n or config.top_k
            return self.reranker.rerank(question, results, top_n=top_n)

        return results[: config.top_k]

    def evaluate(
        self,
        test_cases: Sequence[RetrievalEvalCase],
        config: SmartRetrievalConfig,
    ) -> RetrievalEvaluationReport:
        return evaluate_retrieval_cases(
            test_cases,
            lambda case: self.retrieve(
                case.question,
                replace(
                    config,
                    filename_filter=case.filename_filter or config.filename_filter,
                ),
            ),
        )

    def _retrieve_hybrid(
        self,
        question: str,
        config: SmartRetrievalConfig,
        *,
        coarse_k: int,
    ):
        vector_k = max(coarse_k, config.candidate_k)
        vector_results = self.retriever.retrieve(
            question,
            RetrievalStrategyConfig(
                strategy_name="similarity",
                top_k=vector_k,
                candidate_k=vector_k,
                filename_filter=config.filename_filter,
            ),
        )
        bm25_scorer = self._build_bm25_scorer(filename_filter=config.filename_filter)
        return hybrid_search(
            query=question,
            vector_results=vector_results,
            bm25_scorer=bm25_scorer,
            alpha=config.hybrid_alpha,
            top_k=coarse_k,
        )

    def _build_bm25_scorer(self, filename_filter: str | None = None):
        if filename_filter is None:
            filtered_corpus = self.corpus
        else:
            filtered_corpus = [
                chunk
                for chunk in self.corpus
                if chunk.metadata.get("filename") == filename_filter
            ]
        from retrieval_basics import SimpleBM25Scorer

        return SimpleBM25Scorer(filtered_corpus)


def build_demo_smart_engine(
    backend: BackendName,
    provider: EmbeddingProvider | None = None,
    *,
    reset_store: bool = False,
    json_store_path: Path | None = None,
    chroma_persist_directory: Path | None = None,
):
    retriever, store = build_demo_retriever(
        backend=backend,
        provider=provider,
        reset_store=reset_store,
        json_store_path=(
            json_store_path if json_store_path is not None else DEFAULT_JSON_STORE_PATH
        ),
        chroma_persist_directory=(
            chroma_persist_directory
            if chroma_persist_directory is not None
            else DEFAULT_CHROMA_DIR
        ),
    )
    return SmartRetrievalEngine(retriever, corpus=demo_source_chunks()), store
