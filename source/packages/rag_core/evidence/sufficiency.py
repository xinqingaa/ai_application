"""Turn verified Citation coverage into an answerability decision and gaps."""

from __future__ import annotations

import json
from collections.abc import Sequence

from pydantic import BaseModel

from llm_core import LLMClient, estimate_usage_cost
from llm_core.prompts import get_prompt, render_prompt
from llm_core.structured import StructuredMode
from rag_core.evidence.models import (
    EvidenceClaim,
    EvidenceCoverageCheck,
    EvidenceCoverageVerdict,
    EvidenceDecision,
    EvidenceDecisionKind,
    EvidenceGap,
    EvidenceRequirement,
    EvidenceScopeSource,
    EvidenceSufficiencyReport,
    EvidenceSufficiencyResult,
    EvidenceSufficiencyValidationStatus,
    VerifiedCitation,
)


class _CoverageJudgment(BaseModel):
    requirement_id: str
    verdict: EvidenceCoverageVerdict
    citation_claim_ids: list[str]
    reason: str


class _CoverageJudgmentList(BaseModel):
    judgments: list[_CoverageJudgment]


def decide_evidence_sufficiency(
    claims: Sequence[EvidenceClaim],
    verified_citations: Sequence[VerifiedCitation],
    requirements: Sequence[EvidenceRequirement],
    scope_sources: Sequence[EvidenceScopeSource],
    *,
    client: LLMClient | None = None,
    config_ref: str = "chat.structured_chat",
    prompt_version: str = "1.0.0",
    structured_mode: StructuredMode = "json_schema",
    temperature: float = 0,
    debug: bool = False,
) -> EvidenceSufficiencyResult:
    """Judge semantic coverage once, then aggregate it deterministically.

    The caller fixes the review claims, the required fact categories, and the
    active knowledge scope.  This function never retrieves more sources or
    turns an execution failure into a refusal.
    """

    claim_records = tuple(claims)
    requirement_records = tuple(requirements)
    source_records = tuple(scope_sources)
    citation_records = tuple(verified_citations)
    _validate_inputs(
        claim_records,
        citation_records,
        requirement_records,
        source_records,
    )
    prompt = get_prompt("review.evidence_sufficiency", version=prompt_version)
    sources_by_id = {source.source_id: source for source in source_records}
    citations_by_claim = _citations_by_claim(citation_records)
    claim_texts = {item.claim_id: item.claim_text for item in claim_records}

    deterministic_gaps: list[EvidenceCoverageCheck] = []
    model_requirements: list[EvidenceRequirement] = []
    for requirement in requirement_records:
        if _eligible_claim_ids(requirement, citations_by_claim, sources_by_id):
            model_requirements.append(requirement)
        else:
            deterministic_gaps.append(
                EvidenceCoverageCheck(
                    requirement_id=requirement.requirement_id,
                    verdict=EvidenceCoverageVerdict.GAP,
                    citation_claim_ids=(),
                    reason=(
                        "当前范围内没有来自预期来源角色的已验证 Citation，"
                        "不能把缺口当作强结论。"
                    ),
                )
            )

    if not model_requirements:
        return _completed_without_model(
            claim_records,
            requirement_records,
            source_records,
            citation_records,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            checks=tuple(deterministic_gaps),
        )

    messages = render_prompt(
        prompt,
        {
            "claims": json.dumps(
                [
                    {"claim_id": item.claim_id, "claim": item.claim_text}
                    for item in claim_records
                ],
                ensure_ascii=False,
                indent=2,
            ),
            "verified_citations": json.dumps(
                [
                    {
                        "claim_id": item.claim_id,
                        "source_id": item.source_id,
                        "excerpt": item.excerpt,
                        "locator": item.source_locator,
                        "support_reason": item.reason,
                    }
                    for item in citation_records
                ],
                ensure_ascii=False,
                indent=2,
            ),
            "coverage_requirements": json.dumps(
                [
                    {
                        "requirement_id": item.requirement_id,
                        "required_fact": item.required_fact,
                        "expected_source_role": item.expected_source_role,
                        "affected_claim_ids": list(item.affected_claim_ids),
                    }
                    for item in model_requirements
                ],
                ensure_ascii=False,
                indent=2,
            ),
            "active_sources": json.dumps(
                [
                    {
                        "source_id": item.source_id,
                        "source_role": item.source_role,
                        "source_locator": item.source_locator,
                        "content": item.content,
                    }
                    for item in source_records
                ],
                ensure_ascii=False,
                indent=2,
            ),
        },
    )
    llm = client or LLMClient.from_default_config()
    response = llm.chat_structured(
        messages,
        config_ref,
        response_model=_CoverageJudgmentList,
        schema_name="evidence_sufficiency_judgments",
        structured_mode=structured_mode,
        temperature=temperature,
        debug=debug,
    )
    if not response.parse.ok:
        return _failed_result(
            claim_records,
            requirement_records,
            source_records,
            citation_records,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            messages=messages,
            response=response,
            status=EvidenceSufficiencyValidationStatus.STRUCTURED_OUTPUT_INVALID,
            error_stage=response.parse.error_stage,
            error_message=response.parse.message,
        )

    value = response.parse.value
    if not isinstance(value, _CoverageJudgmentList):
        raise TypeError("Evidence sufficiency 结构化结果类型不匹配")
    model_checks = _validate_judgments(
        value.judgments,
        model_requirements,
        citations_by_claim,
        sources_by_id,
    )
    if model_checks is None:
        return _failed_result(
            claim_records,
            requirement_records,
            source_records,
            citation_records,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            messages=messages,
            response=response,
            status=EvidenceSufficiencyValidationStatus.JUDGMENT_SET_INVALID,
            error_stage="business",
            error_message="充分性判断必须按输入顺序返回合法的 requirement_id 与 Citation 关联。",
        )

    checks_by_id = {
        item.requirement_id: item for item in (*deterministic_gaps, *model_checks)
    }
    checks = tuple(checks_by_id[item.requirement_id] for item in requirement_records)
    decision = _decision(requirement_records, checks, claim_texts)
    return EvidenceSufficiencyResult(
        decision=decision,
        report=_report(
            claim_records,
            requirement_records,
            source_records,
            citation_records,
            checks,
            status=EvidenceSufficiencyValidationStatus.COMPLETED,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            model_call_count=1,
            response=response,
        ),
        messages=tuple(messages),
        response=response,
    )


def _validate_inputs(claims, citations, requirements, sources) -> None:
    if not claims:
        raise ValueError("至少需要一条 Claim")
    if not requirements:
        raise ValueError("至少需要一个覆盖要求")
    claim_ids = [item.claim_id.strip() for item in claims]
    requirement_ids = [item.requirement_id.strip() for item in requirements]
    source_ids = [item.source_id.strip() for item in sources]
    if any(not item.claim_text.strip() for item in claims):
        raise ValueError("Claim 文本不能为空")
    if len(set(claim_ids)) != len(claim_ids) or any(not item for item in claim_ids):
        raise ValueError("claim_id 必须唯一且非空")
    if len(set(requirement_ids)) != len(requirement_ids) or any(
        not item for item in requirement_ids
    ):
        raise ValueError("requirement_id 必须唯一且非空")
    if len(set(source_ids)) != len(source_ids) or any(not item for item in source_ids):
        raise ValueError("scope source_id 必须唯一且非空")
    claim_id_set = set(claim_ids)
    source_id_set = set(source_ids)
    for requirement in requirements:
        if (
            not requirement.required_fact.strip()
            or not requirement.expected_source_role.strip()
        ):
            raise ValueError("覆盖要求必须说明缺失事实与预期来源角色")
        if not requirement.affected_claim_ids or not set(
            requirement.affected_claim_ids
        ).issubset(claim_id_set):
            raise ValueError("覆盖要求必须关联已有 Claim")
    for citation in citations:
        if citation.claim_id not in claim_id_set:
            raise ValueError("VerifiedCitation 必须属于本次 Claim")
        if citation.source_id not in source_id_set:
            raise ValueError("VerifiedCitation 的来源必须仍在当前 knowledge scope")


def _citations_by_claim(citations):
    result: dict[str, tuple[VerifiedCitation, ...]] = {}
    for citation in citations:
        result[citation.claim_id] = (*result.get(citation.claim_id, ()), citation)
    return result


def _eligible_claim_ids(
    requirement, citations_by_claim, sources_by_id
) -> tuple[str, ...]:
    return tuple(
        claim_id
        for claim_id in requirement.affected_claim_ids
        if any(
            sources_by_id[citation.source_id].source_role
            == requirement.expected_source_role
            for citation in citations_by_claim.get(claim_id, ())
        )
    )


def _validate_judgments(judgments, requirements, citations_by_claim, sources_by_id):
    expected_ids = [item.requirement_id for item in requirements]
    actual_ids = [item.requirement_id for item in judgments]
    if actual_ids != expected_ids or len(set(actual_ids)) != len(actual_ids):
        return None
    result: list[EvidenceCoverageCheck] = []
    by_id = {item.requirement_id: item for item in requirements}
    for judgment in judgments:
        requirement = by_id[judgment.requirement_id]
        cited_ids = tuple(judgment.citation_claim_ids)
        if len(set(cited_ids)) != len(cited_ids):
            return None
        eligible_ids = set(
            _eligible_claim_ids(requirement, citations_by_claim, sources_by_id)
        )
        if judgment.verdict is EvidenceCoverageVerdict.COVERED:
            if not cited_ids or not set(cited_ids).issubset(eligible_ids):
                return None
        elif cited_ids:
            return None
        result.append(
            EvidenceCoverageCheck(
                requirement_id=judgment.requirement_id,
                verdict=judgment.verdict,
                citation_claim_ids=cited_ids,
                reason=judgment.reason,
            )
        )
    return tuple(result)


def _completed_without_model(
    claims,
    requirements,
    sources,
    citations,
    *,
    prompt_ref,
    config_ref,
    structured_mode,
    checks,
):
    return EvidenceSufficiencyResult(
        decision=_decision(
            requirements,
            checks,
            {item.claim_id: item.claim_text for item in claims},
        ),
        report=_report(
            claims,
            requirements,
            sources,
            citations,
            checks,
            status=EvidenceSufficiencyValidationStatus.COMPLETED,
            prompt_ref=prompt_ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            model_call_count=0,
            response=None,
        ),
        messages=(),
        response=None,
    )


def _failed_result(
    claims,
    requirements,
    sources,
    citations,
    *,
    prompt_ref,
    config_ref,
    structured_mode,
    messages,
    response,
    status,
    error_stage,
    error_message,
):
    empty_checks: tuple[EvidenceCoverageCheck, ...] = ()
    return EvidenceSufficiencyResult(
        decision=None,
        report=_report(
            claims,
            requirements,
            sources,
            citations,
            empty_checks,
            status=status,
            prompt_ref=prompt_ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            model_call_count=1,
            response=response,
            error_stage=error_stage,
            error_message=error_message,
        ),
        messages=tuple(messages),
        response=response,
    )


def _decision(requirements, checks, claim_texts) -> EvidenceDecision:
    checks_by_id = {item.requirement_id: item for item in checks}
    gaps = tuple(
        _gap(requirement, checks_by_id[requirement.requirement_id], claim_texts)
        for requirement in requirements
        if checks_by_id[requirement.requirement_id].verdict
        is EvidenceCoverageVerdict.GAP
    )
    covered_count = len(requirements) - len(gaps)
    kind = (
        EvidenceDecisionKind.ANSWERABLE
        if not gaps
        else EvidenceDecisionKind.PARTIAL
        if covered_count
        else EvidenceDecisionKind.REFUSAL
    )
    return EvidenceDecision(kind=kind, coverage=tuple(checks), gaps=gaps)


def _gap(requirement, check, claim_texts) -> EvidenceGap:
    affected_claim_text = "；".join(
        claim_texts[claim_id].rstrip("。.!！？?")
        for claim_id in requirement.affected_claim_ids
    )
    return EvidenceGap(
        requirement_id=requirement.requirement_id,
        missing_fact=requirement.required_fact,
        expected_source_role=requirement.expected_source_role,
        affected_claim_ids=requirement.affected_claim_ids,
        reason=check.reason,
        question=(
            f"请补充来自“{requirement.expected_source_role}”的"
            f"{requirement.required_fact}，以判断：{affected_claim_text}。"
        ),
    )


def _report(
    claims,
    requirements,
    sources,
    citations,
    checks,
    *,
    status,
    prompt_ref,
    config_ref,
    structured_mode,
    model_call_count,
    response,
    error_stage=None,
    error_message=None,
):
    usage = response.llm.usage if response is not None else None
    cost = (
        estimate_usage_cost(usage, config_ref=config_ref, model=response.llm.model)
        if response is not None
        else None
    )
    return EvidenceSufficiencyReport(
        status=status,
        prompt_ref=prompt_ref,
        config_ref=config_ref,
        structured_mode=structured_mode,
        claim_count=len(claims),
        requirement_count=len(requirements),
        active_source_count=len(sources),
        verified_citation_count=len(citations),
        covered_count=sum(
            item.verdict is EvidenceCoverageVerdict.COVERED for item in checks
        ),
        gap_count=sum(item.verdict is EvidenceCoverageVerdict.GAP for item in checks),
        model_call_count=model_call_count,
        usage=usage,
        cost=cost,
        latency_ms=response.llm.latency_ms if response is not None else None,
        parse_error_stage=error_stage,
        parse_error_message=error_message,
    )
