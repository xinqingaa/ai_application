"""Structured PostgreSQL retrieval errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import psycopg
from psycopg import errors


class RetrievalStage(str, Enum):
    CONNECTION = "connection"
    INDEXING = "indexing"
    INDEX_SETUP = "index_setup"
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


def map_postgres_error(
    exc: psycopg.Error,
    stage: RetrievalStage,
) -> RetrievalError:
    """Keep PostgreSQL failures visible and consistent across retrieval routes."""

    if isinstance(exc, errors.InvalidPassword):
        code = RetrievalErrorCode.AUTH_FAILED
        message = "PostgreSQL 用户名或密码错误"
    elif isinstance(
        exc,
        (
            errors.UndefinedTable,
            errors.UndefinedObject,
            errors.UndefinedFunction,
        ),
    ):
        code = RetrievalErrorCode.MIGRATION_REQUIRED
        message = "数据库对象不完整，请执行 review_assistant 的全部 migration"
    elif isinstance(exc, errors.InsufficientPrivilege):
        code = RetrievalErrorCode.PERMISSION_DENIED
        message = "当前 PostgreSQL role 没有执行该操作的权限"
    elif isinstance(exc, errors.ForeignKeyViolation):
        code = RetrievalErrorCode.DATABASE_ERROR
        message = "向量引用的 Chunk 不存在，请先保存 Chunk 再写入向量"
    elif isinstance(exc, psycopg.OperationalError):
        code = RetrievalErrorCode.CONNECTION_FAILED
        message = "无法连接 PostgreSQL，请检查服务、host、port、database 和网络"
    else:
        code = RetrievalErrorCode.DATABASE_ERROR
        message = str(exc).strip() or "PostgreSQL 执行失败"
    return RetrievalError(code=code, stage=stage, message=message, raw=exc)
