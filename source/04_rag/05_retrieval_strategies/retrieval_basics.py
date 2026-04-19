from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sys


CHAPTER_ROOT = Path(__file__).resolve().parent
CHAPTER4_ROOT = CHAPTER_ROOT.parent / "04_vector_databases"
DEFAULT_STORE_PATH = CHAPTER_ROOT / "store" / "demo_retrieval_store.json"
DEFAULT_BAD_CASES_PATH = CHAPTER_ROOT / "evals" / "retrieval_bad_cases.json"

if str(CHAPTER4_ROOT) not in sys.path:
    sys.path.insert(0, str(CHAPTER4_ROOT))

from vector_store_basics import (  # noqa: E402
    EmbeddedChunk,
    EmbeddingProvider,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    RetrievalResult,
    SourceChunk,
    VectorStoreConfig,
    cosine_similarity,
    demo_chunk_metadata,
    embed_chunks,
    embedding_space_from_provider,
    ensure_same_embedding_space,
    ensure_vector_dimensions,
)


@dataclass(frozen=True)
class RetrievalStrategyConfig:
    strategy_name: str
    top_k: int = 3
    candidate_k: int = 5
    score_threshold: float = 0.80
    mmr_lambda: float = 0.65
    filename_filter: str | None = None

    def __post_init__(self) -> None:
        if self.strategy_name not in {"similarity", "threshold", "mmr"}:
            raise ValueError(f"Unsupported strategy: {self.strategy_name}")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive.")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k.")
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0.")
        if not 0.0 <= self.mmr_lambda <= 1.0:
            raise ValueError("mmr_lambda must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class SearchHit:
    embedded_chunk: EmbeddedChunk
    similarity_score: float


@dataclass(frozen=True)
class BadCaseEvaluation:
    strategy_name: str
    status: str
    messages: tuple[str, ...]


def demo_source_chunks() -> list[SourceChunk]:
    refund_policy = "退款规则：购买后 7 天内且学习进度不超过 20%，可以申请全额退款。"
    refund_summary = "退款政策摘要：7 天内且学习进度不超过 20%，支持全额退费。"
    refund_duplicate = "退款说明：购买后 7 天内且学习进度不超过 20%，支持全额退款。"
    refund_process = "退费申请流程：在学习后台提交退款申请，审核通过后原路退回。"
    trial_policy = "课程支持一次 30 分钟免费试学，需要提前预约。"
    metadata_rules = (
        "每个 chunk 应保留 source、filename、suffix、char_start、char_end 和 "
        "chunk_chars，方便过滤、引用和调试。"
    )
    support_hours = "课程助教在工作日提供答疑支持，周末只处理紧急问题。"
    embedding_notes = "Embedding 会把文本映射成向量，检索时通过相似度找到相关 chunk。"

    return [
        SourceChunk(
            chunk_id="refund_policy:0",
            document_id="refund_policy",
            content=refund_policy,
            metadata=demo_chunk_metadata("data/refund_policy.md", refund_policy),
        ),
        SourceChunk(
            chunk_id="refund_summary:0",
            document_id="refund_summary",
            content=refund_summary,
            metadata=demo_chunk_metadata("data/refund_summary.md", refund_summary),
        ),
        SourceChunk(
            chunk_id="refund_duplicate:0",
            document_id="refund_duplicate",
            content=refund_duplicate,
            metadata=demo_chunk_metadata("data/refund_duplicate.md", refund_duplicate),
        ),
        SourceChunk(
            chunk_id="refund_process:0",
            document_id="refund_process",
            content=refund_process,
            metadata=demo_chunk_metadata("data/refund_process.md", refund_process),
        ),
        SourceChunk(
            chunk_id="trial:0",
            document_id="trial",
            content=trial_policy,
            metadata=demo_chunk_metadata("data/trial_policy.md", trial_policy),
        ),
        SourceChunk(
            chunk_id="metadata:0",
            document_id="metadata",
            content=metadata_rules,
            metadata=demo_chunk_metadata("data/metadata_rules.md", metadata_rules),
        ),
        SourceChunk(
            chunk_id="support:0",
            document_id="support",
            content=support_hours,
            metadata=demo_chunk_metadata("data/support_hours.md", support_hours),
        ),
        SourceChunk(
            chunk_id="embedding:0",
            document_id="embedding",
            content=embedding_notes,
            metadata=demo_chunk_metadata("data/embedding_notes.md", embedding_notes),
        ),
    ]


def demo_embedded_chunks(
    provider: EmbeddingProvider | None = None,
) -> list[EmbeddedChunk]:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    return embed_chunks(demo_source_chunks(), embedding_provider)


def index_demo_chunks(
    store: PersistentVectorStore,
    provider: EmbeddingProvider,
    reset_store: bool = False,
) -> int:
    expected_space = embedding_space_from_provider(provider)
    expected_doc_ids = {chunk.document_id for chunk in demo_source_chunks()}
    should_reset = reset_store

    if not should_reset:
        try:
            current_space = store.embedding_space()
            current_doc_ids = set(store.list_document_ids())
        except ValueError:
            should_reset = True
        else:
            if current_space is not None and current_space != expected_space:
                should_reset = True
            if current_doc_ids and current_doc_ids != expected_doc_ids:
                should_reset = True

    if should_reset:
        store.reset()

    return store.replace_document(demo_embedded_chunks(provider))


def build_demo_store(
    provider: EmbeddingProvider | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
    reset_store: bool = False,
) -> PersistentVectorStore:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig(store_path=store_path))
    index_demo_chunks(store, embedding_provider, reset_store=reset_store)
    return store


class SimpleRetriever:
    def __init__(
        self,
        store: PersistentVectorStore,
        provider: EmbeddingProvider,
    ) -> None:
        self.store = store
        self.provider = provider

    def retrieve(
        self,
        question: str,
        strategy: RetrievalStrategyConfig,
    ) -> list[RetrievalResult]:
        query_vector = self.provider.embed_query(question)
        candidates = self._search_candidates(
            query_vector=query_vector,
            top_k=strategy.candidate_k,
            filename_filter=strategy.filename_filter,
        )

        if strategy.strategy_name == "similarity":
            selected = candidates[: strategy.top_k]
        elif strategy.strategy_name == "threshold":
            selected = [
                item for item in candidates if item.similarity_score >= strategy.score_threshold
            ][: strategy.top_k]
        elif strategy.strategy_name == "mmr":
            selected = maximal_marginal_relevance(
                query_vector=query_vector,
                candidates=candidates,
                top_k=strategy.top_k,
                lambda_mult=strategy.mmr_lambda,
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy.strategy_name}")

        return [
            RetrievalResult(chunk=item.embedded_chunk.chunk, score=item.similarity_score)
            for item in selected
        ]

    def _search_candidates(
        self,
        query_vector: list[float],
        top_k: int,
        filename_filter: str | None = None,
    ) -> list[SearchHit]:
        ensure_vector_dimensions(query_vector, self.provider.dimensions, context="query vector")
        embedded_chunks = self.store.load_chunks()
        for chunk in embedded_chunks:
            ensure_same_embedding_space(chunk, self.provider)

        if filename_filter is not None:
            embedded_chunks = [
                chunk
                for chunk in embedded_chunks
                if chunk.chunk.metadata.get("filename") == filename_filter
            ]

        hits = [
            SearchHit(
                embedded_chunk=chunk,
                similarity_score=cosine_similarity(query_vector, chunk.vector),
            )
            for chunk in embedded_chunks
        ]
        hits.sort(key=lambda item: item.similarity_score, reverse=True)
        return hits[:top_k]


def maximal_marginal_relevance(
    query_vector: list[float],
    candidates: list[SearchHit],
    top_k: int,
    lambda_mult: float,
) -> list[SearchHit]:
    if not candidates:
        return []

    remaining = candidates[:]
    selected: list[SearchHit] = []

    while remaining and len(selected) < top_k:
        if not selected:
            selected.append(remaining.pop(0))
            continue

        best_index = 0
        best_score = float("-inf")
        for index, candidate in enumerate(remaining):
            redundancy = max(
                cosine_similarity(candidate.embedded_chunk.vector, chosen.embedded_chunk.vector)
                for chosen in selected
            )
            mmr_score = (
                lambda_mult * candidate.similarity_score
                - (1.0 - lambda_mult) * redundancy
            )
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        selected.append(remaining.pop(best_index))

    return selected


def average_redundancy(
    results: list[RetrievalResult],
    provider: EmbeddingProvider,
) -> float:
    if len(results) < 2:
        return 0.0

    embedded = provider.embed_documents([result.chunk.content for result in results])
    pair_scores: list[float] = []
    for index, left in enumerate(embedded):
        for right in embedded[index + 1 :]:
            pair_scores.append(cosine_similarity(left, right))
    return sum(pair_scores) / len(pair_scores)


def load_bad_cases(path: Path = DEFAULT_BAD_CASES_PATH) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Bad cases payload must be a list.")
    return [dict(case) for case in payload]


def evaluate_bad_case(
    case: dict[str, object],
    strategy_name: str,
    results: list[RetrievalResult],
    provider: EmbeddingProvider,
) -> BadCaseEvaluation:
    expectations = case.get("expectations")
    if not isinstance(expectations, dict):
        return BadCaseEvaluation(
            strategy_name=strategy_name,
            status="info",
            messages=("no machine-checkable expectations",),
        )

    strategy_expectation = expectations.get(strategy_name)
    if not isinstance(strategy_expectation, dict):
        return BadCaseEvaluation(
            strategy_name=strategy_name,
            status="info",
            messages=("no machine-checkable expectations for this strategy",),
        )

    observed_messages = [
        f"top={results[0].chunk.chunk_id if results else 'none'}",
        f"count={len(results)}",
        f"redundancy={average_redundancy(results, provider):.3f}",
    ]
    failures: list[str] = []

    expected_top_chunk = strategy_expectation.get("top_chunk_id")
    if expected_top_chunk is not None:
        top_chunk = results[0].chunk.chunk_id if results else "none"
        if top_chunk != expected_top_chunk:
            failures.append(
                f"expected top_chunk_id={expected_top_chunk}, got {top_chunk}"
            )

    expected_count = strategy_expectation.get("count")
    if expected_count is not None:
        if not isinstance(expected_count, int) or isinstance(expected_count, bool):
            raise ValueError("Bad case expectation count must be an integer.")
        if len(results) != expected_count:
            failures.append(f"expected count={expected_count}, got {len(results)}")

    expected_empty = strategy_expectation.get("empty")
    if expected_empty is not None:
        if not isinstance(expected_empty, bool):
            raise ValueError("Bad case expectation empty must be a boolean.")
        if expected_empty and results:
            failures.append("expected no results, but retriever returned hits")
        if not expected_empty and not results:
            failures.append("expected non-empty results, but retriever returned none")

    expected_filename = strategy_expectation.get("filename")
    if expected_filename is not None:
        filenames = {result.chunk.metadata.get("filename") for result in results}
        if filenames != {expected_filename}:
            failures.append(
                f"expected all filenames={expected_filename}, got {sorted(filenames)}"
            )

    required_chunk_ids = strategy_expectation.get("must_include_chunk_ids")
    if required_chunk_ids is not None:
        if not isinstance(required_chunk_ids, list):
            raise ValueError("Bad case expectation must_include_chunk_ids must be a list.")
        actual_chunk_ids = {result.chunk.chunk_id for result in results}
        missing = [
            str(chunk_id)
            for chunk_id in required_chunk_ids
            if str(chunk_id) not in actual_chunk_ids
        ]
        if missing:
            failures.append(f"missing required chunk ids: {missing}")

    max_redundancy = strategy_expectation.get("max_redundancy")
    if max_redundancy is not None:
        if not isinstance(max_redundancy, (int, float)) or isinstance(max_redundancy, bool):
            raise ValueError("Bad case expectation max_redundancy must be numeric.")
        redundancy = average_redundancy(results, provider)
        if redundancy > float(max_redundancy):
            failures.append(
                f"expected redundancy <= {float(max_redundancy):.3f}, got {redundancy:.3f}"
            )

    if failures:
        return BadCaseEvaluation(
            strategy_name=strategy_name,
            status="fail",
            messages=tuple(observed_messages + failures),
        )

    return BadCaseEvaluation(
        strategy_name=strategy_name,
        status="pass",
        messages=tuple(observed_messages),
    )
