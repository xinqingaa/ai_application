from pathlib import Path

from app.embeddings.providers import EmbeddingProvider
from app.indexing.index_manager import build_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.schemas import EmbeddedChunk, SourceChunk


def embed_question(question: str, provider: EmbeddingProvider) -> list[float]:
    """Embed a single user question using the provider's query path."""

    return provider.embed_query(question)


def embed_texts(
    texts: list[str],
    provider: EmbeddingProvider,
    batch_size: int = 8,
) -> list[list[float]]:
    """Embed document texts in batches so later phases can reuse the same path."""

    if batch_size <= 0:
        raise ValueError("Embedding batch size must be positive.")

    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        vectors.extend(provider.embed_documents(texts[start : start + batch_size]))
    return vectors


def embed_chunks(
    chunks: list[SourceChunk],
    provider: EmbeddingProvider,
    batch_size: int = 8,
) -> list[EmbeddedChunk]:
    """Attach vectors while preserving the Phase 1/2 SourceChunk identity."""

    vectors = embed_texts(
        texts=[chunk.content for chunk in chunks],
        provider=provider,
        batch_size=batch_size,
    )

    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected vector count.")

    embedded_chunks: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors):
        embedded_chunks.append(
            EmbeddedChunk(
                chunk=chunk,
                vector=vector,
                provider_name=provider.provider_name,
                model_name=provider.model_name,
                dimensions=len(vector),
            )
        )
    return embedded_chunks


def build_embedded_chunk_corpus(
    data_dir: Path,
    split_config: SplitterConfig,
    supported_suffixes: tuple[str, ...],
    provider: EmbeddingProvider,
    batch_size: int = 8,
) -> list[EmbeddedChunk]:
    """Reuse the Phase 2 chunk pipeline, then add the Phase 3 vector payload."""

    chunks = build_chunk_corpus(data_dir, split_config, supported_suffixes)
    return embed_chunks(chunks, provider, batch_size=batch_size)
