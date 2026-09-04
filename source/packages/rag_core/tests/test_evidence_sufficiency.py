from __future__ import annotations

import json

from llm_core import LLMResponse
from llm_core.config import TokenUsage
from llm_core.schemas.parse import parse_structured_model
from llm_core.structured import StructuredLLMResponse
from rag_core import (
    EvidenceClaim,
    EvidenceDecisionKind,
    EvidenceRequirement,
    EvidenceScopeSource,
    EvidenceSufficiencyValidationStatus,
    CitationSupportVerdict,
    VerifiedCitation,
    decide_evidence_sufficiency,
)


class FakeSufficiencyClient:
    def __init__(self, payload: dict | str) -> None:
        self.payload = payload
        self.calls = []

    def chat_structured(self, messages, config_ref, *, response_model, **kwargs):
        self.calls.append((messages, config_ref, response_model, kwargs))
        content = (
            self.payload
            if isinstance(self.payload, str)
            else json.dumps(self.payload, ensure_ascii=False)
        )
        return StructuredLLMResponse(
            llm=LLMResponse(
                content=content,
                raw_response={},
                usage=TokenUsage(
                    prompt_tokens=100,
                    completion_tokens=20,
                    total_tokens=120,
                ),
                latency_ms=12.0,
                provider="fake-provider",
                model="fake-model",
                config_ref=config_ref,
            ),
            parse=parse_structured_model(content, response_model),
            structured_mode=kwargs["structured_mode"],
            request_params=kwargs,
        )


CLAIMS = (
    EvidenceClaim(
        claim_id="source-channel",
        claim_text="现行售后接口 v2 的所有请求都必须提供 source_channel。",
    ),
    EvidenceClaim(
        claim_id="error-presentation",
        claim_text="网络错误和业务拒绝必须向用户作不同说明。",
    ),
)

REQUIREMENTS = (
    EvidenceRequirement(
        requirement_id="interface-rule",
        required_fact="现行接口对 source_channel 的适用范围",
        expected_source_role="接口规则",
        affected_claim_ids=("source-channel",),
    ),
    EvidenceRequirement(
        requirement_id="error-contract",
        required_fact="网络错误与业务拒绝的展示差异",
        expected_source_role="错误契约",
        affected_claim_ids=("error-presentation",),
    ),
)


def _sources(*source_ids: str) -> tuple[EvidenceScopeSource, ...]:
    records = {
        "api": EvidenceScopeSource(
            source_id="api",
            source_role="接口规则",
            content="现行售后接口 v2 的全部请求必须提供 source_channel。",
            source_locator="api.md#v2",
        ),
        "errors": EvidenceScopeSource(
            source_id="errors",
            source_role="错误契约",
            content="网络错误提示可重试；业务拒绝展示拒绝原因。",
            source_locator="errors.md#display",
        ),
    }
    return tuple(records[item] for item in source_ids)


def _citation(claim_id: str, source_id: str) -> VerifiedCitation:
    return VerifiedCitation(
        claim_id=claim_id,
        claim_text=next(
            item.claim_text for item in CLAIMS if item.claim_id == claim_id
        ),
        source_id=source_id,
        excerpt="固定的已验证引文。",
        source_locator=f"{source_id}.md",
        char_start=0,
        char_end=8,
        verdict=CitationSupportVerdict.SUPPORTED,
        reason="上游支持性校验已确认。",
    )


def test_covered_and_gap_are_aggregated_as_partial_with_rendered_question():
    client = FakeSufficiencyClient(
        {
            "judgments": [
                {
                    "requirement_id": "interface-rule",
                    "verdict": "covered",
                    "citation_claim_ids": ["source-channel"],
                    "reason": "现行接口规则直接覆盖全部请求。",
                },
                {
                    "requirement_id": "error-contract",
                    "verdict": "gap",
                    "citation_claim_ids": [],
                    "reason": "现有引用没有说明展示差异。",
                },
            ]
        }
    )
    result = decide_evidence_sufficiency(
        CLAIMS,
        (_citation("source-channel", "api"), _citation("error-presentation", "errors")),
        REQUIREMENTS,
        _sources("api", "errors"),
        client=client,  # type: ignore[arg-type]
    )

    assert result.report.status is EvidenceSufficiencyValidationStatus.COMPLETED
    assert result.report.model_call_count == 1
    assert result.decision is not None
    assert result.decision.kind is EvidenceDecisionKind.PARTIAL
    assert [gap.requirement_id for gap in result.decision.gaps] == ["error-contract"]
    assert "错误契约" in result.decision.gaps[0].question


def test_absent_eligible_citations_become_refusal_without_model_call():
    client = FakeSufficiencyClient({"judgments": []})
    result = decide_evidence_sufficiency(
        CLAIMS,
        (),
        REQUIREMENTS,
        (),
        client=client,  # type: ignore[arg-type]
    )

    assert result.report.status is EvidenceSufficiencyValidationStatus.COMPLETED
    assert result.report.model_call_count == 0
    assert client.calls == []
    assert result.decision is not None
    assert result.decision.kind is EvidenceDecisionKind.REFUSAL
    assert len(result.decision.gaps) == 2


def test_invalid_citation_claim_mapping_is_not_converted_to_refusal():
    client = FakeSufficiencyClient(
        {
            "judgments": [
                {
                    "requirement_id": "interface-rule",
                    "verdict": "covered",
                    "citation_claim_ids": ["error-presentation"],
                    "reason": "错误的 Claim 映射。",
                },
                {
                    "requirement_id": "error-contract",
                    "verdict": "covered",
                    "citation_claim_ids": ["error-presentation"],
                    "reason": "错误的 Claim 映射。",
                },
            ]
        }
    )
    result = decide_evidence_sufficiency(
        CLAIMS,
        (_citation("source-channel", "api"), _citation("error-presentation", "errors")),
        REQUIREMENTS,
        _sources("api", "errors"),
        client=client,  # type: ignore[arg-type]
    )

    assert result.decision is None
    assert (
        result.report.status is EvidenceSufficiencyValidationStatus.JUDGMENT_SET_INVALID
    )


def test_structured_failure_is_not_converted_to_refusal():
    client = FakeSufficiencyClient("not json")
    result = decide_evidence_sufficiency(
        CLAIMS,
        (_citation("source-channel", "api"), _citation("error-presentation", "errors")),
        REQUIREMENTS,
        _sources("api", "errors"),
        client=client,  # type: ignore[arg-type]
    )

    assert result.decision is None
    assert (
        result.report.status
        is EvidenceSufficiencyValidationStatus.STRUCTURED_OUTPUT_INVALID
    )
