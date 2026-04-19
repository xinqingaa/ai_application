from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
import hashlib
import json
import re
from typing import Protocol


CHAPTER_ROOT = Path(__file__).resolve().parent
DEFAULT_STORE_PATH = CHAPTER_ROOT / "store" / "demo_vector_store.json"
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
MODE_BUCKETS = 1
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


@dataclass(frozen=True)
class RetrievalResult:
    chunk: SourceChunk
    score: float


@dataclass(frozen=True)
class VectorStoreConfig:
    store_path: Path = DEFAULT_STORE_PATH


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

        mode_index = self.dimensions - 1
        vector[mode_index] = 0.15 if kind == "query" else 0.05

        return normalize(vector)


def demo_source_chunks() -> list[SourceChunk]:
    return [
        SourceChunk(
            chunk_id="refund:0",
            document_id="refund",
            content="购买后 7 天内且学习进度不超过 20%，可以申请全额退款。",
            metadata={
                "source": "data/refund_policy.md",
                "filename": "refund_policy.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="trial:0",
            document_id="trial",
            content="课程支持一次 30 分钟免费试学，需要提前预约。",
            metadata={
                "source": "data/trial_policy.md",
                "filename": "trial_policy.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="metadata:0",
            document_id="metadata",
            content="每个 chunk 应保留 source、filename 和 chunk_index，方便后续引用和调试。",
            metadata={
                "source": "data/metadata_rules.md",
                "filename": "metadata_rules.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="embedding:0",
            document_id="embedding",
            content="Embedding 会把文本映射成向量，后续系统可以计算相似度并做检索。",
            metadata={
                "source": "data/embedding_notes.md",
                "filename": "embedding_notes.md",
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


class PersistentVectorStore:
    def __init__(self, config: VectorStoreConfig) -> None:
        self.config = config
        self.config.store_path.parent.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        if self.config.store_path.exists():
            self.config.store_path.unlink()

    def upsert(self, chunks: list[EmbeddedChunk]) -> int:
        records = self._load_records()
        for chunk in chunks:
            records[chunk.chunk.chunk_id] = self._serialize_embedded_chunk(chunk)
        self._save_records(records)
        return len(chunks)

    def count(self) -> int:
        return len(self._load_records())

    def list_document_ids(self) -> list[str]:
        records = self._load_records().values()
        return sorted({record["chunk"]["document_id"] for record in records})

    def similarity_search(
        self,
        query_vector: list[float],
        top_k: int = 3,
        filename: str | None = None,
    ) -> list[RetrievalResult]:
        embedded_chunks = self.load_chunks()
        if filename is not None:
            embedded_chunks = [
                chunk
                for chunk in embedded_chunks
                if chunk.chunk.metadata.get("filename") == filename
            ]

        scored = [
            RetrievalResult(
                chunk=chunk.chunk,
                score=cosine_similarity(query_vector, chunk.vector),
            )
            for chunk in embedded_chunks
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def delete_by_document_id(self, document_id: str) -> int:
        records = self._load_records()
        removable = [
            chunk_id
            for chunk_id, record in records.items()
            if record["chunk"]["document_id"] == document_id
        ]
        for chunk_id in removable:
            del records[chunk_id]
        self._save_records(records)
        return len(removable)

    def load_chunks(self) -> list[EmbeddedChunk]:
        return [
            self._deserialize_embedded_chunk(record)
            for _, record in sorted(self._load_records().items())
        ]

    def _load_records(self) -> dict[str, dict[str, object]]:
        if not self.config.store_path.exists():
            return {}
        payload = json.loads(self.config.store_path.read_text(encoding="utf-8"))
        return {record["chunk"]["chunk_id"]: record for record in payload["records"]}

    def _save_records(self, records: dict[str, dict[str, object]]) -> None:
        payload = {
            "records": [records[key] for key in sorted(records)],
        }
        self.config.store_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _serialize_embedded_chunk(self, chunk: EmbeddedChunk) -> dict[str, object]:
        return {
            "chunk": {
                "chunk_id": chunk.chunk.chunk_id,
                "document_id": chunk.chunk.document_id,
                "content": chunk.chunk.content,
                "metadata": dict(chunk.chunk.metadata),
            },
            "vector": chunk.vector,
            "provider_name": chunk.provider_name,
            "model_name": chunk.model_name,
            "dimensions": chunk.dimensions,
        }

    def _deserialize_embedded_chunk(self, record: dict[str, object]) -> EmbeddedChunk:
        chunk_payload = record["chunk"]
        if not isinstance(chunk_payload, dict):
            raise ValueError("Invalid chunk payload in vector store.")

        chunk = SourceChunk(
            chunk_id=str(chunk_payload["chunk_id"]),
            document_id=str(chunk_payload["document_id"]),
            content=str(chunk_payload["content"]),
            metadata=dict(chunk_payload["metadata"]),
        )
        return EmbeddedChunk(
            chunk=chunk,
            vector=list(record["vector"]),
            provider_name=str(record["provider_name"]),
            model_name=str(record["model_name"]),
            dimensions=int(record["dimensions"]),
        )


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
