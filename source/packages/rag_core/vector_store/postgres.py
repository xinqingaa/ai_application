"""pgvector persistence bound to stable Chunk and Embedding-space identities."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from time import perf_counter
from typing import Any

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg import sql
from psycopg.rows import dict_row

from rag_core.chunking.models import Chunk
from rag_core.embedding.models import EmbeddingRecord
from rag_core.retrieval.errors import RetrievalStage, map_postgres_error
from rag_core.vector_store.models import (
    EmbeddingSpace,
    HNSWIndexReport,
    VectorDeleteReport,
    VectorIndexReport,
    hnsw_index_name,
)

_UPSERT_SQL = """
INSERT INTO review_assistant.rag_chunk_embeddings (
    chunk_id,
    embedding_space_ref,
    embedding_provider,
    embedding_config_ref,
    embedding_model,
    embedding_dimensions,
    preprocessing_version,
    embedding
) VALUES (
    %(chunk_id)s,
    %(embedding_space_ref)s,
    %(embedding_provider)s,
    %(embedding_config_ref)s,
    %(embedding_model)s,
    %(embedding_dimensions)s,
    %(preprocessing_version)s,
    %(embedding)s
)
ON CONFLICT (chunk_id, embedding_space_ref) DO UPDATE SET
    embedding_provider = EXCLUDED.embedding_provider,
    embedding_config_ref = EXCLUDED.embedding_config_ref,
    embedding_model = EXCLUDED.embedding_model,
    embedding_dimensions = EXCLUDED.embedding_dimensions,
    preprocessing_version = EXCLUDED.preprocessing_version,
    embedding = EXCLUDED.embedding,
    updated_at = CURRENT_TIMESTAMP
"""

_DELETE_SQL = """
DELETE FROM review_assistant.rag_chunk_embeddings
WHERE embedding_space_ref = %(embedding_space_ref)s
  AND chunk_id = ANY (%(chunk_ids)s)
"""


class PostgresVectorStore:
    """Store Chunk embeddings without duplicating the Embedding provider."""

    def __init__(
        self,
        dsn: str | None = None,
        *,
        connect: Callable[..., Any] = psycopg.connect,
        register: Callable[[Any], None] = register_vector,
    ) -> None:
        resolved_dsn = dsn or os.getenv("DATABASE_URL", "")
        if not resolved_dsn.strip():
            raise ValueError("DATABASE_URL 不能为空")
        self._dsn = resolved_dsn
        self._connect = connect
        self._register = register

    def upsert_embeddings(
        self,
        chunks: Sequence[Chunk],
        records: Sequence[EmbeddingRecord],
    ) -> VectorIndexReport:
        rows, space = _embedding_rows(chunks, records)
        started = perf_counter()
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                self._register(connection)
                with connection.cursor() as cursor:
                    cursor.executemany(_UPSERT_SQL, rows)
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.INDEXING) from exc
        return VectorIndexReport(
            indexed_embeddings=len(rows),
            embedding_space=space,
            latency_ms=(perf_counter() - started) * 1000,
        )

    def ensure_hnsw_index(self, space: EmbeddingSpace) -> HNSWIndexReport:
        if space.dimensions > 2000:
            raise ValueError(
                "pgvector 的 vector HNSW 索引最多支持 2000 维；"
                "当前空间需要改用其他存储类型或索引方案"
            )
        index_name = hnsw_index_name(space)
        statement = sql.SQL(
            """
            CREATE INDEX IF NOT EXISTS {index_name}
            ON review_assistant.rag_chunk_embeddings
            USING hnsw ((embedding::vector({dimensions})) vector_cosine_ops)
            WHERE embedding_space_ref = {space_ref}
            """
        ).format(
            index_name=sql.Identifier(index_name),
            dimensions=sql.Literal(space.dimensions),
            space_ref=sql.Literal(space.space_ref),
        )
        started = perf_counter()
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                connection.execute(statement)
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.INDEX_SETUP) from exc
        return HNSWIndexReport(
            index_name=index_name,
            embedding_space=space,
            latency_ms=(perf_counter() - started) * 1000,
        )

    def delete_embeddings(
        self,
        chunk_ids: Sequence[str],
        *,
        space: EmbeddingSpace,
    ) -> VectorDeleteReport:
        normalized_ids = [chunk_id for chunk_id in chunk_ids if chunk_id.strip()]
        if not normalized_ids:
            raise ValueError("delete_embeddings 至少需要一个非空 chunk_id")
        started = perf_counter()
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                result = connection.execute(
                    _DELETE_SQL,
                    {
                        "embedding_space_ref": space.space_ref,
                        "chunk_ids": normalized_ids,
                    },
                )
                deleted = result.rowcount
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.DELETION) from exc
        return VectorDeleteReport(
            deleted_embeddings=max(deleted, 0),
            latency_ms=(perf_counter() - started) * 1000,
        )


def _embedding_rows(
    chunks: Sequence[Chunk],
    records: Sequence[EmbeddingRecord],
) -> tuple[list[dict[str, Any]], EmbeddingSpace]:
    if not chunks:
        raise ValueError("upsert_embeddings 至少需要一个 Chunk")
    if len(chunks) != len(records):
        raise ValueError("Chunk 与 EmbeddingRecord 数量必须一致")
    space = EmbeddingSpace.from_records(records)
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for chunk, record in zip(chunks, records, strict=True):
        if record.text_id != chunk.chunk_id:
            raise ValueError(
                "EmbeddingRecord.text_id 必须等于对应 chunk_id；"
                f"record={record.text_id!r} chunk={chunk.chunk_id!r}"
            )
        if record.text != chunk.text:
            raise ValueError("EmbeddingRecord.text 必须与对应 Chunk.text 一致")
        if chunk.chunk_id in seen_ids:
            raise ValueError(f"重复 chunk_id：{chunk.chunk_id}")
        seen_ids.add(chunk.chunk_id)
        rows.append(
            {
                "chunk_id": chunk.chunk_id,
                "embedding_space_ref": space.space_ref,
                "embedding_provider": space.provider,
                "embedding_config_ref": space.config_ref,
                "embedding_model": space.model,
                "embedding_dimensions": space.dimensions,
                "preprocessing_version": space.preprocessing_version,
                "embedding": Vector(list(record.vector)),
            }
        )
    return rows, space
