"""第四章向量存储示例的 LangChain 适配层。

课程保留自己的 SourceChunk、RetrievalResult 和 EmbeddingProvider 契约；
这个模块展示这些契约如何映射到 LangChain 的 Document、Embeddings
和 Chroma VectorStore 抽象。
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
import shutil
from typing import Any

from vector_store_basics import (
    CHAPTER_ROOT,
    EmbeddingProvider,
    RetrievalResult,
    SourceChunk,
    demo_source_chunks,
)

DEFAULT_LANGCHAIN_DIR = CHAPTER_ROOT / "store" / "langchain_chroma"

LANGCHAIN_CORE_AVAILABLE = find_spec("langchain_core") is not None
LANGCHAIN_CHROMA_AVAILABLE = find_spec("langchain_chroma") is not None

if LANGCHAIN_CORE_AVAILABLE:
    # langchain-core 提供框架级基础对象：Document 承载文本和 metadata，
    # Embeddings 定义写入/查询时向量化方法的标准接口。
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
else:  # pragma: no cover - 只在依赖缺失时覆盖
    Document = object  # type: ignore[assignment]
    Embeddings = object  # type: ignore[assignment]


def langchain_vectorstore_is_available() -> bool:
    """检查可选的 LangChain VectorStore 依赖是否存在。"""

    return LANGCHAIN_CORE_AVAILABLE and LANGCHAIN_CHROMA_AVAILABLE


def require_langchain_vectorstore() -> None:
    """当 LangChain 依赖缺失时，用可执行的提示信息失败。"""

    if langchain_vectorstore_is_available():
        return
    raise RuntimeError(
        "LangChain Chroma support requires `langchain-core` and `langchain-chroma`. "
        "Run `python -m pip install -r requirements.txt` in this chapter directory."
    )


@dataclass(frozen=True)
class LangChainChromaConfig:
    """LangChain 管理的 Chroma collection 配置。"""

    persist_directory: Path = DEFAULT_LANGCHAIN_DIR
    collection_name: str = "chapter4_langchain_chunks"


class ProviderEmbeddingsAdapter(Embeddings):
    """把本章 EmbeddingProvider 适配到 LangChain 的 Embeddings 接口。"""

    def __init__(self, provider: EmbeddingProvider) -> None:
        """保存 LangChain 后续会调用的文档/query 向量化 provider。"""

        require_langchain_vectorstore()
        self.provider = provider

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """LangChain 写入 records 时，用本章 provider 向量化文档文本。"""

        # LangChain 期待自己的 Embeddings 接口；本章保留统一 provider 契约，
        # 在这里做适配，而不是重新定义一套 embedding 语义。
        return self.provider.embed_documents(list(texts))

    def embed_query(self, text: str) -> list[float]:
        """LangChain 执行相似度查询时，用本章 provider 向量化 query。"""

        return self.provider.embed_query(text)


def build_documents(chunks: list[SourceChunk] | None = None) -> list[Any]:
    """把 SourceChunk[] 转成 LangChain Document[]。

    chunk_id 和 document_id 会复制到 metadata 中，这样搜索结果才能转回
    本章标准的 RetrievalResult 形状。
    """

    require_langchain_vectorstore()
    source_chunks = demo_source_chunks() if chunks is None else chunks
    documents: list[Any] = []
    for chunk in source_chunks:
        # 将 chunk_id/document_id 放入 metadata，后续 LangChain 结果才能
        # 转回本章自己的 SourceChunk / RetrievalResult 对象。
        metadata = dict(chunk.metadata)
        metadata["chunk_id"] = chunk.chunk_id
        metadata["document_id"] = chunk.document_id
        documents.append(Document(page_content=chunk.content, metadata=metadata))
    return documents


def create_langchain_chroma(
    provider: EmbeddingProvider,
    config: LangChainChromaConfig | None = None,
) -> Any:
    """使用本章 provider 打开或创建 LangChain Chroma VectorStore。"""

    require_langchain_vectorstore()
    # langchain-chroma 提供 LangChain 风格的 Chroma VectorStore；
    # 底层仍然是 Chroma，只是对外暴露 similarity_search/as_retriever 等接口。
    from langchain_chroma import Chroma

    actual_config = config or LangChainChromaConfig()
    actual_config.persist_directory.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=actual_config.collection_name,
        persist_directory=actual_config.persist_directory.as_posix(),
        embedding_function=ProviderEmbeddingsAdapter(provider),
    )


def create_langchain_chroma_from_documents(
    provider: EmbeddingProvider,
    config: LangChainChromaConfig | None = None,
    chunks: list[SourceChunk] | None = None,
) -> Any:
    """通过 Chroma.from_documents(...) 初始化 LangChain Chroma。"""

    require_langchain_vectorstore()
    # from_documents 是 LangChain 的便捷初始化入口：传入 Document[] 和
    # Embeddings 适配器后，由 VectorStore 负责调用 embed_documents 并写入。
    from langchain_chroma import Chroma

    actual_config = config or LangChainChromaConfig()
    actual_config.persist_directory.mkdir(parents=True, exist_ok=True)
    documents = build_documents(chunks)
    ids = [str(document.metadata["chunk_id"]) for document in documents]
    return Chroma.from_documents(
        documents=documents,
        embedding=ProviderEmbeddingsAdapter(provider),
        ids=ids,
        collection_name=actual_config.collection_name,
        persist_directory=actual_config.persist_directory.as_posix(),
    )


def reset_langchain_chroma(config: LangChainChromaConfig | None = None) -> None:
    """删除 LangChain Chroma 持久化目录，让演示从干净状态开始。"""

    actual_config = config or LangChainChromaConfig()
    if actual_config.persist_directory.exists():
        shutil.rmtree(actual_config.persist_directory)


def similarity_results_from_documents(documents: list[Any]) -> list[RetrievalResult]:
    """把不带显式分数的 LangChain Document 结果转成 RetrievalResult[]。"""

    results: list[RetrievalResult] = []
    for document in documents:
        metadata = dict(getattr(document, "metadata", {}) or {})
        # 当 LangChain 返回不带显式分数的 Document 时，反向执行
        # SourceChunk -> Document 的映射。
        chunk = SourceChunk(
            chunk_id=str(metadata.pop("chunk_id", "")),
            document_id=str(metadata.pop("document_id", "")),
            content=str(getattr(document, "page_content", "")),
            metadata=metadata,
        )
        results.append(RetrievalResult(chunk=chunk, score=0.0))
    return results


def retrieval_results_from_scored_documents(
    documents: list[tuple[Any, float]],
) -> list[RetrievalResult]:
    """把 LangChain 的 (Document, distance) 元组转成 RetrievalResult[]。"""

    results: list[RetrievalResult] = []
    for document, distance in documents:
        metadata = dict(getattr(document, "metadata", {}) or {})
        # LangChain 暴露的是 distance；第四章希望返回带“后端无关 score 字段”的
        # 标准检索结果。
        chunk = SourceChunk(
            chunk_id=str(metadata.pop("chunk_id", "")),
            document_id=str(metadata.pop("document_id", "")),
            content=str(getattr(document, "page_content", "")),
            metadata=metadata,
        )
        results.append(
            RetrievalResult(
                chunk=chunk,
                score=max(-1.0, 1.0 - float(distance)),
            )
        )
    return results
