"""Embedding representation helpers for RAG experiments."""

from rag_core.embedding.models import (
    EmbeddingBatchResult,
    EmbeddingRecord,
    SimilarityMetric,
    SimilarityObservation,
    embed_texts,
    pairwise_similarity,
    similarity,
)

__all__ = [
    "EmbeddingBatchResult",
    "EmbeddingRecord",
    "SimilarityMetric",
    "SimilarityObservation",
    "embed_texts",
    "pairwise_similarity",
    "similarity",
]
