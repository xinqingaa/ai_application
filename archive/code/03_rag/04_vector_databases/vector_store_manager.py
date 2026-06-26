"""第四章多个向量存储 backend 的统一教学管理器。

这个 manager 刻意保持很小：它展示 JSON、原生 Chroma、LangChain Chroma
如何共享 add/search/replace/delete 语义，同时不隐藏底层实现差异。
"""

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
    # manager 统一的是职责，不是底层存储细节；每个 backend 仍然保留
    # 自己具体的写入、查询和删除机制。
    backend: BackendName
    provider: LocalKeywordEmbeddingProvider
    json_store_path: Path = DEFAULT_STORE_PATH
    chroma_persist_directory: Path = DEFAULT_CHROMA_DIR
    chroma_collection_name: str = "chapter4_chunks"
    langchain_persist_directory: Path = DEFAULT_LANGCHAIN_DIR
    langchain_collection_name: str = "chapter4_langchain_chunks"

    def reset(self) -> None:
        """只重置当前选中 backend 的持久化状态。"""

        if self.backend == "json":
            self._json_store().reset()
            return
        if self.backend == "chroma":
            self._chroma_store().reset()
            return
        reset_langchain_chroma(self._langchain_config())

    def ensure_index(self) -> None:
        """当选中 backend 为空时创建演示索引。"""

        if self.count() > 0:
            return

        # 教学演示用同一份逻辑语料初始化每个 backend，方便后面对比
        # search/delete/replace 行为。
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
        """通过选中 backend 添加原始文档文本。

        参数：
            documents: 待存储文本。在这个教学 manager 中，每段文本会变成一个 SourceChunk。
            metadatas: 可选 metadata 列表，需要和 documents 一一对应。
            ids: 可选 document id 列表，需要和 documents 一一对应。
        """

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
        """替换一个逻辑文档，并保持文档级整体替换语义。"""

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

        # LangChain Chroma 没有暴露同样的文档级 replace helper，
        # 所以 manager 用“先删再加”保留本章语义。
        self.delete_document(document_id)
        return self._add_source_chunks([source_chunk])

    def delete_document(self, document_id: str) -> int:
        """从选中 backend 中删除一个逻辑文档。"""

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
        """查询选中 backend，并将结果归一化成 RetrievalResult[]。"""

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

        # LangChain backend 内部会处理 query embedding；manager 仍然负责
        # 把返回结果归一化成本章统一形状。
        vectorstore = self._langchain_store()
        search_kwargs: dict[str, object] = {"k": top_k}
        if filename:
            search_kwargs["filter"] = {"filename": filename}
        results = vectorstore.similarity_search_with_score(question, **search_kwargs)
        return retrieval_results_from_scored_documents(results)

    def count(self) -> int:
        """返回选中 backend 当前的记录数量。"""

        if self.backend == "json":
            return self._json_store().count()
        if self.backend == "chroma":
            return self._chroma_store().count()
        return int(self._langchain_store()._collection.count())

    def list_document_ids(self) -> list[str]:
        """列出选中 backend 中的 document_id。"""

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
        """使用具体 backend 的原生写入路径写入 SourceChunk[]。"""

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
        """为教学 manager 的每段原始文档构造一个 SourceChunk。"""

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
        """创建一个稳定 SourceChunk，并合并调用方 metadata 与默认 metadata。"""

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
        """根据 document_id 派生单 chunk 文档使用的 chunk_id。"""

        return f"{document_id}:0"

    def _json_store(self) -> PersistentVectorStore:
        """根据当前配置创建 JSON store adapter。"""

        return PersistentVectorStore(
            VectorStoreConfig(store_path=self.json_store_path)
        )

    def _chroma_store(self) -> ChromaVectorStore:
        """根据当前配置创建原生 Chroma store adapter。"""

        return ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.chroma_persist_directory,
                collection_name=self.chroma_collection_name,
            )
        )

    def _langchain_config(self) -> LangChainChromaConfig:
        """为当前 manager 构造 LangChain Chroma 配置。"""

        return LangChainChromaConfig(
            persist_directory=self.langchain_persist_directory,
            collection_name=self.langchain_collection_name,
        )

    def _langchain_store(self):
        """根据当前配置打开 LangChain Chroma VectorStore。"""

        return create_langchain_chroma(self.provider, self._langchain_config())
