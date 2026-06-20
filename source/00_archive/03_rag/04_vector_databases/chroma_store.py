"""第四章向量存储契约的 Chroma backend。

这个模块把 PersistentVectorStore 讲过的同一组动作映射到真实 Chroma
持久化 collection：upsert、replace_document、similarity_search、
load_chunks 和 delete_by_document_id。
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from vector_store_basics import (
    CHAPTER_ROOT,
    EmbeddedChunk,
    EmbeddingProvider,
    EmbeddingSpace,
    RetrievalResult,
    SourceChunk,
    embedding_space_from_provider,
    ensure_matching_embedding_space,
    ensure_vector_dimensions,
    infer_chunks_embedding_space,
)

MetadataValue = str | int | float | bool
MetadataFilter = dict[str, MetadataValue]

DEFAULT_CHROMA_DIR = CHAPTER_ROOT / "store" / "chroma"
CHUNK_ID_KEY = "_rag_chunk_id"
DOCUMENT_ID_KEY = "_rag_document_id"
PROVIDER_NAME_KEY = "_rag_provider_name"
MODEL_NAME_KEY = "_rag_model_name"
DIMENSIONS_KEY = "_rag_dimensions"
INTERNAL_METADATA_KEYS = {
    CHUNK_ID_KEY,
    DOCUMENT_ID_KEY,
    PROVIDER_NAME_KEY,
    MODEL_NAME_KEY,
    DIMENSIONS_KEY,
}
# Chroma 可以持久化任意标量 metadata，所以第四章用几个保留 key
# 保存 chunk 身份和 embedding-space 身份，保证后续可以恢复对象。
SUPPORTED_DISTANCE_METRICS = {"cosine", "l2", "ip"}


def chromadb_is_available() -> bool:
    """检查可选的 Chroma 依赖是否已经安装。"""

    return find_spec("chromadb") is not None


@dataclass(frozen=True)
class ChromaVectorStoreConfig:
    """本章 Chroma 持久化 collection 的配置。"""

    persist_directory: Path = DEFAULT_CHROMA_DIR
    collection_name: str = "chapter4_chunks"
    distance_metric: str = "cosine"


class ChromaVectorStore:
    """第四章向量存储接口的 Chroma 实现。

    Chroma 负责保存向量、文档和标量 metadata。这个 wrapper 会把课程层面的
    存储契约显式保留下来：在 metadata 中保存 chunk 身份和 embedding-space 身份。
    """

    def __init__(self, config: ChromaVectorStoreConfig) -> None:
        """打开或创建配置指定的持久化 Chroma collection。"""

        if config.distance_metric not in SUPPORTED_DISTANCE_METRICS:
            raise ValueError(
                "Unsupported distance metric. Expected one of: "
                f"{', '.join(sorted(SUPPORTED_DISTANCE_METRICS))}."
            )

        chromadb_module = _load_chromadb()
        persist_directory = config.persist_directory.resolve()
        persist_directory.mkdir(parents=True, exist_ok=True)

        self.persist_directory = persist_directory
        self.collection_name = config.collection_name
        self.distance_metric = config.distance_metric
        self._client = chromadb_module.PersistentClient(
            path=self.persist_directory.as_posix()
        )
        self._collection = self._get_or_create_collection()

    def reset(self) -> None:
        """删除并重建 collection，让演示从干净状态开始。"""

        if self._collection_exists():
            self._client.delete_collection(self.collection_name)
        self._collection = self._get_or_create_collection()

    def count(self) -> int:
        """返回 Chroma collection 中的记录数量。"""

        return self._collection.count()

    def list_document_ids(self) -> list[str]:
        """返回从已存 chunks 中恢复出的全部 document_id。"""

        return sorted({chunk.chunk.document_id for chunk in self.load_chunks()})

    def embedding_space(self) -> EmbeddingSpace | None:
        """推断当前 collection 所代表的唯一 embedding space。"""

        return infer_chunks_embedding_space(self.load_chunks())

    def upsert(
        self,
        chunks: list[EmbeddedChunk],
        batch_size: int = 32,
    ) -> int:
        """按 chunk_id 向 Chroma 插入或覆盖 embedded chunks。

        参数：
            chunks: 待写入的 EmbeddedChunk 列表。
            batch_size: 每次 upsert 调用发送给 Chroma 的 chunk 数量。

        返回：
            实际写入的 chunk 数量。
        """

        if batch_size <= 0:
            raise ValueError("Vector store batch size must be positive.")

        validated_chunks, incoming_space = _validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        stored_space = self.embedding_space()
        if stored_space is not None and incoming_space is not None:
            # Chroma 本身不会强制校验 provider/model 兼容性；
            # 本章 wrapper 要显式守住这个契约。
            ensure_matching_embedding_space(
                actual=incoming_space,
                expected=stored_space,
                context="incoming chunks",
            )

        for start in range(0, len(validated_chunks), batch_size):
            batch = validated_chunks[start : start + batch_size]
            self._collection.upsert(
                ids=[item.chunk.chunk_id for item in batch],
                documents=[item.chunk.content for item in batch],
                metadatas=[_serialize_metadata(item) for item in batch],
                embeddings=[item.vector for item in batch],
            )
        return len(validated_chunks)

    def replace_document(
        self,
        chunks: list[EmbeddedChunk],
        batch_size: int = 32,
    ) -> int:
        """替换 incoming document ids 对应的全部旧 chunk。

        Chroma 原生 upsert 更偏 chunk 级写入，这里额外保留文档级替换语义。
        """

        validated_chunks, incoming_space = _validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        target_document_ids = {chunk.chunk.document_id for chunk in validated_chunks}
        # 即便底层数据库主要暴露 chunk 级写入，也要在这里保留文档级替换语义。
        remaining_chunks = [
            chunk
            for chunk in self.load_chunks()
            if chunk.chunk.document_id not in target_document_ids
        ]
        remaining_space = infer_chunks_embedding_space(remaining_chunks)
        if remaining_space is not None and incoming_space is not None:
            ensure_matching_embedding_space(
                actual=incoming_space,
                expected=remaining_space,
                context="incoming chunks",
            )

        for document_id in target_document_ids:
            self.delete_by_document_id(document_id)
        return self.upsert(validated_chunks, batch_size=batch_size)

    def get_chunks(
        self,
        where: MetadataFilter | None = None,
        limit: int | None = None,
    ) -> list[SourceChunk]:
        """只检查已存 SourceChunk，不暴露向量。"""

        return [chunk.chunk for chunk in self.load_chunks(where=where, limit=limit)]

    def load_chunks(
        self,
        where: MetadataFilter | None = None,
        limit: int | None = None,
    ) -> list[EmbeddedChunk]:
        """读取 Chroma records，并水合回 EmbeddedChunk 对象。"""

        if limit is not None and limit <= 0:
            raise ValueError("Chunk inspection limit must be positive.")
        if self.count() == 0:
            return []

        response = self._collection.get(
            where=where or None,
            limit=limit,
            include=["documents", "metadatas", "embeddings"],
        )
        chunks = _hydrate_get_results(response)
        infer_chunks_embedding_space(chunks)
        return chunks

    def similarity_search(
        self,
        query_vector: list[float],
        provider: EmbeddingProvider,
        top_k: int = 3,
        where: MetadataFilter | None = None,
    ) -> list[RetrievalResult]:
        """在 Chroma 中执行向量查询，并返回 RetrievalResult 对象。

        参数：
            query_vector: 使用写入时同一 provider 生成的查询向量。
            provider: 用于校验 query/store 空间一致性的 provider 身份。
            top_k: 最多返回的匹配数量。
            where: 可选 Chroma metadata 过滤条件。
        """

        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        ensure_vector_dimensions(query_vector, provider.dimensions, context="query vector")
        store_space = self.embedding_space()
        if store_space is None:
            return []

        ensure_matching_embedding_space(
            actual=embedding_space_from_provider(provider),
            expected=store_space,
            context="query provider",
        )

        response = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )
        return _hydrate_query_results(response)

    def delete_by_document_id(self, document_id: str) -> int:
        """删除内部 document_id 匹配的所有 Chroma records。"""

        existing = self.get_chunks(where={DOCUMENT_ID_KEY: document_id})
        if not existing:
            return 0
        self._collection.delete(where={DOCUMENT_ID_KEY: document_id})
        return len(existing)

    def _collection_exists(self) -> bool:
        for item in self._client.list_collections():
            name = item if isinstance(item, str) else getattr(item, "name", None)
            if name == self.collection_name:
                return True
        return False

    def _get_or_create_collection(self) -> Any:
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": self.distance_metric},
        )


def _load_chromadb() -> Any:
    """延迟导入 chromadb，让只跑 JSON 的演示不需要安装它。"""

    if not chromadb_is_available():
        raise RuntimeError(
            "Real Chroma support requires the `chromadb` package. "
            "Run `python -m pip install -r requirements.txt` in this chapter directory."
        )

    import chromadb

    return chromadb


def _validate_write_batch(
    chunks: list[EmbeddedChunk],
) -> tuple[list[EmbeddedChunk], EmbeddingSpace | None]:
    """触碰 Chroma collection 前，先校验写入批次。"""

    seen_chunk_ids: set[str] = set()
    for chunk in chunks:
        _validate_embedded_chunk(chunk)
        if chunk.chunk.chunk_id in seen_chunk_ids:
            raise ValueError(f"Write batch contains duplicate chunk_id={chunk.chunk.chunk_id}.")
        seen_chunk_ids.add(chunk.chunk.chunk_id)
    return chunks, infer_chunks_embedding_space(chunks)


def _validate_embedded_chunk(chunk: EmbeddedChunk) -> None:
    """校验 Chroma 持久化所需的最小字段。"""

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


def _serialize_metadata(chunk: EmbeddedChunk) -> MetadataFilter:
    """合并用户 metadata 和 Chroma 必须保留的内部字段。"""

    # 将用户 metadata 与存储内部 metadata 合并，让单条 Chroma record
    # 同时支持检索、按文档删除和空间校验。
    metadata: MetadataFilter = {
        CHUNK_ID_KEY: chunk.chunk.chunk_id,
        DOCUMENT_ID_KEY: chunk.chunk.document_id,
        PROVIDER_NAME_KEY: chunk.provider_name,
        MODEL_NAME_KEY: chunk.model_name,
        DIMENSIONS_KEY: chunk.dimensions,
    }
    metadata.update(chunk.chunk.metadata)

    for key, value in metadata.items():
        if not isinstance(value, (str, int, float, bool)):
            raise TypeError(
                f"Chroma metadata only supports scalar values. Got {type(value)!r} "
                f"for key {key!r}."
            )
    return metadata


def _hydrate_get_results(response: dict[str, Any]) -> list[EmbeddedChunk]:
    """把 collection.get(...) 的输出水合成 EmbeddedChunk 对象。"""

    ids = _as_list(response.get("ids"))
    documents = _as_list(response.get("documents"))
    metadatas = _as_list(response.get("metadatas"))
    embeddings = _as_list(response.get("embeddings"))

    chunks: list[EmbeddedChunk] = []
    for chunk_id, document, metadata, vector in zip(ids, documents, metadatas, embeddings):
        # Chroma 返回的是多组平行数组，水合阶段负责把它们重新组装成
        # 第四章自己的运行时对象。
        chunks.append(
            _deserialize_embedded_chunk(
                document=document,
                metadata=metadata,
                vector=vector,
                fallback_chunk_id=chunk_id,
            )
        )
    return chunks


def _hydrate_query_results(response: dict[str, Any]) -> list[RetrievalResult]:
    """把 collection.query(...) 的输出水合成 RetrievalResult 对象。"""

    ids = _first_nested_list(response.get("ids"))
    documents = _first_nested_list(response.get("documents"))
    metadatas = _first_nested_list(response.get("metadatas"))
    distances = _first_nested_list(response.get("distances"))

    results: list[RetrievalResult] = []
    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        results.append(
            RetrievalResult(
                chunk=_deserialize_source_chunk(
                    document=document,
                    metadata=metadata,
                    fallback_chunk_id=chunk_id,
                ),
                score=_distance_to_similarity(distance),
            )
        )
    return results


def _deserialize_embedded_chunk(
    *,
    document: str,
    metadata: MetadataFilter | None,
    vector: list[float] | None,
    fallback_chunk_id: str,
) -> EmbeddedChunk:
    """根据 Chroma 的 document/metadata/vector 字段重建 EmbeddedChunk。"""

    if not isinstance(vector, list):
        raise ValueError("Chroma response did not include embeddings for chunk hydration.")
    embedded_chunk = EmbeddedChunk(
        chunk=_deserialize_source_chunk(
            document=document,
            metadata=metadata,
            fallback_chunk_id=fallback_chunk_id,
        ),
        vector=[float(value) for value in vector],
        provider_name=str((metadata or {}).get(PROVIDER_NAME_KEY, "")),
        model_name=str((metadata or {}).get(MODEL_NAME_KEY, "")),
        dimensions=int((metadata or {}).get(DIMENSIONS_KEY, 0)),
    )
    _validate_embedded_chunk(embedded_chunk)
    return embedded_chunk


def _deserialize_source_chunk(
    *,
    document: str,
    metadata: MetadataFilter | None,
    fallback_chunk_id: str,
) -> SourceChunk:
    """重建 SourceChunk，并剥离只属于 Chroma 内部使用的 metadata key。"""

    metadata = metadata or {}
    chunk_metadata = {
        key: value for key, value in metadata.items() if key not in INTERNAL_METADATA_KEYS
    }
    return SourceChunk(
        chunk_id=str(metadata.get(CHUNK_ID_KEY, fallback_chunk_id)),
        document_id=str(metadata.get(DOCUMENT_ID_KEY, "")),
        content=document,
        metadata=chunk_metadata,
    )


def _distance_to_similarity(distance: float | None) -> float:
    """把 Chroma distance 转成第四章统一的“越高越好”的 score。"""

    if distance is None:
        return 0.0
    # Chroma 返回的是 distance 类值；第四章统一转成简单的“越高越好”分数，
    # 这样每个 backend 都能暴露同一种结果形状。
    return max(-1.0, 1.0 - float(distance))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        converted = value.tolist()
        return converted if isinstance(converted, list) else [converted]
    return list(value)


def _first_nested_list(value: Any) -> list[Any]:
    outer = _as_list(value)
    if not outer:
        return []
    first = outer[0]
    if hasattr(first, "tolist"):
        converted = first.tolist()
        return converted if isinstance(converted, list) else [converted]
    return list(first)
