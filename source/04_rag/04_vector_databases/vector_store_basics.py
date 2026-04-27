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


@dataclass(frozen=True)
class RetrievalResult:
    chunk: SourceChunk
    score: float


@dataclass(frozen=True)
class VectorStoreConfig:
    store_path: Path = DEFAULT_STORE_PATH


@dataclass(frozen=True)
class EmbeddingSpace:
    # The store treats provider/model/dimensions as one inseparable identity.
    # Once a store has written one space, later writes and queries must stay in it.
    provider_name: str
    model_name: str
    dimensions: int

    def label(self) -> str:
        return f"{self.provider_name}/{self.model_name}/{self.dimensions}d"


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
            content=(
                "每个 chunk 应保留 source、filename、suffix、char_start、char_end 和 "
                "chunk_chars，方便过滤、引用和调试。"
            ),
            metadata=demo_chunk_metadata(
                source="data/metadata_rules.md",
                content=(
                    "每个 chunk 应保留 source、filename、suffix、char_start、char_end 和 "
                    "chunk_chars，方便过滤、引用和调试。"
                ),
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


def embedding_space_from_provider(provider: EmbeddingProvider) -> EmbeddingSpace:
    return EmbeddingSpace(
        provider_name=provider.provider_name,
        model_name=provider.model_name,
        dimensions=provider.dimensions,
    )


def embedding_space_from_chunk(chunk: EmbeddedChunk) -> EmbeddingSpace:
    return EmbeddingSpace(
        provider_name=chunk.provider_name,
        model_name=chunk.model_name,
        dimensions=chunk.dimensions,
    )


def ensure_matching_embedding_space(
    actual: EmbeddingSpace,
    expected: EmbeddingSpace,
    context: str,
) -> None:
    if actual != expected:
        raise ValueError(
            f"{context} uses embedding space {actual.label()}, expected {expected.label()}."
        )


def ensure_same_embedding_space(
    chunk: EmbeddedChunk,
    provider: EmbeddingProvider,
) -> None:
    ensure_matching_embedding_space(
        actual=embedding_space_from_chunk(chunk),
        expected=embedding_space_from_provider(provider),
        context=f"embedded chunk {chunk.chunk.chunk_id}",
    )
    ensure_vector_dimensions(
        chunk.vector,
        chunk.dimensions,
        context=f"embedded chunk {chunk.chunk.chunk_id}",
    )


def infer_chunks_embedding_space(chunks: list[EmbeddedChunk]) -> EmbeddingSpace | None:
    if not chunks:
        return None

    expected_space = embedding_space_from_chunk(chunks[0])
    for chunk in chunks:
        ensure_vector_dimensions(
            chunk.vector,
            chunk.dimensions,
            context=f"embedded chunk {chunk.chunk.chunk_id}",
        )
        ensure_matching_embedding_space(
            actual=embedding_space_from_chunk(chunk),
            expected=expected_space,
            context=f"embedded chunk {chunk.chunk.chunk_id}",
        )
    return expected_space


def embed_chunks(
    chunks: list[SourceChunk],
    provider: EmbeddingProvider,
) -> list[EmbeddedChunk]:
    if not chunks:
        return []

    # The provider may be remote or wrapped by another library, so we check both
    # vector count and dimensions here before anything enters the storage layer.
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


def demo_embedded_chunks(
    provider: EmbeddingProvider | None = None,
) -> list[EmbeddedChunk]:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    return embed_chunks(demo_source_chunks(), embedding_provider)


class PersistentVectorStore:
    def __init__(self, config: VectorStoreConfig) -> None:
        self.config = config
        self.config.store_path.parent.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        if self.config.store_path.exists():
            self.config.store_path.unlink()

    def upsert(self, chunks: list[EmbeddedChunk]) -> int:
        validated_chunks, incoming_space = self._validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        records = self._load_records()
        stored_space = self._infer_record_embedding_space(records)
        if stored_space is not None and incoming_space is not None:
            # A single store intentionally holds one embedding space only.
            ensure_matching_embedding_space(
                actual=incoming_space,
                expected=stored_space,
                context="incoming chunks",
            )

        for chunk in validated_chunks:
            records[chunk.chunk.chunk_id] = self._serialize_embedded_chunk(chunk)
        self._save_records(records)
        return len(validated_chunks)

    def replace_document(self, chunks: list[EmbeddedChunk]) -> int:
        validated_chunks, incoming_space = self._validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        target_document_ids = {chunk.chunk.document_id for chunk in validated_chunks}
        # replace_document is document-scoped, not chunk-scoped: remove every old
        # chunk that belongs to the same document before inserting the new version.
        remaining_records = {
            chunk_id: record
            for chunk_id, record in self._load_records().items()
            if self._record_document_id(record) not in target_document_ids
        }
        stored_space = self._infer_record_embedding_space(remaining_records)
        if stored_space is not None and incoming_space is not None:
            ensure_matching_embedding_space(
                actual=incoming_space,
                expected=stored_space,
                context="incoming chunks",
            )

        for chunk in validated_chunks:
            remaining_records[chunk.chunk.chunk_id] = self._serialize_embedded_chunk(chunk)
        self._save_records(remaining_records)
        return len(validated_chunks)

    def count(self) -> int:
        return len(self._load_records())

    def list_document_ids(self) -> list[str]:
        return sorted({chunk.chunk.document_id for chunk in self.load_chunks()})

    def embedding_space(self) -> EmbeddingSpace | None:
        return infer_chunks_embedding_space(self.load_chunks())

    def similarity_search(
        self,
        query_vector: list[float],
        provider: EmbeddingProvider,
        top_k: int = 3,
        filename: str | None = None,
    ) -> list[RetrievalResult]:
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        ensure_vector_dimensions(query_vector, provider.dimensions, context="query vector")
        embedded_chunks = self.load_chunks()
        # Query-time validation matters as much as write-time validation. Searching
        # across mixed spaces produces plausible-looking but meaningless scores.
        for chunk in embedded_chunks:
            ensure_same_embedding_space(chunk, provider)

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
            if self._record_document_id(record) == document_id
        ]
        for chunk_id in removable:
            del records[chunk_id]
        self._save_records(records)
        return len(removable)

    def load_chunks(self) -> list[EmbeddedChunk]:
        chunks = [
            self._deserialize_embedded_chunk(record)
            for _, record in sorted(self._load_records().items())
        ]
        infer_chunks_embedding_space(chunks)
        return chunks

    def _load_records(self) -> dict[str, dict[str, object]]:
        if not self.config.store_path.exists():
            return {}

        payload = json.loads(self.config.store_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Vector store payload must be a JSON object.")

        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("Vector store payload must contain a records list.")

        records: dict[str, dict[str, object]] = {}
        for index, record in enumerate(raw_records):
            record_payload = self._require_mapping(record, context=f"records[{index}]")
            chunk_id = self._record_chunk_id(record_payload)
            if chunk_id in records:
                raise ValueError(f"Duplicate chunk_id={chunk_id} found in vector store.")
            records[chunk_id] = record_payload
        return records

    def _save_records(self, records: dict[str, dict[str, object]]) -> None:
        payload: dict[str, object] = {
            "records": [records[key] for key in sorted(records)],
        }

        store_space = self._infer_record_embedding_space(records)
        if store_space is not None:
            # Persist the store-level space explicitly so the file itself reveals
            # which provider/model/dimensions the records belong to.
            payload["embedding_space"] = {
                "provider_name": store_space.provider_name,
                "model_name": store_space.model_name,
                "dimensions": store_space.dimensions,
            }

        self.config.store_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _validate_write_batch(
        self,
        chunks: list[EmbeddedChunk],
    ) -> tuple[list[EmbeddedChunk], EmbeddingSpace | None]:
        seen_chunk_ids: set[str] = set()
        for chunk in chunks:
            self._validate_embedded_chunk(chunk)
            if chunk.chunk.chunk_id in seen_chunk_ids:
                raise ValueError(
                    f"Write batch contains duplicate chunk_id={chunk.chunk.chunk_id}."
                )
            seen_chunk_ids.add(chunk.chunk.chunk_id)
        return chunks, infer_chunks_embedding_space(chunks)

    def _validate_embedded_chunk(self, chunk: EmbeddedChunk) -> None:
        if not chunk.chunk.chunk_id:
            raise ValueError("Embedded chunk must have a non-empty chunk_id.")
        if not chunk.chunk.document_id:
            raise ValueError(
                f"Embedded chunk {chunk.chunk.chunk_id} must have a non-empty document_id."
            )
        if not chunk.provider_name:
            raise ValueError(
                f"Embedded chunk {chunk.chunk.chunk_id} must have a provider_name."
            )
        if not chunk.model_name:
            raise ValueError(f"Embedded chunk {chunk.chunk.chunk_id} must have a model_name.")
        if chunk.dimensions <= 0:
            raise ValueError(
                f"Embedded chunk {chunk.chunk.chunk_id} must have positive dimensions."
            )
        ensure_vector_dimensions(
            chunk.vector,
            chunk.dimensions,
            context=f"embedded chunk {chunk.chunk.chunk_id}",
        )

    def _serialize_embedded_chunk(self, chunk: EmbeddedChunk) -> dict[str, object]:
        self._validate_embedded_chunk(chunk)
        # We store both vector data and the original chunk identity so later
        # retrieval can return standard chunks instead of detached scores.
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
        chunk_payload = self._require_mapping(record.get("chunk"), context="record.chunk")
        metadata_payload = self._require_mapping(
            chunk_payload.get("metadata"),
            context="record.chunk.metadata",
        )

        vector_payload = record.get("vector")
        if not isinstance(vector_payload, list):
            raise ValueError("record.vector must be a list of numbers.")
        vector: list[float] = []
        for index, value in enumerate(vector_payload):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"record.vector[{index}] must be a number.")
            vector.append(float(value))

        chunk = SourceChunk(
            chunk_id=self._require_string(chunk_payload, "chunk_id", context="record.chunk"),
            document_id=self._require_string(
                chunk_payload,
                "document_id",
                context="record.chunk",
            ),
            content=self._require_string(chunk_payload, "content", context="record.chunk"),
            metadata=dict(metadata_payload),
        )
        embedded_chunk = EmbeddedChunk(
            chunk=chunk,
            vector=vector,
            provider_name=self._require_string(
                record,
                "provider_name",
                context="record",
            ),
            model_name=self._require_string(record, "model_name", context="record"),
            dimensions=self._require_int(record, "dimensions", context="record"),
        )
        self._validate_embedded_chunk(embedded_chunk)
        return embedded_chunk

    def _infer_record_embedding_space(
        self,
        records: dict[str, dict[str, object]],
    ) -> EmbeddingSpace | None:
        if not records:
            return None
        return infer_chunks_embedding_space(
            [self._deserialize_embedded_chunk(record) for record in records.values()]
        )

    def _record_chunk_id(self, record: dict[str, object]) -> str:
        chunk_payload = self._require_mapping(record.get("chunk"), context="record.chunk")
        return self._require_string(chunk_payload, "chunk_id", context="record.chunk")

    def _record_document_id(self, record: dict[str, object]) -> str:
        chunk_payload = self._require_mapping(record.get("chunk"), context="record.chunk")
        return self._require_string(chunk_payload, "document_id", context="record.chunk")

    def _require_mapping(self, value: object, context: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ValueError(f"{context} must be a JSON object.")
        return value

    def _require_string(self, payload: dict[str, object], key: str, context: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{context}.{key} must be a non-empty string.")
        return value

    def _require_int(self, payload: dict[str, object], key: str, context: str) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{context}.{key} must be an integer.")
        return value


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
