"""Dense retrieval over pgvector with explicit distance and index diagnostics."""

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

from rag_core.embedding.models import EmbeddingRecord
from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.retrieval.errors import RetrievalStage, map_postgres_error
from rag_core.retrieval.models import (
    DenseDiagnostics,
    DenseHit,
    DenseSearchMode,
    DenseSearchResult,
    source_spans_from_payload,
)
from rag_core.vector_store.models import EmbeddingSpace, hnsw_index_name


class PostgresDenseRetriever:
    """Retrieve nearest visible chunks from one compatible Embedding space."""

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

    def search(
        self,
        query: EmbeddingRecord,
        *,
        candidate_k: int = 5,
        knowledge_scope: str | None = None,
        source_roles: Sequence[SourceRole] | None = None,
        evidence_eligibilities: Sequence[EvidenceEligibility] | None = None,
        mode: DenseSearchMode = DenseSearchMode.EXACT,
        inspect_plan: bool = False,
    ) -> DenseSearchResult:
        if candidate_k <= 0:
            raise ValueError("candidate_k 必须大于 0")
        if knowledge_scope is not None and not knowledge_scope.strip():
            raise ValueError("knowledge_scope 不能是空字符串")
        space = EmbeddingSpace.from_record(query)
        if mode is DenseSearchMode.HNSW and space.dimensions > 2000:
            raise ValueError("当前向量维度超过 pgvector vector HNSW 的 2000 维上限")

        filters, params = _filters(
            space,
            knowledge_scope=knowledge_scope,
            source_roles=source_roles,
            evidence_eligibilities=evidence_eligibilities,
        )
        params.update(
            {
                "query_vector": Vector(list(query.vector)),
                "candidate_k": candidate_k,
            }
        )
        distance = _distance_expression(mode, space.dimensions)
        query_sql = _ranked_sql(filters, distance)
        count_sql = _count_sql(filters)
        plan_node_types: tuple[str, ...] = ()
        index_name = hnsw_index_name(space) if mode is DenseSearchMode.HNSW else None
        index_used: bool | None = None
        started = perf_counter()
        try:
            with self._connect(self._dsn, row_factory=dict_row) as connection:
                self._register(connection)
                counts = connection.execute(count_sql, params).fetchone()
                if inspect_plan:
                    explain_sql = sql.SQL("EXPLAIN (FORMAT JSON) ") + _ranked_sql(
                        filters,
                        distance,
                    )
                    plan_rows = connection.execute(explain_sql, params).fetchall()
                    plan_node_types, used_indexes = _plan_details(plan_rows)
                    index_used = index_name in used_indexes if index_name else False
                rows = connection.execute(query_sql, params).fetchall()
        except psycopg.Error as exc:
            raise map_postgres_error(exc, RetrievalStage.QUERY) from exc

        latency_ms = (perf_counter() - started) * 1000
        hits = tuple(_dense_hit(row, rank + 1) for rank, row in enumerate(rows))
        return DenseSearchResult(
            hits=hits,
            diagnostics=DenseDiagnostics(
                query=query.text,
                embedding_space_ref=space.space_ref,
                provider=space.provider,
                config_ref=space.config_ref,
                model=space.model,
                dimensions=space.dimensions,
                preprocessing_version=space.preprocessing_version,
                knowledge_scope=knowledge_scope,
                source_roles=tuple(source_roles or ()),
                evidence_eligibilities=tuple(evidence_eligibilities or ()),
                indexed_chunk_count=int(counts["indexed_chunk_count"] or 0),
                visible_chunk_count=int(counts["visible_chunk_count"] or 0),
                returned_chunk_count=len(hits),
                candidate_k=candidate_k,
                distance_name="pgvector_cosine_distance",
                lower_is_better=True,
                search_mode=mode,
                index_name=index_name,
                index_used=index_used,
                plan_node_types=plan_node_types,
                latency_ms=latency_ms,
            ),
        )


def _filters(
    space: EmbeddingSpace,
    *,
    knowledge_scope: str | None,
    source_roles: Sequence[SourceRole] | None,
    evidence_eligibilities: Sequence[EvidenceEligibility] | None,
) -> tuple[list[sql.Composable], dict[str, Any]]:
    clauses: list[sql.Composable] = [
        sql.SQL("embedding.embedding_space_ref = %(embedding_space_ref)s")
    ]
    params: dict[str, Any] = {"embedding_space_ref": space.space_ref}
    if knowledge_scope is not None:
        clauses.append(
            sql.SQL(
                "chunk.business_metadata ->> 'knowledge_scope' = %(knowledge_scope)s"
            )
        )
        params["knowledge_scope"] = knowledge_scope
    if source_roles:
        clauses.append(sql.SQL("chunk.source_role = ANY (%(source_roles)s)"))
        params["source_roles"] = [role.value for role in source_roles]
    if evidence_eligibilities:
        clauses.append(
            sql.SQL("chunk.evidence_eligibility = ANY (%(evidence_eligibilities)s)")
        )
        params["evidence_eligibilities"] = [
            item.value for item in evidence_eligibilities
        ]
    return clauses, params


def _distance_expression(
    mode: DenseSearchMode,
    dimensions: int,
) -> sql.Composable:
    if mode is DenseSearchMode.HNSW:
        return sql.SQL(
            "embedding.embedding::vector({dimensions}) "
            "<=> %(query_vector)s::vector({dimensions})"
        ).format(dimensions=sql.Literal(dimensions))
    return sql.SQL("embedding.embedding <=> %(query_vector)s")


def _visible_sql(
    filters: Sequence[sql.Composable],
    distance: sql.Composable,
) -> sql.Composable:
    where = sql.SQL(" AND ").join(filters)
    return sql.SQL(
        """
        SELECT
            chunk.chunk_id,
            chunk.document_id,
            chunk.document_version,
            chunk.content,
            chunk.source_role,
            chunk.evidence_eligibility,
            chunk.source_spans,
            chunk.business_metadata,
            {distance} AS cosine_distance
        FROM review_assistant.rag_chunk_embeddings AS embedding
        JOIN review_assistant.rag_chunks AS chunk
          ON chunk.chunk_id = embedding.chunk_id
        WHERE {where}
        """
    ).format(distance=distance, where=where)


def _ranked_sql(
    filters: Sequence[sql.Composable],
    distance: sql.Composable,
) -> sql.Composable:
    return sql.SQL(
        """
        SELECT *
        FROM ({visible}) AS visible
        ORDER BY cosine_distance ASC
        LIMIT %(candidate_k)s
        """
    ).format(visible=_visible_sql(filters, distance))


def _count_sql(
    filters: Sequence[sql.Composable],
) -> sql.Composable:
    where = sql.SQL(" AND ").join(filters)
    return sql.SQL(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM review_assistant.rag_chunk_embeddings
                WHERE embedding_space_ref = %(embedding_space_ref)s
            ) AS indexed_chunk_count,
            COUNT(*) AS visible_chunk_count
        FROM review_assistant.rag_chunk_embeddings AS embedding
        JOIN review_assistant.rag_chunks AS chunk
          ON chunk.chunk_id = embedding.chunk_id
        WHERE {where}
        """
    ).format(where=where)


def _dense_hit(row: dict[str, Any], route_rank: int) -> DenseHit:
    distance = float(row["cosine_distance"])
    return DenseHit(
        chunk_id=row["chunk_id"],
        document_id=row["document_id"],
        document_version=row["document_version"],
        content=row["content"],
        source_role=SourceRole(row["source_role"]),
        evidence_eligibility=EvidenceEligibility(row["evidence_eligibility"]),
        business_metadata=row["business_metadata"],
        cosine_distance=distance,
        cosine_similarity=1.0 - distance,
        route_rank=route_rank,
        source_spans=source_spans_from_payload(row.get("source_spans", [])),
    )


def _plan_details(rows: Sequence[dict[str, Any]]) -> tuple[tuple[str, ...], set[str]]:
    if not rows:
        return (), set()
    payload = rows[0].get("QUERY PLAN")
    if not isinstance(payload, list) or not payload:
        return (), set()
    root = payload[0].get("Plan", {})
    node_types: list[str] = []
    indexes: set[str] = set()

    def visit(node: dict[str, Any]) -> None:
        node_type = node.get("Node Type")
        if node_type:
            node_types.append(str(node_type))
        index_name = node.get("Index Name")
        if index_name:
            indexes.add(str(index_name))
        for child in node.get("Plans", []):
            visit(child)

    visit(root)
    return tuple(node_types), indexes
