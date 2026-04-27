from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from chroma_store import (
    DEFAULT_CHROMA_DIR,
    ChromaVectorStore,
    ChromaVectorStoreConfig,
)
from langchain_adapter import (
    DEFAULT_LANGCHAIN_DIR,
    LangChainChromaConfig,
    build_documents,
    create_langchain_chroma,
    reset_langchain_chroma,
    retrieval_results_from_scored_documents,
)
from vector_store_basics import (
    DEFAULT_STORE_PATH,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    RetrievalResult,
    SourceChunk,
    VectorStoreConfig,
    demo_chunk_metadata,
    demo_embedded_chunks,
    demo_source_chunks,
    embed_chunks,
)

BackendName = Literal["json", "chroma", "langchain"]
MetadataValue = str | int | float | bool
MetadataPayload = dict[str, MetadataValue]


@dataclass
class VectorStoreManager:
    # The manager unifies responsibilities, not storage internals. Each backend
    # still keeps its own concrete write/search/delete mechanics underneath.
    backend: BackendName
    provider: LocalKeywordEmbeddingProvider
    json_store_path: Path = DEFAULT_STORE_PATH
    chroma_persist_directory: Path = DEFAULT_CHROMA_DIR
    chroma_collection_name: str = "chapter4_chunks"
    langchain_persist_directory: Path = DEFAULT_LANGCHAIN_DIR
    langchain_collection_name: str = "chapter4_langchain_chunks"

    def reset(self) -> None:
        if self.backend == "json":
            self._json_store().reset()
            return
        if self.backend == "chroma":
            self._chroma_store().reset()
            return
        reset_langchain_chroma(self._langchain_config())

    def ensure_index(self) -> None:
        if self.count() > 0:
            return

        # The teaching demos bootstrap each backend with the same logical corpus so
        # later search/delete/replace comparisons stay easy to reason about.
        if self.backend == "json":
            self._json_store().replace_document(demo_embedded_chunks(self.provider))
            return

        if self.backend == "chroma":
            self._chroma_store().replace_document(demo_embedded_chunks(self.provider))
            return

        vectorstore = self._langchain_store()
        source_chunks = demo_source_chunks()
        vectorstore.add_documents(
            documents=build_documents(source_chunks),
            ids=[chunk.chunk_id for chunk in source_chunks],
        )

    def add_documents(
        self,
        documents: list[str],
        *,
        metadatas: list[MetadataPayload] | None = None,
        ids: list[str] | None = None,
    ) -> int:
        source_chunks = self._build_source_chunks(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        return self._add_source_chunks(source_chunks)

    def replace_document(
        self,
        document_id: str,
        document: str,
        *,
        metadata: MetadataPayload | None = None,
    ) -> int:
        source_chunk = self._build_source_chunk(
            document=document,
            document_id=document_id,
            metadata=metadata,
        )
        if self.backend == "json":
            return self._json_store().replace_document(
                embed_chunks([source_chunk], self.provider)
            )
        if self.backend == "chroma":
            return self._chroma_store().replace_document(
                embed_chunks([source_chunk], self.provider)
            )

        # LangChain Chroma does not expose the same document-scoped replace helper,
        # so the manager preserves chapter semantics with delete-then-add.
        self.delete_document(document_id)
        return self._add_source_chunks([source_chunk])

    def delete_document(self, document_id: str) -> int:
        if self.backend == "json":
            return self._json_store().delete_by_document_id(document_id)
        if self.backend == "chroma":
            return self._chroma_store().delete_by_document_id(document_id)

        vectorstore = self._langchain_store()
        chunk_id = self._chunk_id_for_document(document_id)
        existing = vectorstore._collection.get(ids=[chunk_id], include=["metadatas"])
        ids = list(existing.get("ids") or [])
        if not ids:
            return 0
        vectorstore.delete(ids=ids)
        return len(ids)

    def search(
        self,
        question: str,
        *,
        top_k: int,
        filename: str | None = None,
    ) -> list[RetrievalResult]:
        if self.backend == "json":
            query_vector = self.provider.embed_query(question)
            return self._json_store().similarity_search(
                query_vector=query_vector,
                provider=self.provider,
                top_k=top_k,
                filename=filename,
            )

        if self.backend == "chroma":
            query_vector = self.provider.embed_query(question)
            return self._chroma_store().similarity_search(
                query_vector=query_vector,
                provider=self.provider,
                top_k=top_k,
                where={"filename": filename} if filename else None,
            )

        # For the LangChain backend, the vectorstore handles query embedding
        # internally, but the manager still normalizes the returned shape.
        vectorstore = self._langchain_store()
        search_kwargs: dict[str, object] = {"k": top_k}
        if filename:
            search_kwargs["filter"] = {"filename": filename}
        results = vectorstore.similarity_search_with_score(question, **search_kwargs)
        return retrieval_results_from_scored_documents(results)

    def count(self) -> int:
        if self.backend == "json":
            return self._json_store().count()
        if self.backend == "chroma":
            return self._chroma_store().count()
        return int(self._langchain_store()._collection.count())

    def list_document_ids(self) -> list[str]:
        if self.backend == "json":
            return self._json_store().list_document_ids()
        if self.backend == "chroma":
            return self._chroma_store().list_document_ids()

        response = self._langchain_store()._collection.get(include=["metadatas"])
        metadatas = response.get("metadatas") or []
        return sorted(
            {
                str(metadata.get("document_id"))
                for metadata in metadatas
                if metadata and metadata.get("document_id")
            }
        )

    def _add_source_chunks(self, source_chunks: list[SourceChunk]) -> int:
        if not source_chunks:
            return 0

        if self.backend == "json":
            return self._json_store().upsert(embed_chunks(source_chunks, self.provider))
        if self.backend == "chroma":
            return self._chroma_store().upsert(embed_chunks(source_chunks, self.provider))

        vectorstore = self._langchain_store()
        vectorstore.add_documents(
            documents=build_documents(source_chunks),
            ids=[chunk.chunk_id for chunk in source_chunks],
        )
        return len(source_chunks)

    def _build_source_chunks(
        self,
        *,
        documents: list[str],
        metadatas: list[MetadataPayload] | None,
        ids: list[str] | None,
    ) -> list[SourceChunk]:
        if ids is not None and len(ids) != len(documents):
            raise ValueError("ids length must match documents length.")
        if metadatas is not None and len(metadatas) != len(documents):
            raise ValueError("metadatas length must match documents length.")

        source_chunks: list[SourceChunk] = []
        for index, document in enumerate(documents):
            document_id = ids[index] if ids is not None else f"doc_{index}"
            metadata = metadatas[index] if metadatas is not None else None
            source_chunks.append(
                self._build_source_chunk(
                    document=document,
                    document_id=document_id,
                    metadata=metadata,
                )
            )
        return source_chunks

    def _build_source_chunk(
        self,
        *,
        document: str,
        document_id: str,
        metadata: MetadataPayload | None,
    ) -> SourceChunk:
        payload = dict(metadata or {})
        source = str(payload.get("source", f"data/{document_id}.md"))
        chunk_metadata = demo_chunk_metadata(source=source, content=document)
        chunk_metadata.update(payload)
        return SourceChunk(
            chunk_id=self._chunk_id_for_document(document_id),
            document_id=document_id,
            content=document,
            metadata=chunk_metadata,
        )

    def _chunk_id_for_document(self, document_id: str) -> str:
        return f"{document_id}:0"

    def _json_store(self) -> PersistentVectorStore:
        return PersistentVectorStore(
            VectorStoreConfig(store_path=self.json_store_path)
        )

    def _chroma_store(self) -> ChromaVectorStore:
        return ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.chroma_persist_directory,
                collection_name=self.chroma_collection_name,
            )
        )

    def _langchain_config(self) -> LangChainChromaConfig:
        return LangChainChromaConfig(
            persist_directory=self.langchain_persist_directory,
            collection_name=self.langchain_collection_name,
        )

    def _langchain_store(self):
        return create_langchain_chroma(self.provider, self._langchain_config())
