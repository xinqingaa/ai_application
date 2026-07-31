"""Retrieval public API."""

from rag_core.retrieval.errors import (
    RetrievalError,
    RetrievalErrorCode,
    RetrievalStage,
)
from rag_core.retrieval.models import (
    DeleteReport,
    LexicalDiagnostics,
    LexicalHit,
    LexicalIndexReport,
    LexicalSearchResult,
)
from rag_core.retrieval.postgres_fts import PostgresFTSRetriever

__all__ = [
    "DeleteReport",
    "LexicalDiagnostics",
    "LexicalHit",
    "LexicalIndexReport",
    "LexicalSearchResult",
    "PostgresFTSRetriever",
    "RetrievalError",
    "RetrievalErrorCode",
    "RetrievalStage",
]
