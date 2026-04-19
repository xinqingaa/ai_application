from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
import hashlib
import re
from typing import Protocol


TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]", re.IGNORECASE)
STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "how", "why", "do"}
CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "refund")),
    ("trial", ("试学", "预约", "trial")),
    ("metadata", ("metadata", "source", "filename", "来源")),
    ("stable_id", ("stable", "id", "document_id", "chunk_id", "稳定")),
    ("embedding", ("embedding", "向量", "vector")),
    ("similarity", ("similarity", "相似度", "检索", "retrieve")),
    ("support", ("答疑", "support", "工作日")),
]
HASH_BUCKETS = 4
MODE_BUCKETS = 2
DEFAULT_DIMENSIONS = len(CONCEPT_GROUPS) + HASH_BUCKETS + MODE_BUCKETS


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
            vector[hash_offset + bucket] += 0.25

        query_mode_index = self.dimensions - 2
        document_mode_index = self.dimensions - 1
        if kind == "query":
            vector[query_mode_index] = 0.30
        else:
            vector[document_mode_index] = 0.30

        return normalize(vector)


def demo_chunk_metadata(source: str, content: str, chunk_index: int = 0) -> dict[str, str | int]:
    filename = source.rsplit("/", maxsplit=1)[-1]
    suffix = f".{filename.rsplit('.', maxsplit=1)[-1]}" if "." in filename else ""
    char_count = len(content)
    line_count = 0 if not content else content.count("\n") + 1
    return {
        "source": source,
        "filename": filename,
        "suffix": suffix,
        "char_count": char_count,
        "line_count": line_count,
        "chunk_index": chunk_index,
        "char_start": 0,
        "char_end": char_count,
        "chunk_chars": char_count,
    }


def demo_source_chunks() -> list[SourceChunk]:
    return [
        SourceChunk(
            chunk_id="refund:0",
            document_id="refund",
            content="购买后 7 天内且学习进度不超过 20%，可以申请全额退款。",
            metadata=demo_chunk_metadata(
                source="data/refund_policy.md",
                content="购买后 7 天内且学习进度不超过 20%，可以申请全额退款。",
            ),
        ),
        SourceChunk(
            chunk_id="trial:0",
            document_id="trial",
            content="课程支持一次 30 分钟免费试学，需要提前预约。",
            metadata=demo_chunk_metadata(
                source="data/trial_policy.md",
                content="课程支持一次 30 分钟免费试学，需要提前预约。",
            ),
        ),
        SourceChunk(
            chunk_id="metadata:0",
            document_id="metadata",
            content="每个 chunk 应保留 source、filename 和 chunk_index，方便后续引用和调试。",
            metadata=demo_chunk_metadata(
                source="data/metadata_rules.md",
                content="每个 chunk 应保留 source、filename 和 chunk_index，方便后续引用和调试。",
            ),
        ),
        SourceChunk(
            chunk_id="embedding:0",
            document_id="embedding",
            content="Embedding 会把文本映射成向量，后续系统可以计算相似度并做检索。",
            metadata=demo_chunk_metadata(
                source="data/embedding_notes.md",
                content="Embedding 会把文本映射成向量，后续系统可以计算相似度并做检索。",
            ),
        ),
        SourceChunk(
            chunk_id="support:0",
            document_id="support",
            content="课程助教在工作日提供答疑支持，周末只处理紧急问题。",
            metadata=demo_chunk_metadata(
                source="data/support_hours.md",
                content="课程助教在工作日提供答疑支持，周末只处理紧急问题。",
            ),
        ),
    ]


def ensure_vector_dimensions(
    vector: list[float],
    expected_dimensions: int,
    context: str,
) -> None:
    if len(vector) != expected_dimensions:
        raise ValueError(
            f"{context} has dimensions={len(vector)}, expected {expected_dimensions}."
        )


def ensure_same_embedding_space(
    chunk: EmbeddedChunk,
    provider: EmbeddingProvider,
) -> None:
    if chunk.provider_name != provider.provider_name or chunk.model_name != provider.model_name:
        raise ValueError("Query and document vectors must come from the same provider/model.")

    if chunk.dimensions != provider.dimensions:
        raise ValueError("Embedded chunk dimensions do not match provider dimensions.")

    ensure_vector_dimensions(
        chunk.vector,
        chunk.dimensions,
        context=f"embedded chunk {chunk.chunk.chunk_id}",
    )


def embed_chunks(
    chunks: list[SourceChunk],
    provider: EmbeddingProvider,
) -> list[EmbeddedChunk]:
    if not chunks:
        return []

    vectors = provider.embed_documents([chunk.content for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected vector count.")

    embedded_chunks: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors):
        ensure_vector_dimensions(
            vector,
            provider.dimensions,
            context=f"document vector for {chunk.chunk_id}",
        )
        embedded_chunks.append(
            EmbeddedChunk(
                chunk=chunk,
                vector=vector,
                provider_name=provider.provider_name,
                model_name=provider.model_name,
                dimensions=provider.dimensions,
            )
        )
    return embedded_chunks


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Cosine similarity requires vectors with the same dimensions.")

    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def score_query_against_chunks(
    question: str,
    chunks: list[EmbeddedChunk],
    provider: EmbeddingProvider,
) -> list[tuple[EmbeddedChunk, float]]:
    if not chunks:
        return []

    query_vector = provider.embed_query(question)
    ensure_vector_dimensions(query_vector, provider.dimensions, context="query vector")
    scored: list[tuple[EmbeddedChunk, float]] = []
    for chunk in chunks:
        ensure_same_embedding_space(chunk, provider)
        scored.append((chunk, cosine_similarity(query_vector, chunk.vector)))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
