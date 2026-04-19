from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
import hashlib
import json
import re
from typing import Protocol


TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "how", "why", "do"}
CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "refund")),
    ("trial", ("试学", "预约", "trial")),
    ("policy", ("规则", "政策", "条件")),
    ("process", ("流程", "申请", "提交", "审核")),
    ("metadata", ("metadata", "source", "filename", "来源")),
    ("stable_id", ("stable", "id", "document_id", "chunk_id", "稳定")),
    ("embedding", ("embedding", "向量", "vector")),
    ("similarity", ("similarity", "相似度", "检索", "retrieve")),
    ("support", ("答疑", "support", "工作日")),
]
HASH_BUCKETS = 4
MODE_BUCKETS = 1
DEFAULT_DIMENSIONS = len(CONCEPT_GROUPS) + HASH_BUCKETS + MODE_BUCKETS
DEFAULT_BAD_CASES_PATH = Path(__file__).resolve().parent / "evals" / "retrieval_bad_cases.json"


@dataclass(frozen=True)
class SourceChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: SourceChunk
    vector: list[float]
    provider_name: str
    model_name: str
    dimensions: int


@dataclass(frozen=True)
class RetrievalResult:
    chunk: SourceChunk
    score: float


@dataclass(frozen=True)
class RetrievalStrategyConfig:
    strategy_name: str
    top_k: int = 3
    candidate_k: int = 5
    score_threshold: float = 0.60
    mmr_lambda: float = 0.65
    filename_filter: str | None = None

    def __post_init__(self) -> None:
        if self.strategy_name not in {"similarity", "threshold", "mmr"}:
            raise ValueError(f"Unsupported strategy: {self.strategy_name}")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k")
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.mmr_lambda <= 1.0:
            raise ValueError("mmr_lambda must be between 0.0 and 1.0")


@dataclass(frozen=True)
class SearchHit:
    embedded_chunk: EmbeddedChunk
    score: float


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimensions: int

    def embed_query(self, text: str) -> list[float]:
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalKeywordEmbeddingProvider:
    def __init__(
        self,
        model_name: str = "concept-space-v1",
        dimensions: int = DEFAULT_DIMENSIONS,
    ) -> None:
        if dimensions != DEFAULT_DIMENSIONS:
            raise ValueError(
                f"LocalKeywordEmbeddingProvider expects dimensions={DEFAULT_DIMENSIONS}."
            )

        self.provider_name = "local_keyword"
        self.model_name = model_name
        self.dimensions = dimensions

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, kind="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text, kind="document") for text in texts]

    def _embed(self, text: str, kind: str) -> list[float]:
        normalized = " ".join(text.lower().split())
        vector = [0.0] * self.dimensions

        for index, (_, keywords) in enumerate(CONCEPT_GROUPS):
            hits = sum(1 for keyword in keywords if keyword in normalized)
            vector[index] = float(hits)

        hash_offset = len(CONCEPT_GROUPS)
        for token in TOKEN_PATTERN.findall(normalized):
            if token in STOPWORDS:
                continue
            bucket = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % HASH_BUCKETS
            vector[hash_offset + bucket] += 0.10

        mode_index = self.dimensions - 1
        vector[mode_index] = 0.15 if kind == "query" else 0.05

        return normalize(vector)


def demo_source_chunks() -> list[SourceChunk]:
    return [
        SourceChunk(
            chunk_id="refund_policy:0",
            document_id="refund_policy",
            content="退款规则：购买后 7 天内且学习进度不超过 20%，可以申请全额退款。",
            metadata={
                "source": "data/refund_policy.md",
                "filename": "refund_policy.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="refund_summary:0",
            document_id="refund_summary",
            content="退款政策摘要：7 天内且学习进度不超过 20%，支持全额退费。",
            metadata={
                "source": "data/refund_summary.md",
                "filename": "refund_summary.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="refund_duplicate:0",
            document_id="refund_duplicate",
            content="退款说明：购买后 7 天内且学习进度不超过 20%，支持全额退款。",
            metadata={
                "source": "data/refund_duplicate.md",
                "filename": "refund_duplicate.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="refund_process:0",
            document_id="refund_process",
            content="退费申请流程：在学习后台提交退款申请，审核通过后原路退回。",
            metadata={
                "source": "data/refund_process.md",
                "filename": "refund_process.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="metadata_rules:0",
            document_id="metadata_rules",
            content="每个 chunk 应保留 source、filename 和 chunk_index，方便后续引用和调试。",
            metadata={
                "source": "data/metadata_rules.md",
                "filename": "metadata_rules.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="metadata_filter:0",
            document_id="metadata_filter",
            content="metadata filter 可以限制检索范围，只查指定 filename 或 source。",
            metadata={
                "source": "data/metadata_filter.md",
                "filename": "metadata_filter.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="support:0",
            document_id="support",
            content="课程助教在工作日提供答疑支持，周末只处理紧急问题。",
            metadata={
                "source": "data/support_hours.md",
                "filename": "support_hours.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="embedding:0",
            document_id="embedding",
            content="Embedding 会把文本映射成向量，检索时通过相似度找到相关 chunk。",
            metadata={
                "source": "data/embedding_notes.md",
                "filename": "embedding_notes.md",
                "chunk_index": 0,
            },
        ),
    ]


def demo_embedded_chunks(
    provider: EmbeddingProvider | None = None,
) -> list[EmbeddedChunk]:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    chunks = demo_source_chunks()
    vectors = embedding_provider.embed_documents([chunk.content for chunk in chunks])
    return [
        EmbeddedChunk(
            chunk=chunk,
            vector=vector,
            provider_name=embedding_provider.provider_name,
            model_name=embedding_provider.model_name,
            dimensions=len(vector),
        )
        for chunk, vector in zip(chunks, vectors)
    ]


class InMemoryVectorStore:
    def __init__(self, chunks: list[EmbeddedChunk]) -> None:
        self._chunks = chunks

    def similarity_search(
        self,
        query_vector: list[float],
        top_k: int,
        filename_filter: str | None = None,
    ) -> list[SearchHit]:
        candidates = self._chunks
        if filename_filter is not None:
            candidates = [
                chunk
                for chunk in candidates
                if chunk.chunk.metadata.get("filename") == filename_filter
            ]

        hits = [
            SearchHit(
                embedded_chunk=chunk,
                score=cosine_similarity(query_vector, chunk.vector),
            )
            for chunk in candidates
        ]
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]


class SimpleRetriever:
    def __init__(
        self,
        store: InMemoryVectorStore,
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
        candidates = self.store.similarity_search(
            query_vector=query_vector,
            top_k=strategy.candidate_k,
            filename_filter=strategy.filename_filter,
        )

        if strategy.strategy_name == "similarity":
            selected = candidates[: strategy.top_k]
        elif strategy.strategy_name == "threshold":
            selected = [
                item for item in candidates if item.score >= strategy.score_threshold
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
            RetrievalResult(chunk=item.embedded_chunk.chunk, score=item.score)
            for item in selected
        ]


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
            query_score = cosine_similarity(query_vector, candidate.embedded_chunk.vector)
            redundancy = max(
                cosine_similarity(candidate.embedded_chunk.vector, chosen.embedded_chunk.vector)
                for chosen in selected
            )
            mmr_score = lambda_mult * query_score - (1 - lambda_mult) * redundancy
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        selected.append(remaining.pop(best_index))

    return selected


def average_redundancy(results: list[RetrievalResult], provider: EmbeddingProvider) -> float:
    if len(results) < 2:
        return 0.0

    embedded = provider.embed_documents([result.chunk.content for result in results])
    pair_scores: list[float] = []
    for index, left in enumerate(embedded):
        for right in embedded[index + 1 :]:
            pair_scores.append(cosine_similarity(left, right))
    return sum(pair_scores) / len(pair_scores)


def load_bad_cases(path: Path = DEFAULT_BAD_CASES_PATH) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Cosine similarity requires vectors with the same dimensions.")

    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
