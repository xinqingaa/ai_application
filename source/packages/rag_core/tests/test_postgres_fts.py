from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

from rag_core import (
    ChunkPolicy,
    ChunkStrategy,
    EvidenceEligibility,
    PostgresFTSRetriever,
    RetrievalError,
    RetrievalErrorCode,
    SourceRole,
    chunk_document,
    load_document,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE = REPO_ROOT / "source/apps/review_assistant/fixtures/rag/ingestion/order_rules.md"
MIGRATION = REPO_ROOT / "source/apps/review_assistant/infra/migrations/0001_create_rag_chunks.sql"


class FakeResult:
    def __init__(self, rows=None, *, rowcount: int = 0) -> None:
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, rows=None) -> None:
        self.rows = rows or []
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.executions.append((sql, params))
        return FakeResult(self.rows, rowcount=2)


class FakeConnect:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def __call__(self, dsn, **kwargs):
        assert dsn == "postgresql://fake"
        assert "row_factory" in kwargs
        return self.connection


def test_retriever_requires_database_url() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        PostgresFTSRetriever("")


def test_retriever_rejects_invalid_candidate_k() -> None:
    retriever = PostgresFTSRetriever("postgresql://unused")

    with pytest.raises(ValueError, match="candidate_k"):
        retriever.search("售后", candidate_k=0)


def test_search_maps_native_rank_and_diagnostics() -> None:
    connection = FakeConnection(
        [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "document_version": "1.0.0",
                "content": "售后接口 v2 必须提供 source_channel。",
                "source_role": "reference_knowledge",
                "evidence_eligibility": "current_evidence",
                "source_spans": [
                    {
                        "element_id": "element-1",
                        "start_char": 0,
                        "end_char": 12,
                        "text": "售后接口字段说明",
                        "locator": {
                            "kind": "markdown",
                            "line_start": 8,
                            "line_end": 10,
                            "heading_path": ["接口规则"],
                        },
                    }
                ],
                "business_metadata": {"knowledge_scope": "after_sale"},
                "matched_terms": ["techidsourcechannel"],
                "fts_rank": 0.75,
                "indexed_chunk_count": 4,
                "visible_chunk_count": 2,
                "matched_chunk_count": 1,
                "tsquery": "'techidsourcechannel'",
                "query_lexemes": ["source", "channel", "techidsourcechannel"],
            }
        ]
    )
    retriever = PostgresFTSRetriever(
        "postgresql://fake",
        connect=FakeConnect(connection),
    )

    result = retriever.search(
        "source_channel",
        candidate_k=3,
        knowledge_scope="after_sale",
        source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
        evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
    )

    assert result.hits[0].chunk_id == "chunk-1"
    assert result.hits[0].fts_rank == 0.75
    assert result.hits[0].route_rank == 1
    assert result.hits[0].source_spans[0].locator.line_start == 8
    assert result.diagnostics.matched_chunk_count == 1
    assert result.diagnostics.returned_chunk_count == 1
    assert result.diagnostics.indexed_chunk_count == 4
    assert result.diagnostics.visible_chunk_count == 2
    assert result.diagnostics.knowledge_scope == "after_sale"
    assert result.diagnostics.higher_is_better is True
    assert result.diagnostics.retriever_config_ref.startswith("postgres_fts@")
    assert connection.executions[0][1]["websearch_query"].count(" OR ") == 1


def test_search_preserves_successful_empty_result_diagnostics() -> None:
    connection = FakeConnection(
        [
            {
                "chunk_id": None,
                "indexed_chunk_count": 3,
                "visible_chunk_count": 3,
                "matched_chunk_count": None,
                "tsquery": "'逆向' | '服务'",
                "query_lexemes": ["逆向", "服务"],
            }
        ]
    )
    retriever = PostgresFTSRetriever(
        "postgresql://fake",
        connect=FakeConnect(connection),
    )

    result = retriever.search("逆向服务")

    assert result.hits == ()
    assert result.diagnostics.matched_chunk_count == 0
    assert result.diagnostics.tsquery == "'逆向' | '服务'"


def test_connection_failure_is_not_returned_as_empty_hits() -> None:
    def fail_connect(*args, **kwargs):
        raise psycopg.OperationalError("connection refused")

    retriever = PostgresFTSRetriever(
        "postgresql://fake",
        connect=fail_connect,
    )

    with pytest.raises(RetrievalError) as captured:
        retriever.search("售后")

    assert captured.value.code is RetrievalErrorCode.CONNECTION_FAILED


@pytest.mark.integration
def test_real_postgres_indexes_and_retrieves_exact_identifier() -> None:
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("设置 TEST_DATABASE_URL 后运行真实 PostgreSQL 集成测试")

    with psycopg.connect(dsn) as connection:
        connection.execute(MIGRATION.read_text(encoding="utf-8"))

    document = load_document(
        FIXTURE,
        document_id="TEST-KR-ORDER-STATE",
        document_version="1.0.0",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        metadata={"knowledge_scope": "after_sale_test"},
    ).document
    result = chunk_document(
        document,
        ChunkPolicy(
            name="postgres_fts_integration",
            version="1.0.0",
            strategy=ChunkStrategy.STRUCTURE_AWARE,
            max_tokens=48,
        ),
    )
    retriever = PostgresFTSRetriever(dsn)
    chunk_ids = [chunk.chunk_id for chunk in result.retrieval_chunks]
    try:
        report = retriever.upsert_chunks(result.retrieval_chunks)
        search = retriever.search("source_channel", candidate_k=3)

        assert report.indexed_chunks == len(result.retrieval_chunks)
        assert search.hits
        assert "source_channel" in search.hits[0].content
        assert search.diagnostics.rank_name == "postgresql_ts_rank"
        assert search.diagnostics.higher_is_better is True
    finally:
        retriever.delete_chunks(chunk_ids)
