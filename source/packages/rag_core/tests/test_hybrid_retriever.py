from __future__ import annotations

from rag_core import (
    DenseDiagnostics,
    DenseHit,
    DenseSearchMode,
    DenseSearchResult,
    EmbeddingRecord,
    EvidenceEligibility,
    FixedHybridRetriever,
    HybridRetrieverConfig,
    LexicalDiagnostics,
    LexicalHit,
    LexicalSearchResult,
    NoResultReason,
    QueryOperator,
    RetrievalError,
    RetrievalErrorCode,
    RetrievalStage,
    SourceRole,
    ThresholdStatus,
)


QUERY = "申请售后"
SCOPE = "after_sale"
ROLES = (SourceRole.REFERENCE_KNOWLEDGE,)
ELIGIBILITIES = (EvidenceEligibility.CURRENT_EVIDENCE,)
ORDER_STATUS_CHUNK = "仅已支付且已完成的订单可申请售后。\n虚拟商品不进入售后流程。"
INTERFACE_CLIENT_CHUNK = (
    "售后接口 v2 必须提供 source_channel。\n"
    "Flutter 客户端必须使用相同的入口可见性规则。"
)
CHUNK_CONTENT = {
    "order-status": ORDER_STATUS_CHUNK,
    "interface-client": INTERFACE_CLIENT_CHUNK,
}


class FakeRetriever:
    def __init__(self, result=None, error: RetrievalError | None = None) -> None:
        self.result = result
        self.error = error
        self.calls = []

    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


def _embedding() -> EmbeddingRecord:
    return EmbeddingRecord(
        text=QUERY,
        vector=(0.1, 0.2, 0.3),
        model="test-embedding",
        dimensions=3,
        config_ref="embedding.test",
        provider="test-provider",
        text_id="surface_match",
    )


def _lexical_hit(chunk_id: str, rank: int, score: float) -> LexicalHit:
    return LexicalHit(
        chunk_id=chunk_id,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        content=CHUNK_CONTENT[chunk_id],
        source_role=ROLES[0],
        evidence_eligibility=ELIGIBILITIES[0],
        business_metadata={"knowledge_scope": SCOPE},
        matched_terms=("申请", "售后"),
        fts_rank=score,
        route_rank=rank,
    )


def _dense_hit(chunk_id: str, rank: int, distance: float) -> DenseHit:
    return DenseHit(
        chunk_id=chunk_id,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        content=CHUNK_CONTENT[chunk_id],
        source_role=ROLES[0],
        evidence_eligibility=ELIGIBILITIES[0],
        business_metadata={"knowledge_scope": SCOPE},
        cosine_distance=distance,
        cosine_similarity=1 - distance,
        route_rank=rank,
    )


def _lexical_result(*hits: LexicalHit, visible: int = 2) -> LexicalSearchResult:
    return LexicalSearchResult(
        hits=tuple(hits),
        diagnostics=LexicalDiagnostics(
            query=QUERY,
            normalized_query=QUERY,
            query_terms=("申请", "售后"),
            postgres_query_terms=("申请", "售后"),
            tsquery="'申请' | '售后'",
            query_operator=QueryOperator.OR,
            lexical_config_ref="lexical.test",
            retriever_config_ref="postgres_fts@test",
            postgres_config="simple",
            knowledge_scope=SCOPE,
            source_roles=ROLES,
            evidence_eligibilities=ELIGIBILITIES,
            indexed_chunk_count=2,
            visible_chunk_count=visible,
            matched_chunk_count=len(hits),
            returned_chunk_count=len(hits),
            candidate_k=2,
            rank_name="postgresql_ts_rank",
            higher_is_better=True,
            latency_ms=1.0,
        ),
    )


def _dense_result(*hits: DenseHit, visible: int = 2) -> DenseSearchResult:
    return DenseSearchResult(
        hits=tuple(hits),
        diagnostics=DenseDiagnostics(
            query=QUERY,
            embedding_space_ref="space@test",
            provider="test-provider",
            config_ref="embedding.test",
            model="test-embedding",
            dimensions=3,
            preprocessing_version="raw-v1",
            knowledge_scope=SCOPE,
            source_roles=ROLES,
            evidence_eligibilities=ELIGIBILITIES,
            indexed_chunk_count=2,
            visible_chunk_count=visible,
            returned_chunk_count=len(hits),
            candidate_k=2,
            distance_name="pgvector_cosine_distance",
            lower_is_better=True,
            search_mode=DenseSearchMode.EXACT,
            index_name=None,
            index_used=None,
            plan_node_types=(),
            latency_ms=2.0,
        ),
    )


def _config(**overrides) -> HybridRetrieverConfig:
    values = {
        "lexical_candidate_k": 2,
        "dense_candidate_k": 2,
        "lexical_min_rank": 0.2,
        "dense_max_distance": 0.3,
        "rrf_k": 60,
        "final_top_k": 1,
        "knowledge_scope": SCOPE,
        "source_roles": ROLES,
        "evidence_eligibilities": ELIGIBILITIES,
    }
    values.update(overrides)
    return HybridRetrieverConfig(**values)


def test_fixed_hybrid_retriever_exposes_each_control_stage() -> None:
    lexical = FakeRetriever(
        _lexical_result(
            _lexical_hit("order-status", 1, 0.82),
            _lexical_hit("interface-client", 2, 0.31),
        )
    )
    dense = FakeRetriever(
        _dense_result(
            _dense_hit("order-status", 1, 0.12),
            _dense_hit("interface-client", 2, 0.44),
        )
    )

    result = FixedHybridRetriever(lexical, dense).retrieve(
        QUERY,
        _embedding(),
        config=_config(),
    )

    assert result.report.control_order == (
        "pre_filter",
        "route_candidate_k",
        "route_threshold",
        "rrf",
        "final_top_k",
    )
    assert [item.chunk_id for item in result.candidates] == ["order-status"]
    assert result.report.route_reports["lexical"].candidate_count == 2
    assert result.report.route_reports["lexical"].passed_threshold_count == 2
    assert result.report.route_reports["dense"].dropped_threshold_count == 1
    assert result.report.fusion_diagnostics.distinct_candidate_count == 2
    assert result.report.final_selection[-1].reason == "dropped_by_final_top_k"
    assert result.report.no_result_reason is None

    lexical_query, lexical_options = lexical.calls[0]
    dense_query, dense_options = dense.calls[0]
    assert lexical_query == QUERY
    assert dense_query.text == QUERY
    for options in (lexical_options, dense_options):
        assert options["knowledge_scope"] == SCOPE
        assert options["source_roles"] == ROLES
        assert options["evidence_eligibilities"] == ELIGIBILITIES
    assert lexical_options["candidate_k"] == 2
    assert dense_options["candidate_k"] == 2


def test_all_candidates_below_route_threshold_has_structured_reason() -> None:
    lexical = FakeRetriever(
        _lexical_result(_lexical_hit("order-status", 1, 0.1))
    )
    dense = FakeRetriever(
        _dense_result(_dense_hit("interface-client", 1, 0.9))
    )

    result = FixedHybridRetriever(lexical, dense).retrieve(
        QUERY,
        _embedding(),
        config=_config(),
    )

    assert result.candidates == ()
    assert result.report.no_result_reason is NoResultReason.ALL_BELOW_THRESHOLD
    assert all(
        decision.status is ThresholdStatus.DROPPED
        for decision in result.report.threshold_decisions
    )


def test_empty_visible_scope_is_not_confused_with_no_route_match() -> None:
    lexical = FakeRetriever(_lexical_result(visible=0))
    dense = FakeRetriever(_dense_result(visible=0))

    result = FixedHybridRetriever(lexical, dense).retrieve(
        QUERY,
        _embedding(),
        config=_config(),
    )

    assert result.candidates == ()
    assert result.report.no_result_reason is NoResultReason.VISIBLE_SCOPE_EMPTY


def test_failed_route_remains_visible_instead_of_becoming_empty() -> None:
    lexical = FakeRetriever(
        error=RetrievalError(
            code=RetrievalErrorCode.CONNECTION_FAILED,
            stage=RetrievalStage.QUERY,
            message="database unavailable",
        )
    )
    dense = FakeRetriever(_dense_result())

    result = FixedHybridRetriever(lexical, dense).retrieve(
        QUERY,
        _embedding(),
        config=_config(),
    )

    assert result.report.partial_failure is True
    assert result.report.route_reports["lexical"].error_code == "connection_failed"
    assert result.report.no_result_reason is NoResultReason.ROUTE_FAILURE


def test_config_ref_changes_when_a_retrieval_control_changes() -> None:
    assert _config().config_ref != _config(final_top_k=2).config_ref


def test_final_top_k_only_changes_the_final_selection() -> None:
    lexical_result = _lexical_result(
        _lexical_hit("order-status", 1, 0.82),
        _lexical_hit("interface-client", 2, 0.31),
    )
    dense_result = _dense_result(
        _dense_hit("order-status", 1, 0.12),
        _dense_hit("interface-client", 2, 0.20),
    )

    top_one = FixedHybridRetriever(
        FakeRetriever(lexical_result), FakeRetriever(dense_result)
    ).retrieve(QUERY, _embedding(), config=_config(final_top_k=1))
    top_two = FixedHybridRetriever(
        FakeRetriever(lexical_result), FakeRetriever(dense_result)
    ).retrieve(QUERY, _embedding(), config=_config(final_top_k=2))

    assert top_one.report.route_reports == top_two.report.route_reports
    assert top_one.report.threshold_decisions == top_two.report.threshold_decisions
    assert top_one.report.fusion_diagnostics == top_two.report.fusion_diagnostics
    assert [item.chunk_id for item in top_one.candidates] == ["order-status"]
    assert [item.chunk_id for item in top_two.candidates] == [
        "order-status",
        "interface-client",
    ]
    assert top_one.report.final_selection[-1].reason == "dropped_by_final_top_k"
    assert all(item.selected for item in top_two.report.final_selection)
