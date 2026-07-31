"""PostgreSQL FTS storage and lexical retrieval using explicit native ranks."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from time import perf_counter
from typing import Any

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from rag_core.chunking.models import Chunk
from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.lexical import LexicalAnalyzer
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

_SEARCH_SQL = """
WITH query_input AS (
    SELECT
        websearch_to_tsquery(%(postgres_config)s::regconfig, %(websearch_query)s)
            AS ts_query,
        tsvector_to_array(
            to_tsvector(%(postgres_config)s::regconfig, %(query_lexical_text)s)
        ) AS query_lexemes
),
matched AS (
    SELECT
        chunk.chunk_id,
        chunk.document_id,
        chunk.document_version,
        chunk.content,
        chunk.source_role,
        chunk.evidence_eligibility,
        chunk.business_metadata,
        ARRAY(
            SELECT lexeme
            FROM unnest(tsvector_to_array(chunk.search_vector)) AS term(lexeme)
            WHERE lexeme = ANY (query_input.query_lexemes)
            ORDER BY lexeme
        ) AS matched_terms,
        ts_rank(chunk.search_vector, query_input.ts_query) AS fts_rank
    FROM review_assistant.rag_chunks AS chunk
    CROSS JOIN query_input
    WHERE chunk.lexical_config_ref = %(lexical_config_ref)s
      AND chunk.search_vector @@ query_input.ts_query
),
ranked AS (
    SELECT
        matched.*,
        COUNT(*) OVER () AS matched_chunk_count
    FROM matched
    ORDER BY fts_rank DESC, chunk_id ASC
    LIMIT %(candidate_k)s
)
SELECT
    ranked.*,
    query_input.ts_query::text AS tsquery,
    query_input.query_lexemes
FROM query_input
LEFT JOIN ranked ON TRUE
ORDER BY ranked.fts_rank DESC NULLS LAST, ranked.chunk_id ASC NULLS LAST
"""

_DELETE_SQL = """
DELETE FROM review_assistant.rag_chunks
WHERE chunk_id = ANY (%(chunk_ids)s)
"""


class PostgresFTSRetriever:
    """Persist traceable chunks and retrieve lexical candidates from PostgreSQL."""

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

    def upsert_chunks(self, chunks: Sequence[Chunk]) -> LexicalIndexReport:
        if not chunks:
            raise ValueError("upsert_chunks 至少需要一个 Chunk")
        started = perf_counter()
        rows = [self._chunk_row(chunk) for chunk in chunks]
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(_UPSERT_SQL, rows)
        except psycopg.Error as exc:
            raise _retrieval_error(exc, RetrievalStage.INDEXING) from exc
        return LexicalIndexReport(
            indexed_chunks=len(rows),
            lexical_config_ref=self.analyzer.config.config_ref,
            latency_ms=(perf_counter() - started) * 1000,
        )

    def search(self, query: str, *, candidate_k: int = 5) -> LexicalSearchResult:
        if candidate_k <= 0:
            raise ValueError("candidate_k 必须大于 0")
        analysis = self.analyzer.analyze_query(query)
        started = perf_counter()
        params = {
            "postgres_config": analysis.postgres_config,
            "websearch_query": analysis.websearch_query,
            "query_lexical_text": analysis.lexical_text,
            "lexical_config_ref": analysis.config_ref,
            "candidate_k": candidate_k,
        }
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                rows = connection.execute(_SEARCH_SQL, params).fetchall()
        except psycopg.Error as exc:
            raise _retrieval_error(exc, RetrievalStage.QUERY) from exc

        latency_ms = (perf_counter() - started) * 1000
        hit_rows = [row for row in rows if row["chunk_id"] is not None]
        hits = tuple(
            _hit_from_row(row, index + 1) for index, row in enumerate(hit_rows)
        )
        first = rows[0]
        return LexicalSearchResult(
            hits=hits,
            diagnostics=LexicalDiagnostics(
                query=query,
                normalized_query=analysis.normalized_text,
                query_terms=analysis.terms,
                postgres_query_terms=tuple(first["query_lexemes"]),
                tsquery=first["tsquery"],
                query_operator=self.analyzer.config.query_operator,
                lexical_config_ref=analysis.config_ref,
                retriever_config_ref=self.analyzer.config.retriever_config_ref,
                postgres_config=analysis.postgres_config,
                matched_chunk_count=int(first["matched_chunk_count"] or 0),
                returned_chunk_count=len(hits),
                candidate_k=candidate_k,
                rank_name="postgresql_ts_rank",
                higher_is_better=True,
                latency_ms=latency_ms,
            ),
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
            raise _retrieval_error(exc, RetrievalStage.DELETION) from exc
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
            "source_spans": Jsonb([_source_span_payload(span) for span in chunk.source_spans]),
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


def _hit_from_row(row: dict[str, Any], route_rank: int) -> LexicalHit:
    return LexicalHit(
        chunk_id=row["chunk_id"],
        document_id=row["document_id"],
        document_version=row["document_version"],
        content=row["content"],
        source_role=SourceRole(row["source_role"]),
        evidence_eligibility=EvidenceEligibility(row["evidence_eligibility"]),
        business_metadata=row["business_metadata"],
        matched_terms=tuple(row["matched_terms"]),
        fts_rank=float(row["fts_rank"]),
        route_rank=route_rank,
    )


def _retrieval_error(
    exc: psycopg.Error,
    stage: RetrievalStage,
) -> RetrievalError:
    if isinstance(exc, errors.InvalidPassword):
        code = RetrievalErrorCode.AUTH_FAILED
        message = "PostgreSQL 用户名或密码错误"
    elif isinstance(exc, errors.UndefinedTable):
        code = RetrievalErrorCode.MIGRATION_REQUIRED
        message = "缺少 review_assistant.rag_chunks，请先执行数据库 migration"
    elif isinstance(exc, errors.InsufficientPrivilege):
        code = RetrievalErrorCode.PERMISSION_DENIED
        message = "当前 PostgreSQL role 没有执行该操作的权限"
    elif isinstance(exc, psycopg.OperationalError):
        code = RetrievalErrorCode.CONNECTION_FAILED
        message = "无法连接 PostgreSQL，请检查服务、host、port、database 和网络"
    else:
        code = RetrievalErrorCode.DATABASE_ERROR
        message = str(exc).strip() or "PostgreSQL 执行失败"
    return RetrievalError(code=code, stage=stage, message=message, raw=exc)
