from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from app.embeddings.providers import EmbeddingProvider
from app.schemas import EmbeddedChunk, RetrievalResult, SourceChunk

MetadataValue = str | int | float | bool
MetadataFilter = dict[str, MetadataValue]

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
SUPPORTED_DISTANCE_METRICS = {"cosine", "l2", "ip"}


def chromadb_is_available() -> bool:
    """Return whether the real Chroma dependency is installed."""

    return find_spec("chromadb") is not None


@dataclass(slots=True)
class ChromaVectorStoreConfig:
    """Minimal configuration required to create a persistent Chroma collection."""

    persist_directory: Path
    collection_name: str = "course_chunks"
    distance_metric: str = "cosine"


class ChromaVectorStore:
    """Real Chroma-backed vector store used in Phase 4."""

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

    def count(self) -> int:
        """Return the number of vectors currently stored in the collection."""

        return self._collection.count()

    def reset(self) -> None:
        """Drop and recreate the collection while keeping the persist directory."""

        if self._collection_exists():
            self._client.delete_collection(self.collection_name)
        self._collection = self._get_or_create_collection()

    def upsert(
        self,
        chunks: list[EmbeddedChunk],
        batch_size: int = 32,
    ) -> None:
        """Write embedded chunks into Chroma while preserving chunk identity."""

        if batch_size <= 0:
            raise ValueError("Vector store batch size must be positive.")
        if not chunks:
            return

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self._collection.upsert(
                ids=[item.chunk.chunk_id for item in batch],
                documents=[item.chunk.content for item in batch],
                metadatas=[_serialize_metadata(item) for item in batch],
                embeddings=[item.vector for item in batch],
            )

    def get_chunks(
        self,
        where: MetadataFilter | None = None,
        limit: int | None = None,
    ) -> list[SourceChunk]:
        """Read chunks back from Chroma for inspection or deletion checks."""

        if limit is not None and limit <= 0:
            raise ValueError("Chunk inspection limit must be positive.")
        if self.count() == 0:
            return []

        response = self._collection.get(
            where=where or None,
            limit=limit,
            include=["documents", "metadatas"],
        )
        return _hydrate_get_results(response)

    def similarity_search(
        self,
        question: str,
        provider: EmbeddingProvider,
        top_k: int = 5,
        where: MetadataFilter | None = None,
    ) -> list[RetrievalResult]:
        """Embed the query and ask Chroma for the nearest chunks."""

        query_vector = provider.embed_query(question)
        return self.similarity_search_by_vector(query_vector, top_k=top_k, where=where)

    def similarity_search_by_vector(
        self,
        query_vector: list[float],
        top_k: int = 5,
        where: MetadataFilter | None = None,
    ) -> list[RetrievalResult]:
        """Query Chroma directly with a precomputed query vector."""

        if top_k <= 0:
            raise ValueError("Top-k must be positive.")
        if self.count() == 0:
            return []

        response = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )
        return _hydrate_query_results(response)

    def delete_by_document_id(self, document_id: str) -> None:
        """Delete every chunk belonging to a specific document."""

        self._collection.delete(where={DOCUMENT_ID_KEY: document_id})

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
            "Install it with `pip install -r requirements.txt` inside "
            "`phase_4_vector_databases`."
        )

    import chromadb

    return chromadb


def _serialize_metadata(chunk: EmbeddedChunk) -> MetadataFilter:
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


def _hydrate_get_results(response: dict[str, Any]) -> list[SourceChunk]:
    ids = response.get("ids") or []
    documents = response.get("documents") or []
    metadatas = response.get("metadatas") or []

    chunks: list[SourceChunk] = []
    for chunk_id, document, metadata in zip(ids, documents, metadatas):
        chunks.append(
            _deserialize_source_chunk(
                document=document,
                metadata=metadata,
                fallback_chunk_id=chunk_id,
            )
        )
    return chunks


def _hydrate_query_results(response: dict[str, Any]) -> list[RetrievalResult]:
    ids = (response.get("ids") or [[]])[0]
    documents = (response.get("documents") or [[]])[0]
    metadatas = (response.get("metadatas") or [[]])[0]
    distances = (response.get("distances") or [[]])[0]

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


def _deserialize_source_chunk(
    document: str,
    metadata: MetadataFilter | None,
    fallback_chunk_id: str,
) -> SourceChunk:
    metadata = metadata or {}
    chunk_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in INTERNAL_METADATA_KEYS
    }
    return SourceChunk(
        chunk_id=str(metadata.get(CHUNK_ID_KEY, fallback_chunk_id)),
        document_id=str(metadata.get(DOCUMENT_ID_KEY, "")),
        content=document,
        metadata=chunk_metadata,
    )


def _distance_to_similarity(distance: float | None) -> float | None:
    if distance is None:
        return None
    return max(-1.0, 1.0 - float(distance))
