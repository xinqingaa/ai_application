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
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
else:  # pragma: no cover - exercised only when deps are missing
    Document = object  # type: ignore[assignment]
    Embeddings = object  # type: ignore[assignment]


def langchain_vectorstore_is_available() -> bool:
    return LANGCHAIN_CORE_AVAILABLE and LANGCHAIN_CHROMA_AVAILABLE


def require_langchain_vectorstore() -> None:
    if langchain_vectorstore_is_available():
        return
    raise RuntimeError(
        "LangChain Chroma support requires `langchain-core` and `langchain-chroma`. "
        "Run `python -m pip install -r requirements.txt` in this chapter directory."
    )


@dataclass(frozen=True)
class LangChainChromaConfig:
    persist_directory: Path = DEFAULT_LANGCHAIN_DIR
    collection_name: str = "chapter4_langchain_chunks"


class ProviderEmbeddingsAdapter(Embeddings):
    def __init__(self, provider: EmbeddingProvider) -> None:
        require_langchain_vectorstore()
        self.provider = provider

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.provider.embed_documents(list(texts))

    def embed_query(self, text: str) -> list[float]:
        return self.provider.embed_query(text)


def build_documents(chunks: list[SourceChunk] | None = None) -> list[Document]:
    require_langchain_vectorstore()
    source_chunks = demo_source_chunks() if chunks is None else chunks
    documents: list[Document] = []
    for chunk in source_chunks:
        metadata = dict(chunk.metadata)
        metadata["chunk_id"] = chunk.chunk_id
        metadata["document_id"] = chunk.document_id
        documents.append(Document(page_content=chunk.content, metadata=metadata))
    return documents


def create_langchain_chroma(
    provider: EmbeddingProvider,
    config: LangChainChromaConfig | None = None,
) -> Any:
    require_langchain_vectorstore()
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
    require_langchain_vectorstore()
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
    actual_config = config or LangChainChromaConfig()
    if actual_config.persist_directory.exists():
        shutil.rmtree(actual_config.persist_directory)


def similarity_results_from_documents(documents: list[Any]) -> list[RetrievalResult]:
    results: list[RetrievalResult] = []
    for document in documents:
        metadata = dict(getattr(document, "metadata", {}) or {})
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
    results: list[RetrievalResult] = []
    for document, distance in documents:
        metadata = dict(getattr(document, "metadata", {}) or {})
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
