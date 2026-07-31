"""Structured PostgreSQL retrieval errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RetrievalStage(str, Enum):
    CONNECTION = "connection"
    INDEXING = "indexing"
    QUERY = "query"
    DELETION = "deletion"


class RetrievalErrorCode(str, Enum):
    CONNECTION_FAILED = "connection_failed"
    AUTH_FAILED = "auth_failed"
    MIGRATION_REQUIRED = "migration_required"
    PERMISSION_DENIED = "permission_denied"
    DATABASE_ERROR = "database_error"


@dataclass
class RetrievalError(Exception):
    code: RetrievalErrorCode
    stage: RetrievalStage
    message: str
    raw: Any = None

    def __str__(self) -> str:
        return f"{self.stage.value}/{self.code.value}: {self.message}"
