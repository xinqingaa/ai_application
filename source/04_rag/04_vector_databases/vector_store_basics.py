"""第四章向量存储行为的教学基础模块。

这个模块刻意保留一个最小 JSON store，用来先看清存储层契约；
同一套思路后面再映射到 Chroma 和 LangChain。
主链路是：

SourceChunk[] -> embed_chunks() -> EmbeddedChunk[] -> PersistentVectorStore
-> similarity_search() -> RetrievalResult[].
"""

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
    """从文档处理阶段传下来的文本单元。

    chunk_id 标识当前这个具体 chunk；document_id 标识来源文档，
    一份文档可以包含一个或多个 chunk。
    """

    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddedChunk:
    """带向量和 embedding space 身份的 SourceChunk。"""

    chunk: SourceChunk
    vector: list[float]
    provider_name: str
    model_name: str
    dimensions: int


@dataclass(frozen=True)
class RetrievalResult:
    """第四章所有 backend 统一返回的标准结果形状。"""

    chunk: SourceChunk
    score: float


@dataclass(frozen=True)
class VectorStoreConfig:
    """教学版 JSON 向量库的配置。"""

    store_path: Path = DEFAULT_STORE_PATH


@dataclass(frozen=True)
class EmbeddingSpace:
    # store 会把 provider/model/dimensions 当成不可拆分的空间身份。
    # 一旦某个 store 写入了一个空间，后续写入和查询都必须保持一致。
    provider_name: str
    model_name: str
    dimensions: int

    def label(self) -> str:
        return f"provider_name: {self.provider_name};model_name: {self.model_name};dimensions: {self.dimensions}d"


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimensions: int

    def embed_query(self, text: str) -> list[float]:
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalKeywordEmbeddingProvider:
    """本章演示使用的确定性本地 embedding provider。

    它不是真实语义模型，而是为了让向量库示例无需网络也能稳定复现；
    同时它仍然具备 provider/model/dimensions 这类真实 provider 身份。
    """

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
        """把用户 query 映射到和文档相同的向量空间。"""

        return self._embed(text, kind="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """在写入 store 前批量向量化文档文本。"""

        return [self._embed(text, kind="document") for text in texts]

    def _embed(self, text: str, kind: str) -> list[float]:
        """把文本转换成确定性的概念/hash 混合向量。"""

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
    """构造后续过滤、引用和调试需要的最小来源 metadata。"""

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
    """返回 JSON、Chroma、LangChain 演示共用的固定小语料。"""

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
    """当向量维度不属于期望 embedding space 时尽早失败。"""

    if len(vector) != expected_dimensions:
        raise ValueError(
            f"{context} has dimensions={len(vector)}, expected {expected_dimensions}."
        )


def embedding_space_from_provider(provider: EmbeddingProvider) -> EmbeddingSpace:
    """从 embedding provider 读取 provider/model/dimensions。"""

    return EmbeddingSpace(
        provider_name=provider.provider_name,
        model_name=provider.model_name,
        dimensions=provider.dimensions,
    )


def embedding_space_from_chunk(chunk: EmbeddedChunk) -> EmbeddingSpace:
    """从一个 embedded chunk 读取 provider/model/dimensions。"""

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
    """在继续写入或查询前，确认两个向量空间可以比较。"""

    if actual != expected:
        raise ValueError(
            f"{context} uses embedding space {actual.label()}, expected {expected.label()}."
        )


def ensure_same_embedding_space(
    chunk: EmbeddedChunk,
    provider: EmbeddingProvider,
) -> None:
    """确认 embedded chunk 和 query provider 属于同一个空间。"""

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
    """从一批 embedded chunks 中推断共享 embedding space。

    空批次还没有空间身份；非空批次必须内部一致，才能进入 store。
    """

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
    """把 SourceChunk[] 转成存储层需要的 EmbeddedChunk[]。

    参数：
        chunks: 带稳定 id 和 metadata 的 SourceChunk 列表。
        provider: 当前批次统一使用的 embedding provider。

    返回：
        带向量数据和 provider/model/dimensions 身份的 EmbeddedChunk 列表。
    """

    if not chunks:
        return []

    # provider 可能来自远程服务，也可能被框架包装；进入存储层前先同时校验
    # 向量数量和维度，能把问题拦在写入之前。
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
    """使用指定 provider 构造已经向量化的演示语料。"""

    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    return embed_chunks(demo_source_chunks(), embedding_provider)


class PersistentVectorStore:
    """用于讲解存储契约的最小 JSON 向量库。

    这个 store 会把向量记录持久化到磁盘，并暴露后续 backend 都需要的能力：
    upsert、文档级替换、相似度查询、文档级删除。
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        """创建 store，并确保父目录存在。"""

        self.config = config
        self.config.store_path.parent.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        """删除持久化 JSON 文件，让下一次运行从空 store 开始。"""

        if self.config.store_path.exists():
            self.config.store_path.unlink()

    def upsert(self, chunks: list[EmbeddedChunk]) -> int:
        """按 chunk_id 插入或覆盖 chunks。

        参数：
            chunks: 待写入的 EmbeddedChunk 列表，必须属于同一个 embedding space。

        返回：
            实际写入的 chunk 数量。
        """

        validated_chunks, incoming_space = self._validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        records = self._load_records()
        stored_space = self._infer_record_embedding_space(records)
        if stored_space is not None and incoming_space is not None:
            # 单个 store 刻意只保存一个 embedding space，避免跨空间相似度比较。
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
        """按 document_id 整体替换文档，再写入新的 chunks。

        参数：
            chunks: 一个或多个 document_id 对应的新 EmbeddedChunk 列表。

        返回：
            删除旧 chunk 后实际写入的新 chunk 数量。
        """

        validated_chunks, incoming_space = self._validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        target_document_ids = {chunk.chunk.document_id for chunk in validated_chunks}
        # replace_document 是文档级语义，不是 chunk 级语义：先删除同文档旧 chunk，
        # 再插入新版本，避免 stale chunks 残留。
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
        """返回当前持久化的向量记录数量。"""

        return len(self._load_records())

    def list_document_ids(self) -> list[str]:
        """返回当前 store 中出现过的所有 document_id。"""

        return sorted({chunk.chunk.document_id for chunk in self.load_chunks()})

    def embedding_space(self) -> EmbeddingSpace | None:
        """返回 store 的 embedding space；空 store 返回 None。"""

        return infer_chunks_embedding_space(self.load_chunks())

    def similarity_search(
        self,
        query_vector: list[float],
        provider: EmbeddingProvider,
        top_k: int = 3,
        filename: str | None = None,
    ) -> list[RetrievalResult]:
        """查询已存向量，并返回标准 RetrievalResult 对象。

        参数：
            query_vector: 由 provider.embed_query(...) 生成的查询向量。
            provider: 用于校验 query/store 空间一致性的 provider 身份。
            top_k: 最多返回的结果数量。
            filename: 教学 store 中支持的可选 metadata 等值过滤条件。
        """

        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        # 判断向量维度是否符合 embedding space
        ensure_vector_dimensions(query_vector, provider.dimensions, context="query vector")
        embedded_chunks = self.load_chunks()
        # 查询时校验和写入时校验一样重要；跨空间查询会产生看似正常、
        # 但语义上没有意义的相似度分数。
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
                score=cosine_similarity(query_vector, chunk.vector), # 计算余弦值 分数越高 越接近
            )
            for chunk in embedded_chunks
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def delete_by_document_id(self, document_id: str) -> int:
        """删除属于同一个来源文档的全部 chunk。"""

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
        """把持久化记录重新加载成 EmbeddedChunk 对象。"""

        chunks = [
            self._deserialize_embedded_chunk(record)
            for _, record in sorted(self._load_records().items())
        ]
        infer_chunks_embedding_space(chunks)
        return chunks

    def _load_records(self) -> dict[str, dict[str, object]]:
        """读取并校验原始 JSON records，返回以 chunk_id 为 key 的字典。"""

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
        """按确定顺序持久化 records，方便学习时直接检查文件。"""

        payload: dict[str, object] = {
            "records": [records[key] for key in sorted(records)],
        }

        store_space = self._infer_record_embedding_space(records)
        if store_space is not None:
            # 显式持久化 store 级别的空间身份，让 JSON 文件自身就能说明
            # 这些 records 属于哪个 provider/model/dimensions。
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
        """写入批次改变持久化状态前，先完成基本校验。"""

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
        """校验后续恢复和查询 chunk 所必需的字段。"""

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
        """把 EmbeddedChunk 转成可 JSON 序列化的 record。"""

        self._validate_embedded_chunk(chunk)
        # 同时保存向量数据和原始 chunk 身份，后续检索才能返回标准 chunk，
        # 而不是只返回脱离上下文的分数。
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
        """把一条 JSON record 转回 EmbeddedChunk。"""

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
        """从原始持久化 records 中推断 embedding space。"""

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
    """计算余弦相似度，分数越高表示语义越接近。"""

    if len(left) != len(right):
        raise ValueError("Cosine similarity requires vectors with the same dimensions.")

    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def normalize(vector: list[float]) -> list[float]:
    """归一化向量，让余弦相似度计算更稳定。"""

    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
