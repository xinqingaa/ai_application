"""Shared PostgreSQL persistence for traceable chunks."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from time import perf_counter
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from rag_core.chunking.models import Chunk
from rag_core.lexical import LexicalAnalyzer
from rag_core.retrieval.errors import RetrievalStage, map_postgres_error
from rag_core.retrieval.models import ChunkIndexReport, DeleteReport

_UPSERT_SQL = """
INSERT INTO review_assistant.rag_chunks (
    chunk_id,
    document_id,
    document_version,
    parent_chunk_id,
    original_filename,
    file_format,
    chunk_kind,
    ordinal,
    token_count,
    source_role,
    evidence_eligibility,
    content,
    source_spans,
    business_metadata,
    lexical_text,
    lexical_config_ref
) VALUES (
    %(chunk_id)s,
    %(document_id)s,
    %(document_version)s,
    %(parent_chunk_id)s,
    %(original_filename)s,
    %(file_format)s,
    %(chunk_kind)s,
    %(ordinal)s,
    %(token_count)s,
    %(source_role)s,
    %(evidence_eligibility)s,
    %(content)s,
    %(source_spans)s,
    %(business_metadata)s,
    %(lexical_text)s,
    %(lexical_config_ref)s
)
ON CONFLICT (chunk_id) DO UPDATE SET
    document_id = EXCLUDED.document_id,
    document_version = EXCLUDED.document_version,
    parent_chunk_id = EXCLUDED.parent_chunk_id,
    original_filename = EXCLUDED.original_filename,
    file_format = EXCLUDED.file_format,
    chunk_kind = EXCLUDED.chunk_kind,
    ordinal = EXCLUDED.ordinal,
    token_count = EXCLUDED.token_count,
    source_role = EXCLUDED.source_role,
    evidence_eligibility = EXCLUDED.evidence_eligibility,
    content = EXCLUDED.content,
    source_spans = EXCLUDED.source_spans,
    business_metadata = EXCLUDED.business_metadata,
    lexical_text = EXCLUDED.lexical_text,
    lexical_config_ref = EXCLUDED.lexical_config_ref,
    updated_at = CURRENT_TIMESTAMP
"""

_DELETE_SQL = """
DELETE FROM review_assistant.rag_chunks
WHERE chunk_id = ANY (%(chunk_ids)s)
"""


class PostgresChunkStore:
    """Persist the shared Chunk row used by lexical and dense indexes."""

    def __init__(
        self,
        dsn: str | None = None,
        *,
        analyzer: LexicalAnalyzer | None = None,
        connect: Callable[..., Any] = psycopg.connect,
    ) -> None:
        resolved_dsn = dsn or os.getenv("DATABASE_URL", "")
        if not resolved_dsn.strip():
            raise ValueError("DATABASE_URL 不能为空")
        self._dsn = resolved_dsn
        self.analyzer = analyzer or LexicalAnalyzer()
        self._connect = connect

    def upsert_chunks(self, chunks: Sequence[Chunk]) -> ChunkIndexReport:
        if not chunks:
            raise ValueError("upsert_chunks 至少需要一个 Chunk")
        started = perf_counter()
        rows = [self._chunk_row(chunk) for chunk in chunks]
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(_UPSERT_SQL, rows)
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.INDEXING) from exc
        return ChunkIndexReport(
            indexed_chunks=len(rows),
            lexical_config_ref=self.analyzer.config.config_ref,
            latency_ms=(perf_counter() - started) * 1000,
        )

    def delete_chunks(self, chunk_ids: Sequence[str]) -> DeleteReport:
        normalized_ids = [chunk_id for chunk_id in chunk_ids if chunk_id.strip()]
        if not normalized_ids:
            raise ValueError("delete_chunks 至少需要一个非空 chunk_id")
        started = perf_counter()
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                result = connection.execute(_DELETE_SQL, {"chunk_ids": normalized_ids})
                deleted = result.rowcount
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.DELETION) from exc
        return DeleteReport(
            deleted_chunks=max(deleted, 0),
            latency_ms=(perf_counter() - started) * 1000,
        )

    def _chunk_row(self, chunk: Chunk) -> dict[str, Any]:
        analysis = self.analyzer.analyze_document(chunk.text)
        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "document_version": chunk.document_version,
            "parent_chunk_id": chunk.parent_chunk_id,
            "original_filename": chunk.original_filename,
            "file_format": chunk.file_format.value,
            "chunk_kind": chunk.kind.value,
            "ordinal": chunk.ordinal,
            "token_count": chunk.token_count,
            "source_role": chunk.source_role.value,
            "evidence_eligibility": chunk.evidence_eligibility.value,
            "content": chunk.text,
            "source_spans": Jsonb(
                [_source_span_payload(span) for span in chunk.source_spans]
            ),
            "business_metadata": Jsonb(dict(chunk.business_metadata)),
            "lexical_text": analysis.lexical_text,
            "lexical_config_ref": analysis.config_ref,
        }


def _source_span_payload(span: Any) -> dict[str, Any]:
    locator = span.locator
    return {
        "element_id": span.element_id,
        "start_char": span.start_char,
        "end_char": span.end_char,
        "text": span.text,
        "locator": {
            "kind": locator.kind,
            "line_start": locator.line_start,
            "line_end": locator.line_end,
            "page_number": locator.page_number,
            "paragraph_index": locator.paragraph_index,
            "table_index": locator.table_index,
            "heading_path": list(locator.heading_path),
        },
    }
