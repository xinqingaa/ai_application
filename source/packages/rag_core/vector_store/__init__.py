"""PostgreSQL vector persistence contracts."""

from rag_core.vector_store.models import (
    EmbeddingSpace,
    HNSWIndexReport,
    VectorDeleteReport,
    VectorIndexReport,
    hnsw_index_name,
)
from rag_core.vector_store.postgres import PostgresVectorStore

__all__ = [
    "EmbeddingSpace",
    "HNSWIndexReport",
    "PostgresVectorStore",
    "VectorDeleteReport",
    "VectorIndexReport",
    "hnsw_index_name",
]
