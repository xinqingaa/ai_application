from __future__ import annotations

import pytest

from llm_core import (
    ContextBuildPolicy,
    ContextSource,
    estimate_tokens,
    format_context_source,
    get_context_policy,
)
from rag_core import (
    ChunkSourceSpan,
    ContextMappingStatus,
    EvidenceEligibility,
    RRFContribution,
    RRFCandidate,
    RRFDiagnostics,
    RetrievalReport,
    RetrievalResult,
    SourceLocator,
    SourceRole,
    build_rag_review_context,
    retrieval_result_to_context_sources,
)


def _candidate(
    chunk_id: str,
    rank: int,
    *,
    eligibility: EvidenceEligibility = EvidenceEligibility.CURRENT_EVIDENCE,
    with_spans: bool = True,
) -> RRFCandidate:
    spans = (
        (
            ChunkSourceSpan(
                element_id=f"element-{rank}",
                locator=SourceLocator(
                    kind="markdown",
                    line_start=rank * 10,
                    line_end=rank * 10 + 2,
                    heading_path=("售后规则",),
                ),
                start_char=0,
                end_char=12,
                text="售后接口字段说明",
            ),
        )
        if with_spans
        else ()
    )
    return RRFCandidate(
        chunk_id=chunk_id,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        content=f"rule content for {chunk_id}",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=eligibility,
        business_metadata={"knowledge_scope": "after_sale"},
        contributions=(
            RRFContribution(
                route_name="lexical",
                route_rank=rank,
                reciprocal_rank=1 / (60 + rank),
                native_score_name="postgresql_ts_rank",
                native_score=0.8 / rank,
                higher_is_better=True,
            ),
            RRFContribution(
                route_name="dense",
                route_rank=rank + 1,
                reciprocal_rank=1 / (61 + rank),
                native_score_name="pgvector_cosine_distance",
                native_score=0.1 * rank,
                higher_is_better=False,
            ),
        ),
        rrf_score=0.03 / rank,
        fusion_rank=rank,
        source_spans=spans,
    )


def _result(*candidates: RRFCandidate) -> RetrievalResult:
    return RetrievalResult(
        candidates=tuple(candidates),
        report=RetrievalReport(
            query="售后接口需要什么字段？",
            retriever_config_ref="fixed-hybrid-retriever@test",
            control_order=(
                "pre_filter",
                "route_candidate_k",
                "route_threshold",
                "rrf",
                "final_top_k",
            ),
            route_reports={},
            threshold_decisions=(),
            fusion_diagnostics=RRFDiagnostics(
                rrf_k=60,
                fusion_config_ref="rrf@test",
                route_statuses={},
                route_candidate_counts={},
                distinct_candidate_count=len(candidates),
                overlap_candidate_count=len(candidates),
                failed_routes=(),
            ),
            final_selection=(),
            no_result_reason=None,
            partial_failure=False,
            latency_ms=3.0,
        ),
    )


def test_retrieval_mapping_preserves_identity_locator_and_route_diagnostics() -> None:
    mapping = retrieval_result_to_context_sources(_result(_candidate("chunk-api", 1)))

    assert mapping.mapped_source_ids == ("chunk-api",)
    source = mapping.sources[0]
    assert source.source_id == "chunk-api"
    assert source.source_type == "evidence"
    assert source.score is None
    assert source.metadata["document_id"] == "KR-ORDER-STATE"
    assert "lines=10-12" in source.metadata["source_locators"]
    assert source.metadata["route_ranks"] == "lexical:1,dense:2"
    assert "postgresql_ts_rank" in source.metadata["native_scores"]
    assert mapping.decisions[0].status is ContextMappingStatus.MAPPED


def test_context_report_can_explain_retrieved_but_budget_dropped_source() -> None:
    retrieval = _result(
        _candidate("chunk-first", 1),
        _candidate("chunk-second", 2),
    )
    mapped = retrieval_result_to_context_sources(retrieval)
    requirement = "订单详情页新增申请售后入口。"
    first_source_tokens = estimate_tokens(format_context_source(mapped.sources[0]))
    requirement_tokens = estimate_tokens(requirement)
    policy = ContextBuildPolicy(
        name="one_retrieved_source_only",
        token_budget=requirement_tokens + first_source_tokens + 1,
        section_budgets={
            "requirement": requirement_tokens + 1,
            "evidence": first_source_tokens + 1,
            "history": 0,
            "agent_summary": 0,
            "other": 0,
        },
        allow_compression=False,
        max_source_tokens=None,
    )
    result = build_rag_review_context(
        requirement_text=requirement,
        retrieval_result=retrieval,
        policy=policy,
    )

    assert result.mapping.mapped_source_ids == ("chunk-first", "chunk-second")
    assert result.context.report is not None
    assert result.context.included_source_ids == ["chunk-first"]
    assert result.context.dropped_source_ids == ["chunk-second"]
    assert result.context.dropped_sources[0].reason == "token_budget_exceeded"
    assert (
        result.context.report.citation_source_ids == result.context.included_source_ids
    )


def test_historical_context_is_not_a_citation_candidate() -> None:
    result = build_rag_review_context(
        requirement_text="订单详情页新增申请售后入口。",
        retrieval_result=_result(_candidate("chunk-current", 1)),
        additional_sources=(
            ContextSource(
                source_id="history-1",
                content="旧评审曾发现重复提交。",
                source_type="history_review",
            ),
        ),
        policy=get_context_policy("full_context"),
    )

    assert result.context.report is not None
    assert "history-1" in result.context.included_source_ids
    assert "history-1" not in result.context.report.citation_source_ids
    assert "chunk-current" in result.context.report.citation_source_ids


def test_ineligible_retrieval_candidate_is_explicitly_excluded() -> None:
    mapping = retrieval_result_to_context_sources(
        _result(
            _candidate(
                "chunk-ineligible",
                1,
                eligibility=EvidenceEligibility.INELIGIBLE,
            )
        )
    )

    assert mapping.sources == ()
    assert mapping.decisions[0].status is ContextMappingStatus.EXCLUDED
    assert mapping.decisions[0].reason == "excluded_ineligible_source"


def test_candidate_without_source_span_cannot_enter_traceable_context() -> None:
    with pytest.raises(ValueError, match="缺少 source_spans"):
        retrieval_result_to_context_sources(
            _result(_candidate("chunk-without-locator", 1, with_spans=False))
        )


def test_additional_source_cannot_shadow_retrieved_chunk_id() -> None:
    with pytest.raises(ValueError, match="source_id 冲突"):
        build_rag_review_context(
            requirement_text="订单详情页新增申请售后入口。",
            retrieval_result=_result(_candidate("same-id", 1)),
            additional_sources=(
                ContextSource(source_id="same-id", content="unrelated history"),
            ),
            policy=get_context_policy("full_context"),
        )
