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


QUERY = "申请售后"
ORDER_STATUS_CHUNK = "仅已支付且已完成的订单可申请售后。\n虚拟商品不进入售后流程。"
INTERFACE_CLIENT_CHUNK = (
    "售后接口 v2 必须提供 source_channel。\n"
    "Flutter 客户端必须使用相同的入口可见性规则。"
)


def _candidate(
    chunk_id: str,
    rank: int,
    *,
    eligibility: EvidenceEligibility = EvidenceEligibility.CURRENT_EVIDENCE,
    with_spans: bool = True,
    content: str | None = None,
) -> RRFCandidate:
    candidate_content = content or (
        ORDER_STATUS_CHUNK if rank == 1 else INTERFACE_CLIENT_CHUNK
    )
    spans = (
        (
            ChunkSourceSpan(
                element_id=f"element-{rank}",
                locator=SourceLocator(
                    kind="markdown",
                    line_start=5 if rank == 1 else 10,
                    line_end=6 if rank == 1 else 11,
                    heading_path=(
                        "售后入口与订单状态",
                        "当前订单状态规则"
                        if rank == 1
                        else "接口与客户端约束",
                    ),
                ),
                start_char=0,
                end_char=len(candidate_content),
                text=candidate_content,
            ),
        )
        if with_spans
        else ()
    )
    return RRFCandidate(
        chunk_id=chunk_id,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        content=candidate_content,
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
            query=QUERY,
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
    mapping = retrieval_result_to_context_sources(
        _result(_candidate("order-status", 1))
    )

    assert mapping.mapped_source_ids == ("order-status",)
    source = mapping.sources[0]
    assert source.source_id == "order-status"
    assert source.source_type == "evidence"
    assert source.score is None
    assert source.metadata["document_id"] == "KR-ORDER-STATE"
    assert "lines=5-6" in source.metadata["source_locators"]
    assert source.metadata["route_ranks"] == "lexical:1,dense:2"
    assert "postgresql_ts_rank" in source.metadata["native_scores"]
    assert mapping.decisions[0].status is ContextMappingStatus.MAPPED


def test_context_report_can_explain_retrieved_but_budget_dropped_source() -> None:
    retrieval = _result(
        _candidate("order-status", 1),
        _candidate("interface-client", 2),
    )
    mapped = retrieval_result_to_context_sources(retrieval)
    requirement = QUERY
    first_source_tokens = estimate_tokens(format_context_source(mapped.sources[0]))
    requirement_tokens = estimate_tokens(requirement)
    baseline = build_rag_review_context(
        requirement_text=requirement,
        retrieval_result=retrieval,
        policy=get_context_policy("full_context"),
    )
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

    assert baseline.mapping == result.mapping
    assert baseline.context.included_source_ids == [
        "order-status",
        "interface-client",
    ]
    assert result.mapping.mapped_source_ids == ("order-status", "interface-client")
    assert result.context.report is not None
    assert result.context.included_source_ids == ["order-status"]
    assert result.context.dropped_source_ids == ["interface-client"]
    assert result.context.dropped_sources[0].reason == "token_budget_exceeded"
    assert (
        result.context.report.citation_source_ids == result.context.included_source_ids
    )


def test_historical_context_is_not_a_citation_candidate() -> None:
    result = build_rag_review_context(
        requirement_text=QUERY,
        retrieval_result=_result(_candidate("order-status", 1)),
        additional_sources=(
            ContextSource(
                source_id="assumed-history",
                content="【确定性机制假设，不是当前资料事实】旧规则允许未完成订单申请售后。",
                source_type="history_review",
            ),
        ),
        policy=get_context_policy("full_context"),
    )

    assert result.context.report is not None
    assert "assumed-history" in result.context.included_source_ids
    assert "assumed-history" not in result.context.report.citation_source_ids
    assert "order-status" in result.context.report.citation_source_ids


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
            requirement_text=QUERY,
            retrieval_result=_result(_candidate("same-id", 1)),
            additional_sources=(
                ContextSource(source_id="same-id", content="unrelated history"),
            ),
            policy=get_context_policy("full_context"),
        )
