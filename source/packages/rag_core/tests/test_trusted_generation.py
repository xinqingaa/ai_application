from __future__ import annotations

import json

import pytest

from llm_core import (
    BuiltContext,
    ContextSource,
    LLMResponse,
    build_review_context,
    get_context_policy,
    parse_risk_list,
)
from llm_core.structured import StructuredLLMResponse
from rag_core import (
    CitationClaimStatus,
    EvidenceState,
    GenerationStatus,
    generate_trusted_review,
)


class FakeStructuredClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = []

    def chat_structured(self, messages, config_ref, **kwargs):
        self.calls.append((messages, config_ref, kwargs))
        return StructuredLLMResponse(
            llm=LLMResponse(
                content=self.content,
                raw_response={},
                usage=None,
                latency_ms=12.0,
                provider="fake-provider",
                model="fake-model",
                config_ref=config_ref,
            ),
            parse=parse_risk_list(self.content),
            structured_mode=kwargs["structured_mode"],
            request_params=kwargs,
        )


def _context(*, with_evidence: bool = True) -> BuiltContext:
    sources = (
        [
            ContextSource(
                source_id="chunk-api",
                content="售后接口 v2 必须提供 source_channel。",
                source_type="evidence",
                title="售后接口规则",
            )
        ]
        if with_evidence
        else []
    )
    return build_review_context(
        requirement_text="订单详情页新增申请售后入口。",
        sources=sources,
        policy=get_context_policy("evidence_first"),
    )


def _risk_json(*, source_id: str | None) -> str:
    citations = [] if source_id is None else [{"source_id": source_id}]
    return json.dumps(
        {
            "risks": [
                {
                    "title": "接口字段缺失",
                    "category": "api",
                    "level": "high",
                    "rationale": "需求没有明确传递 source_channel。",
                    "citations": citations,
                }
            ]
        },
        ensure_ascii=False,
    )


def test_known_claim_is_checked_against_this_context_candidates() -> None:
    client = FakeStructuredClient(_risk_json(source_id="chunk-api"))

    result = generate_trusted_review(_context(), client=client)  # type: ignore[arg-type]

    assert result.status is GenerationStatus.SUCCEEDED
    assert result.report.citation_candidate_ids == ("chunk-api",)
    assert result.report.evidence_state is EvidenceState.AVAILABLE
    assert result.report.candidate_claim_count == 1
    assert result.report.unknown_source_count == 0
    assert result.report.claim_checks[0].status is CitationClaimStatus.CANDIDATE
    assert result.report.citation_boundary == (
        "candidate_membership_only_not_support_validation"
    )
    rendered = "\n".join(message["content"] for message in client.calls[0][0])
    assert "Allowed Citation Source IDs" in rendered
    assert "- chunk-api" in rendered


def test_unknown_source_id_makes_generation_result_non_success() -> None:
    client = FakeStructuredClient(_risk_json(source_id="invented-source"))

    result = generate_trusted_review(_context(), client=client)  # type: ignore[arg-type]

    assert result.status is GenerationStatus.UNKNOWN_CITATION_SOURCE
    assert result.report.unknown_source_count == 1
    assert result.report.claim_checks[0].status is CitationClaimStatus.UNKNOWN_SOURCE


def test_risk_without_citation_remains_visible_but_is_not_unknown_source() -> None:
    client = FakeStructuredClient(_risk_json(source_id=None))

    result = generate_trusted_review(_context(), client=client)  # type: ignore[arg-type]

    assert result.status is GenerationStatus.SUCCEEDED
    assert result.report.risk_without_citation_count == 1
    assert result.report.claimed_citation_count == 0
    assert result.report.unknown_source_count == 0


def test_no_evidence_still_calls_real_generation_boundary_with_empty_allowlist() -> (
    None
):
    client = FakeStructuredClient(_risk_json(source_id=None))

    result = generate_trusted_review(
        _context(with_evidence=False),
        client=client,  # type: ignore[arg-type]
        structured_mode="json_object",
    )

    assert result.report.evidence_state is EvidenceState.NO_CITATION_CANDIDATES
    assert result.report.citation_candidate_ids == ()
    rendered = "\n".join(message["content"] for message in client.calls[0][0])
    assert "Allowed Citation Source IDs" in rendered
    assert "（无）" in rendered


def test_invalid_structured_output_keeps_parse_failure_visible() -> None:
    client = FakeStructuredClient("not json")

    result = generate_trusted_review(_context(), client=client)  # type: ignore[arg-type]

    assert result.status is GenerationStatus.STRUCTURED_OUTPUT_INVALID
    assert result.risks == ()
    assert result.report.parse_ok is False
    assert result.report.parse_error_stage == "json"


def test_context_without_build_report_is_rejected() -> None:
    context = BuiltContext(
        requirement_text="requirement",
        evidence_block="evidence",
        included_sources=[],
        dropped_sources=[],
        estimated_tokens=1,
        token_budget=10,
    )

    with pytest.raises(ValueError, match="ContextBuildReport"):
        generate_trusted_review(context, client=FakeStructuredClient("{}"))  # type: ignore[arg-type]
