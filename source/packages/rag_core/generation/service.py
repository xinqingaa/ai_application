"""First-stage structured generation with Citation Candidate membership checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from llm_core import (
    BuiltContext,
    LLMClient,
    QuotedReviewRiskList,
    ReviewRisk,
    ReviewRiskList,
)
from llm_core.prompts import get_prompt, render_prompt
from llm_core.structured import StructuredLLMResponse, StructuredMode


class GenerationStatus(str, Enum):
    SUCCEEDED = "succeeded"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    UNKNOWN_CITATION_SOURCE = "unknown_citation_source"


class EvidenceState(str, Enum):
    AVAILABLE = "available"
    NO_CITATION_CANDIDATES = "no_citation_candidates"


class CitationClaimStatus(str, Enum):
    CANDIDATE = "candidate"
    UNKNOWN_SOURCE = "unknown_source"


@dataclass(frozen=True)
class CitationClaimCheck:
    risk_index: int
    risk_title: str
    citation_index: int
    source_id: str
    status: CitationClaimStatus


@dataclass(frozen=True)
class TrustedGenerationReport:
    prompt_ref: str
    config_ref: str
    structured_mode: StructuredMode
    citation_boundary: str
    citation_candidate_ids: tuple[str, ...]
    evidence_state: EvidenceState
    parse_ok: bool
    parse_error_stage: str | None
    parse_error_message: str | None
    risk_count: int
    risk_without_citation_count: int
    claimed_citation_count: int
    candidate_claim_count: int
    unknown_source_count: int
    claim_checks: tuple[CitationClaimCheck, ...]


@dataclass(frozen=True)
class TrustedGenerationResult:
    status: GenerationStatus
    risks: tuple[ReviewRisk, ...]
    messages: tuple[dict[str, str], ...]
    response: StructuredLLMResponse
    report: TrustedGenerationReport


def generate_trusted_review(
    context: BuiltContext,
    *,
    client: LLMClient | None = None,
    config_ref: str = "chat.structured_chat",
    prompt_version: str = "5.0.0",
    require_citation_excerpts: bool = False,
    structured_mode: StructuredMode = "json_schema",
    temperature: float = 0,
    debug: bool = False,
) -> TrustedGenerationResult:
    """Generate risks and check only whether claimed source IDs were candidates."""

    if context.report is None:
        raise ValueError("BuiltContext 必须携带 ContextBuildReport")
    citation_ids = tuple(context.report.citation_source_ids)
    prompt = get_prompt("review.risk_review", version=prompt_version)
    variables = context.to_prompt_variables()
    variables["citation_candidate_ids"] = (
        "\n".join(f"- {source_id}" for source_id in citation_ids)
        if citation_ids
        else "（无）"
    )
    messages = render_prompt(prompt, variables)
    llm = client or LLMClient.from_default_config()
    response_model = (
        QuotedReviewRiskList if require_citation_excerpts else ReviewRiskList
    )
    response = llm.chat_structured(
        messages,
        config_ref,
        response_model=response_model,
        structured_mode=structured_mode,
        temperature=temperature,
        debug=debug,
    )
    risks = tuple(response.parse.risks or ()) if response.parse.ok else ()
    checks = _check_claims(risks, set(citation_ids))
    unknown_count = sum(
        item.status is CitationClaimStatus.UNKNOWN_SOURCE for item in checks
    )
    status = _generation_status(response.parse.ok, unknown_count)
    report = TrustedGenerationReport(
        prompt_ref=prompt.ref,
        config_ref=config_ref,
        structured_mode=structured_mode,
        citation_boundary="candidate_membership_only_not_support_validation",
        citation_candidate_ids=citation_ids,
        evidence_state=(
            EvidenceState.AVAILABLE
            if citation_ids
            else EvidenceState.NO_CITATION_CANDIDATES
        ),
        parse_ok=response.parse.ok,
        parse_error_stage=response.parse.error_stage,
        parse_error_message=response.parse.message,
        risk_count=len(risks),
        risk_without_citation_count=sum(not risk.citations for risk in risks),
        claimed_citation_count=len(checks),
        candidate_claim_count=len(checks) - unknown_count,
        unknown_source_count=unknown_count,
        claim_checks=checks,
    )
    return TrustedGenerationResult(
        status=status,
        risks=risks,
        messages=tuple(messages),
        response=response,
        report=report,
    )


def _check_claims(
    risks: tuple[ReviewRisk, ...],
    citation_ids: set[str],
) -> tuple[CitationClaimCheck, ...]:
    checks: list[CitationClaimCheck] = []
    for risk_index, risk in enumerate(risks, 1):
        for citation_index, citation in enumerate(risk.citations, 1):
            checks.append(
                CitationClaimCheck(
                    risk_index=risk_index,
                    risk_title=risk.title,
                    citation_index=citation_index,
                    source_id=citation.source_id,
                    status=(
                        CitationClaimStatus.CANDIDATE
                        if citation.source_id in citation_ids
                        else CitationClaimStatus.UNKNOWN_SOURCE
                    ),
                )
            )
    return tuple(checks)


def _generation_status(parse_ok: bool, unknown_count: int) -> GenerationStatus:
    if not parse_ok:
        return GenerationStatus.STRUCTURED_OUTPUT_INVALID
    if unknown_count:
        return GenerationStatus.UNKNOWN_CITATION_SOURCE
    return GenerationStatus.SUCCEEDED
