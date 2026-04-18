"""Embedding providers and adapters."""
from app.embeddings.providers import (
    EmbeddingProvider,
    EmbeddingProviderConfig,
    LocalHashEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    create_embedding_provider,
)
from app.embeddings.similarity import cosine_similarity, score_query_against_chunks
from app.embeddings.vectorizer import (
    build_embedded_chunk_corpus,
    embed_chunks,
    embed_question,
    embed_texts,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingProviderConfig",
    "LocalHashEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "build_embedded_chunk_corpus",
    "cosine_similarity",
    "create_embedding_provider",
    "embed_chunks",
    "embed_question",
    "embed_texts",
    "score_query_against_chunks",
]
