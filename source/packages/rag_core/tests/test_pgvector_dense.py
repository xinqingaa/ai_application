from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

from rag_core import (
    ChunkPolicy,
    ChunkStrategy,
    DenseSearchMode,
    EmbeddingRecord,
    EmbeddingSpace,
    EvidenceEligibility,
    PostgresChunkStore,
    PostgresDenseRetriever,
    PostgresVectorStore,
    SourceRole,
    chunk_document,
    load_document,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE = REPO_ROOT / "review_assistant/fixtures/v0/ingestion/order_rules.md"
MIGRATIONS = (
    REPO_ROOT / "review_assistant/infra/migrations/0001_create_rag_chunks.sql",
    REPO_ROOT / "review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql",
)


class FakeResult:
    def __init__(self, rows=None, *, rowcount: int = 0) -> None:
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._rows[0]

    def fetchall(self):
        return self._rows


class FakeCursor:
    def __init__(self, connection) -> None:
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def executemany(self, statement, rows) -> None:
        self.connection.executions.append((statement, rows))


class FakeConnection:
    def __init__(self, results=None) -> None:
        self.results = list(results or [])
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def cursor(self):
        return FakeCursor(self)

    def execute(self, statement, params=None):
        self.executions.append((statement, params))
        if self.results:
            return self.results.pop(0)
        return FakeResult(rowcount=1)


class FakeConnect:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def __call__(self, dsn, **kwargs):
        assert dsn == "postgresql://fake"
        assert "row_factory" in kwargs
        return self.connection


def _chunks():
    document = load_document(
        FIXTURE,
        document_id="TEST-KR-DENSE",
        document_version="1.0.0",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        metadata={"knowledge_scope": "after_sale_test"},
    ).document
    return chunk_document(
        document,
        ChunkPolicy(
            name="dense_test",
            version="1.0.0",
            strategy=ChunkStrategy.STRUCTURE_AWARE,
            max_tokens=48,
        ),
    ).retrieval_chunks


def _record(chunk, vector, *, model: str = "test-embedding") -> EmbeddingRecord:
    return EmbeddingRecord(
        text=chunk.text,
        vector=tuple(vector),
        model=model,
        dimensions=len(vector),
        config_ref="embedding.test",
        provider="test_provider",
        text_id=chunk.chunk_id,
        preprocessing_version="chunk-text-v1",
    )


def test_embedding_space_ref_changes_with_model_or_preprocessing() -> None:
    chunk = _chunks()[0]
    original = EmbeddingSpace.from_record(_record(chunk, [1.0, 0.0, 0.0]))
    changed_model = EmbeddingSpace.from_record(
        _record(chunk, [1.0, 0.0, 0.0], model="other-model")
    )
    changed_preprocessing = EmbeddingSpace(
        provider=original.provider,
        config_ref=original.config_ref,
        model=original.model,
        dimensions=original.dimensions,
        preprocessing_version="title-plus-chunk-v2",
    )

    assert original.space_ref != changed_model.space_ref
    assert original.space_ref != changed_preprocessing.space_ref


def test_embedding_space_rejects_declared_dimension_mismatch() -> None:
    chunk = _chunks()[0]
    record = _record(chunk, [1.0, 0.0, 0.0])
    invalid = EmbeddingRecord(
        text=record.text,
        vector=record.vector,
        model=record.model,
        dimensions=4,
        config_ref=record.config_ref,
        provider=record.provider,
        text_id=record.text_id,
        preprocessing_version=record.preprocessing_version,
    )

    with pytest.raises(ValueError, match="dimensions"):
        EmbeddingSpace.from_record(invalid)


def test_vector_store_binds_each_vector_to_matching_chunk() -> None:
    chunks = _chunks()[:2]
    records = (
        _record(chunks[0], [1.0, 0.0, 0.0]),
        _record(chunks[1], [0.0, 1.0, 0.0]),
    )
    connection = FakeConnection()
    store = PostgresVectorStore(
        "postgresql://fake",
        connect=FakeConnect(connection),
        register=lambda connection: None,
    )

    report = store.upsert_embeddings(chunks, records)

    assert report.indexed_embeddings == 2
    statement, rows = connection.executions[0]
    assert "rag_chunk_embeddings" in statement
    assert rows[0]["chunk_id"] == chunks[0].chunk_id
    assert rows[0]["embedding_space_ref"] == report.embedding_space.space_ref


def test_vector_store_rejects_record_bound_to_wrong_chunk() -> None:
    chunks = _chunks()[:2]
    records = (
        _record(chunks[1], [1.0, 0.0, 0.0]),
        _record(chunks[0], [0.0, 1.0, 0.0]),
    )
    store = PostgresVectorStore(
        "postgresql://fake",
        connect=FakeConnect(FakeConnection()),
        register=lambda connection: None,
    )

    with pytest.raises(ValueError, match="text_id"):
        store.upsert_embeddings(chunks, records)


def test_hnsw_index_is_scoped_to_one_embedding_space() -> None:
    chunk = _chunks()[0]
    space = EmbeddingSpace.from_record(_record(chunk, [1.0, 0.0, 0.0]))
    connection = FakeConnection()
    store = PostgresVectorStore(
        "postgresql://fake",
        connect=FakeConnect(connection),
        register=lambda connection: None,
    )

    report = store.ensure_hnsw_index(space)
    statement, params = connection.executions[0]
    rendered = statement.as_string(None)

    assert params is None
    assert report.index_name in rendered
    assert "vector_cosine_ops" in rendered
    assert "vector(3)" in rendered
    assert space.space_ref in rendered


def test_dense_search_maps_cosine_distance_and_visibility_diagnostics() -> None:
    chunk = _chunks()[0]
    query = EmbeddingRecord(
        text="发起逆向服务",
        vector=(1.0, 0.0, 0.0),
        model="test-embedding",
        dimensions=3,
        config_ref="embedding.test",
        provider="test_provider",
        text_id="query-synonym",
        preprocessing_version="chunk-text-v1",
    )
    connection = FakeConnection(
        [
            FakeResult([{"indexed_chunk_count": 4, "visible_chunk_count": 2}]),
            FakeResult(
                [
                    {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "document_version": chunk.document_version,
                        "content": chunk.text,
                        "source_role": chunk.source_role.value,
                        "evidence_eligibility": chunk.evidence_eligibility.value,
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
                        "business_metadata": dict(chunk.business_metadata),
                        "cosine_distance": 0.2,
                    }
                ]
            ),
        ]
    )
    retriever = PostgresDenseRetriever(
        "postgresql://fake",
        connect=FakeConnect(connection),
        register=lambda connection: None,
    )

    result = retriever.search(
        query,
        candidate_k=3,
        knowledge_scope="after_sale_test",
    )

    assert result.hits[0].cosine_distance == pytest.approx(0.2)
    assert result.hits[0].cosine_similarity == pytest.approx(0.8)
    assert result.hits[0].source_spans[0].locator.heading_path == ("接口规则",)
    assert result.diagnostics.lower_is_better is True
    assert result.diagnostics.indexed_chunk_count == 4
    assert result.diagnostics.visible_chunk_count == 2
    assert result.diagnostics.search_mode is DenseSearchMode.EXACT
    assert connection.executions[0][1]["knowledge_scope"] == "after_sale_test"


@pytest.mark.integration
def test_real_pgvector_exact_dense_retrieval() -> None:
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("设置 TEST_DATABASE_URL 后运行真实 PostgreSQL 集成测试")

    with psycopg.connect(dsn) as connection:
        for migration in MIGRATIONS:
            connection.execute(migration.read_text(encoding="utf-8"))

    chunks = _chunks()[:2]
    records = (
        _record(chunks[0], [1.0, 0.0, 0.0]),
        _record(chunks[1], [0.0, 1.0, 0.0]),
    )
    query = EmbeddingRecord(
        text="query",
        vector=(0.99, 0.01, 0.0),
        model="test-embedding",
        dimensions=3,
        config_ref="embedding.test",
        provider="test_provider",
        text_id="query",
        preprocessing_version="chunk-text-v1",
    )
    chunk_store = PostgresChunkStore(dsn)
    vector_store = PostgresVectorStore(dsn)
    retriever = PostgresDenseRetriever(dsn)
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    try:
        chunk_store.upsert_chunks(chunks)
        index_report = vector_store.upsert_embeddings(chunks, records)
        vector_store.ensure_hnsw_index(index_report.embedding_space)
        result = retriever.search(
            query,
            candidate_k=2,
            knowledge_scope="after_sale_test",
            mode=DenseSearchMode.EXACT,
        )

        assert result.hits[0].chunk_id == chunks[0].chunk_id
        assert result.hits[0].cosine_distance < result.hits[1].cosine_distance
        assert result.diagnostics.indexed_chunk_count == 2
        assert result.diagnostics.visible_chunk_count == 2
    finally:
        chunk_store.delete_chunks(chunk_ids)
