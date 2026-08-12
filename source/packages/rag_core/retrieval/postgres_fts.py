"""PostgreSQL FTS storage and lexical retrieval using explicit native ranks."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from time import perf_counter
from typing import Any

import psycopg
from psycopg.rows import dict_row

from rag_core.chunking.models import Chunk
from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.lexical import LexicalAnalyzer
from rag_core.retrieval.errors import RetrievalStage, map_postgres_error
from rag_core.retrieval.models import (
    DeleteReport,
    LexicalDiagnostics,
    LexicalHit,
    LexicalIndexReport,
    LexicalSearchResult,
)
from rag_core.retrieval.postgres_chunks import PostgresChunkStore

_SEARCH_SQL = """
WITH query_input AS (
    SELECT
        websearch_to_tsquery(%(postgres_config)s::regconfig, %(websearch_query)s)
            AS ts_query,
        tsvector_to_array(
            to_tsvector(%(postgres_config)s::regconfig, %(query_lexical_text)s)
        ) AS query_lexemes
),
visible AS MATERIALIZED (
    SELECT chunk.*
    FROM review_assistant.rag_chunks AS chunk
    WHERE chunk.lexical_config_ref = %(lexical_config_ref)s
      AND (
        %(knowledge_scope)s::text IS NULL
        OR chunk.business_metadata ->> 'knowledge_scope' = %(knowledge_scope)s
      )
      AND (
        %(source_roles)s::text[] IS NULL
        OR chunk.source_role = ANY (%(source_roles)s)
      )
      AND (
        %(evidence_eligibilities)s::text[] IS NULL
        OR chunk.evidence_eligibility = ANY (%(evidence_eligibilities)s)
      )
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
    FROM visible AS chunk
    CROSS JOIN query_input
    WHERE chunk.search_vector @@ query_input.ts_query
),
ranked AS (
    SELECT
        matched.*,
        COUNT(*) OVER () AS matched_chunk_count
    FROM matched
    ORDER BY fts_rank DESC, chunk_id ASC
    LIMIT %(candidate_k)s
),
indexed_stats AS (
    SELECT COUNT(*) AS indexed_chunk_count
    FROM review_assistant.rag_chunks
    WHERE lexical_config_ref = %(lexical_config_ref)s
),
visible_stats AS (
    SELECT COUNT(*) AS visible_chunk_count FROM visible
)
SELECT
    ranked.*,
    query_input.ts_query::text AS tsquery,
    query_input.query_lexemes,
    indexed_stats.indexed_chunk_count,
    visible_stats.visible_chunk_count
FROM query_input
CROSS JOIN indexed_stats
CROSS JOIN visible_stats
LEFT JOIN ranked ON TRUE
ORDER BY ranked.fts_rank DESC NULLS LAST, ranked.chunk_id ASC NULLS LAST
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
        self._chunk_store = PostgresChunkStore(
            resolved_dsn,
            analyzer=self.analyzer,
            connect=connect,
        )

    def upsert_chunks(self, chunks: Sequence[Chunk]) -> LexicalIndexReport:
        return self._chunk_store.upsert_chunks(chunks)

    def search(
        self,
        query: str,
        *,
        candidate_k: int = 5,
        knowledge_scope: str | None = None,
        source_roles: Sequence[SourceRole] | None = None,
        evidence_eligibilities: Sequence[EvidenceEligibility] | None = None,
    ) -> LexicalSearchResult:
        if candidate_k <= 0:
            raise ValueError("candidate_k 必须大于 0")
        if knowledge_scope is not None and not knowledge_scope.strip():
            raise ValueError("knowledge_scope 不能是空字符串")
        analysis = self.analyzer.analyze_query(query)
        started = perf_counter()
        params = {
            "postgres_config": analysis.postgres_config,
            "websearch_query": analysis.websearch_query,
            "query_lexical_text": analysis.lexical_text,
            "lexical_config_ref": analysis.config_ref,
            "candidate_k": candidate_k,
            "knowledge_scope": knowledge_scope,
            "source_roles": (
                None if not source_roles else [item.value for item in source_roles]
            ),
            "evidence_eligibilities": (
                None
                if not evidence_eligibilities
                else [item.value for item in evidence_eligibilities]
            ),
        }
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                rows = connection.execute(_SEARCH_SQL, params).fetchall()
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.QUERY) from exc

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
                knowledge_scope=knowledge_scope,
                source_roles=tuple(source_roles or ()),
                evidence_eligibilities=tuple(evidence_eligibilities or ()),
                indexed_chunk_count=int(first["indexed_chunk_count"] or 0),
                visible_chunk_count=int(first["visible_chunk_count"] or 0),
                matched_chunk_count=int(first["matched_chunk_count"] or 0),
                returned_chunk_count=len(hits),
                candidate_k=candidate_k,
                rank_name="postgresql_ts_rank",
                higher_is_better=True,
                latency_ms=latency_ms,
            ),
        )

    def delete_chunks(self, chunk_ids: Sequence[str]) -> DeleteReport:
        return self._chunk_store.delete_chunks(chunk_ids)


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
