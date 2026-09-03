"""Locate claimed quotes deterministically, then judge semantic support once."""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Sequence
from dataclasses import replace

from pydantic import BaseModel

from llm_core import (
    BuiltContext,
    ContextSource,
    LLMClient,
    ReviewRisk,
    estimate_usage_cost,
)
from llm_core.prompts import get_prompt, render_prompt
from llm_core.structured import StructuredMode
from rag_core.evidence.models import (
    CitationSupportCheck,
    CitationSupportInput,
    CitationSupportReport,
    CitationSupportResult,
    CitationSupportValidationStatus,
    CitationSupportVerdict,
    QuoteLocationStatus,
    VerifiedCitation,
)
from rag_core.generation import CitationClaimStatus, TrustedGenerationResult


class _SupportJudgment(BaseModel):
    claim_id: str
    verdict: CitationSupportVerdict
    reason: str


class _SupportJudgmentList(BaseModel):
    judgments: list[_SupportJudgment]


def citation_support_inputs_from_generation(
    generation: TrustedGenerationResult,
) -> tuple[CitationSupportInput, ...]:
    """Adapt candidate claims from section 16 without accepting unknown sources."""

    candidate_positions = {
        (check.risk_index, check.citation_index)
        for check in generation.report.claim_checks
        if check.status is CitationClaimStatus.CANDIDATE
    }
    inputs: list[CitationSupportInput] = []
    for risk_index, risk in enumerate(generation.risks, 1):
        for citation_index, citation in enumerate(risk.citations, 1):
            if (risk_index, citation_index) not in candidate_positions:
                continue
            inputs.append(
                CitationSupportInput(
                    claim_id=f"risk-{risk_index}.citation-{citation_index}",
                    claim_text=_claim_text(risk),
                    source_id=citation.source_id,
                    excerpt=citation.excerpt or "",
                )
            )
    return tuple(inputs)


def validate_citation_support(
    context: BuiltContext,
    inputs: Sequence[CitationSupportInput],
    *,
    source_contents: Sequence[ContextSource] | None = None,
    client: LLMClient | None = None,
    config_ref: str = "chat.structured_chat",
    prompt_version: str = "1.0.0",
    structured_mode: StructuredMode = "json_schema",
    temperature: float = 0,
    debug: bool = False,
) -> CitationSupportResult:
    """Validate quote location first and semantic support only for located quotes."""

    normalized_inputs = tuple(inputs)
    _validate_input_ids(normalized_inputs)
    if context.report is None:
        raise ValueError("BuiltContext 必须携带 ContextBuildReport")

    allowed_ids = set(context.report.citation_source_ids)
    source_records = (
        tuple(source_contents)
        if source_contents is not None
        else tuple(context.included_sources)
    )
    sources = {source.source_id: source for source in source_records}
    if len(sources) != len(source_records):
        raise ValueError("source_contents 中的 source_id 必须唯一")
    checks = tuple(
        _locate_input(item, sources=sources, allowed_ids=allowed_ids)
        for item in normalized_inputs
    )
    located = tuple(
        check
        for check in checks
        if check.location_status is QuoteLocationStatus.LOCATED
    )
    prompt = get_prompt("review.citation_support", version=prompt_version)

    if not located:
        return _result_without_model(
            checks,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
        )

    support_items = [
        {
            "claim_id": check.claim_id,
            "claim": check.claim_text,
            "source_id": check.source_id,
            "quoted_excerpt": check.excerpt,
            "source_content": sources[check.source_id].content,
            "source_metadata": sources[check.source_id].metadata,
        }
        for check in located
    ]
    messages = render_prompt(
        prompt,
        {"support_items": json.dumps(support_items, ensure_ascii=False, indent=2)},
    )
    llm = client or LLMClient.from_default_config()
    response = llm.chat_structured(
        messages,
        config_ref,
        response_model=_SupportJudgmentList,
        schema_name="citation_support_judgments",
        structured_mode=structured_mode,
        temperature=temperature,
        debug=debug,
    )
    if not response.parse.ok:
        return _result_with_failed_judgment(
            checks,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            messages=messages,
            response=response,
            status=CitationSupportValidationStatus.STRUCTURED_OUTPUT_INVALID,
            error_stage=response.parse.error_stage,
            error_message=response.parse.message,
        )

    value = response.parse.value
    if not isinstance(value, _SupportJudgmentList):
        raise TypeError("Citation support 结构化结果类型不匹配")
    judgments = value.judgments
    expected_ids = [check.claim_id for check in located]
    actual_ids = [judgment.claim_id for judgment in judgments]
    if actual_ids != expected_ids or len(set(actual_ids)) != len(actual_ids):
        return _result_with_failed_judgment(
            checks,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            messages=messages,
            response=response,
            status=CitationSupportValidationStatus.JUDGMENT_SET_INVALID,
            error_stage="business",
            error_message=(
                "支持性判断必须按输入顺序返回全部 claim_id："
                f"expected={expected_ids}, actual={actual_ids}"
            ),
        )

    by_id = {judgment.claim_id: judgment for judgment in judgments}
    completed_checks = tuple(
        replace(
            check,
            verdict=by_id[check.claim_id].verdict,
            reason=by_id[check.claim_id].reason,
        )
        if check.claim_id in by_id
        else check
        for check in checks
    )
    verified = tuple(_verified(check) for check in completed_checks if _is_supported(check))
    return CitationSupportResult(
        checks=completed_checks,
        verified_citations=verified,
        report=_report(
            completed_checks,
            status=CitationSupportValidationStatus.COMPLETED,
            prompt_ref=prompt.ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            model_call_count=1,
            response=response,
        ),
        messages=tuple(messages),
        response=response,
    )


def _claim_text(risk: ReviewRisk) -> str:
    return risk.rationale.strip()


def _validate_input_ids(inputs: tuple[CitationSupportInput, ...]) -> None:
    ids = [item.claim_id.strip() for item in inputs]
    if any(not value for value in ids):
        raise ValueError("claim_id 不能为空")
    if len(set(ids)) != len(ids):
        raise ValueError("claim_id 必须唯一")


def _locate_input(item, *, sources, allowed_ids) -> CitationSupportCheck:
    claim_id = item.claim_id.strip()
    claim_text = item.claim_text.strip()
    source_id = item.source_id.strip()
    excerpt = item.excerpt.strip()
    if not claim_text:
        raise ValueError(f"{claim_id} 的 claim_text 不能为空")
    if source_id not in allowed_ids or source_id not in sources:
        return _base_check(
            item,
            location_status=QuoteLocationStatus.SOURCE_NOT_ALLOWED,
        )
    if not excerpt:
        return _base_check(
            item,
            location_status=QuoteLocationStatus.MISSING_EXCERPT,
        )

    source = sources[source_id]
    matches = _normalized_matches(source.content, excerpt)
    if not matches:
        return _base_check(
            item,
            location_status=QuoteLocationStatus.QUOTE_NOT_FOUND,
        )
    if len(matches) > 1:
        return _base_check(
            item,
            location_status=QuoteLocationStatus.AMBIGUOUS_QUOTE,
            match_count=len(matches),
        )
    start, end = matches[0]
    return _base_check(
        item,
        location_status=QuoteLocationStatus.LOCATED,
        source_locator=source.metadata.get("source_locators") or source.title,
        char_start=start,
        char_end=end,
        match_count=1,
    )


def _base_check(
    item: CitationSupportInput,
    *,
    location_status: QuoteLocationStatus,
    source_locator: str | None = None,
    char_start: int | None = None,
    char_end: int | None = None,
    match_count: int = 0,
) -> CitationSupportCheck:
    return CitationSupportCheck(
        claim_id=item.claim_id.strip(),
        claim_text=item.claim_text.strip(),
        source_id=item.source_id.strip(),
        excerpt=item.excerpt.strip(),
        location_status=location_status,
        source_locator=source_locator,
        char_start=char_start,
        char_end=char_end,
        match_count=match_count,
    )


def _normalized_matches(source: str, excerpt: str) -> list[tuple[int, int]]:
    normalized_source, offsets = _normalize_with_offsets(source)
    normalized_excerpt, _ = _normalize_with_offsets(excerpt)
    if not normalized_excerpt:
        return []
    matches: list[tuple[int, int]] = []
    start = 0
    while True:
        index = normalized_source.find(normalized_excerpt, start)
        if index < 0:
            break
        original_start = offsets[index]
        original_end = offsets[index + len(normalized_excerpt) - 1] + 1
        matches.append((original_start, original_end))
        start = index + 1
    return matches


def _normalize_with_offsets(value: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    offsets: list[int] = []
    pending_space_offset: int | None = None
    for original_index, original_char in enumerate(value):
        normalized_piece = unicodedata.normalize("NFKC", original_char)
        for char in normalized_piece:
            if char.isspace():
                if chars and chars[-1] != " " and pending_space_offset is None:
                    pending_space_offset = original_index
                continue
            if pending_space_offset is not None:
                chars.append(" ")
                offsets.append(pending_space_offset)
                pending_space_offset = None
            chars.append(char)
            offsets.append(original_index)
    return "".join(chars).strip(), offsets


def _result_without_model(checks, *, prompt_ref, config_ref, structured_mode):
    return CitationSupportResult(
        checks=checks,
        verified_citations=(),
        report=_report(
            checks,
            status=CitationSupportValidationStatus.COMPLETED,
            prompt_ref=prompt_ref,
            config_ref=config_ref,
            structured_mode=structured_mode,
            model_call_count=0,
            response=None,
        ),
        messages=(),
        response=None,
    )


def _result_with_failed_judgment(
    checks,
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
    return CitationSupportResult(
        checks=checks,
        verified_citations=(),
        report=_report(
            checks,
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


def _report(
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
    verdicts = [check.verdict for check in checks]
    usage = response.llm.usage if response is not None else None
    cost = (
        estimate_usage_cost(
            usage,
            config_ref=config_ref,
            model=response.llm.model,
        )
        if response is not None
        else None
    )
    return CitationSupportReport(
        status=status,
        prompt_ref=prompt_ref,
        config_ref=config_ref,
        structured_mode=structured_mode,
        input_count=len(checks),
        located_count=sum(
            check.location_status is QuoteLocationStatus.LOCATED for check in checks
        ),
        quote_not_found_count=sum(
            check.location_status is QuoteLocationStatus.QUOTE_NOT_FOUND
            for check in checks
        ),
        ambiguous_quote_count=sum(
            check.location_status is QuoteLocationStatus.AMBIGUOUS_QUOTE
            for check in checks
        ),
        skipped_count=sum(
            check.location_status
            in {
                QuoteLocationStatus.MISSING_EXCERPT,
                QuoteLocationStatus.SOURCE_NOT_ALLOWED,
            }
            for check in checks
        ),
        judged_count=sum(verdict is not None for verdict in verdicts),
        supported_count=verdicts.count(CitationSupportVerdict.SUPPORTED),
        contradicted_count=verdicts.count(CitationSupportVerdict.CONTRADICTED),
        unrelated_count=verdicts.count(CitationSupportVerdict.UNRELATED),
        indeterminate_count=verdicts.count(CitationSupportVerdict.INDETERMINATE),
        model_call_count=model_call_count,
        usage=usage,
        cost=cost,
        latency_ms=response.llm.latency_ms if response is not None else None,
        parse_error_stage=error_stage,
        parse_error_message=error_message,
    )


def _is_supported(check: CitationSupportCheck) -> bool:
    return check.verdict is CitationSupportVerdict.SUPPORTED


def _verified(check: CitationSupportCheck) -> VerifiedCitation:
    if (
        check.char_start is None
        or check.char_end is None
        or check.reason is None
        or check.verdict is not CitationSupportVerdict.SUPPORTED
    ):
        raise ValueError("只有完成定位且判断为 supported 的检查才能形成 VerifiedCitation")
    return VerifiedCitation(
        claim_id=check.claim_id,
        claim_text=check.claim_text,
        source_id=check.source_id,
        excerpt=check.excerpt,
        source_locator=check.source_locator,
        char_start=check.char_start,
        char_end=check.char_end,
        verdict=check.verdict,
        reason=check.reason,
    )
