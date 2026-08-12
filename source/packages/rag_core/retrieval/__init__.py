"""Retrieval public API."""

from rag_core.retrieval.errors import (
    RetrievalError,
    RetrievalErrorCode,
    RetrievalStage,
)
from rag_core.retrieval.models import (
    ChunkIndexReport,
    DenseDiagnostics,
    DenseHit,
    DenseSearchMode,
    DenseSearchResult,
    DeleteReport,
    LexicalDiagnostics,
    LexicalHit,
    LexicalIndexReport,
    LexicalSearchResult,
)
from rag_core.retrieval.postgres_chunks import PostgresChunkStore
from rag_core.retrieval.postgres_dense import PostgresDenseRetriever
from rag_core.retrieval.postgres_fts import PostgresFTSRetriever

__all__ = [
    "ChunkIndexReport",
    "DenseDiagnostics",
    "DenseHit",
    "DenseSearchMode",
    "DenseSearchResult",
    "DeleteReport",
    "LexicalDiagnostics",
    "LexicalHit",
    "LexicalIndexReport",
    "LexicalSearchResult",
    "PostgresChunkStore",
    "PostgresDenseRetriever",
    "PostgresFTSRetriever",
    "RetrievalError",
    "RetrievalErrorCode",
    "RetrievalStage",
]
