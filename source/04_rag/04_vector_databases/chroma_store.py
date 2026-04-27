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
# Chroma can persist arbitrary scalar metadata, so chapter 4 uses a few reserved
# keys to keep chunk identity and embedding-space identity recoverable.
SUPPORTED_DISTANCE_METRICS = {"cosine", "l2", "ip"}


def chromadb_is_available() -> bool:
    return find_spec("chromadb") is not None


@dataclass(frozen=True)
class ChromaVectorStoreConfig:
    persist_directory: Path = DEFAULT_CHROMA_DIR
    collection_name: str = "chapter4_chunks"
    distance_metric: str = "cosine"


class ChromaVectorStore:
    def __init__(self, config: ChromaVectorStoreConfig) -> None:
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
        if self._collection_exists():
            self._client.delete_collection(self.collection_name)
        self._collection = self._get_or_create_collection()

    def count(self) -> int:
        return self._collection.count()

    def list_document_ids(self) -> list[str]:
        return sorted({chunk.chunk.document_id for chunk in self.load_chunks()})

    def embedding_space(self) -> EmbeddingSpace | None:
        return infer_chunks_embedding_space(self.load_chunks())

    def upsert(
        self,
        chunks: list[EmbeddedChunk],
        batch_size: int = 32,
    ) -> int:
        if batch_size <= 0:
            raise ValueError("Vector store batch size must be positive.")

        validated_chunks, incoming_space = _validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        stored_space = self.embedding_space()
        if stored_space is not None and incoming_space is not None:
            # Chroma itself does not enforce provider/model compatibility.
            # The chapter store keeps that contract explicit.
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
        validated_chunks, incoming_space = _validate_write_batch(chunks)
        if not validated_chunks:
            return 0

        target_document_ids = {chunk.chunk.document_id for chunk in validated_chunks}
        # replace_document keeps document-level semantics even on top of a database
        # that primarily exposes chunk-level writes.
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
        return [chunk.chunk for chunk in self.load_chunks(where=where, limit=limit)]

    def load_chunks(
        self,
        where: MetadataFilter | None = None,
        limit: int | None = None,
    ) -> list[EmbeddedChunk]:
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
    seen_chunk_ids: set[str] = set()
    for chunk in chunks:
        _validate_embedded_chunk(chunk)
        if chunk.chunk.chunk_id in seen_chunk_ids:
            raise ValueError(f"Write batch contains duplicate chunk_id={chunk.chunk.chunk_id}.")
        seen_chunk_ids.add(chunk.chunk.chunk_id)
    return chunks, infer_chunks_embedding_space(chunks)


def _validate_embedded_chunk(chunk: EmbeddedChunk) -> None:
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
    # We merge user metadata with storage-internal metadata so a single Chroma
    # record can be used for retrieval, delete-by-document, and space validation.
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
    ids = _as_list(response.get("ids"))
    documents = _as_list(response.get("documents"))
    metadatas = _as_list(response.get("metadatas"))
    embeddings = _as_list(response.get("embeddings"))

    chunks: list[EmbeddedChunk] = []
    for chunk_id, document, metadata, vector in zip(ids, documents, metadatas, embeddings):
        # Chroma returns parallel arrays, so hydration is where we reassemble them
        # into chapter-4 runtime objects.
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
    if distance is None:
        return 0.0
    # Chroma returns distance-like values; chapter 4 converts them into a simple
    # higher-is-better score so every backend can expose the same result shape.
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
