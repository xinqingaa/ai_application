"""Main context-building pipeline for review prompts."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional, Sequence

from llm_core.context.compression import extract_keywords, fit_source
from llm_core.context.formatting import SECTION_TITLES, format_context_source, format_evidence_block
from llm_core.context.policies import get_context_policy
from llm_core.context.ranking import EVIDENCE_TYPES, drop_source, prepare_sources, section_for_source
from llm_core.context.tokenization import estimate_tokens
from llm_core.context.types import (
    BuiltContext,
    CitationCandidate,
    CompressedContextSource,
    ContextBuildPolicy,
    ContextBuildReport,
    ContextSection,
    ContextSectionName,
    ContextSource,
    ContextWarning,
    DroppedContextSource,
)


def build_review_context(
    *,
    requirement_text: str,
    sources: Sequence[ContextSource] = (),
    token_budget: Optional[int] = None,
    model: Optional[str] = None,
    policy: Optional[ContextBuildPolicy] = None,
    strategy: Optional[str] = None,
) -> BuiltContext:
    """Build a traceable context block for review prompts."""

    active_policy = policy or get_context_policy(strategy or "balanced")
    if token_budget is not None:
        active_policy = replace(active_policy, token_budget=token_budget)

    requirement = requirement_text.strip()
    if not requirement:
        raise ValueError("requirement_text 不能为空")

    warnings: list[ContextWarning] = []
    dropped: list[DroppedContextSource] = []
    compressed: list[CompressedContextSource] = []
    keywords = extract_keywords(requirement)

    requirement_tokens = estimate_tokens(requirement, model=model)
    requirement_budget = active_policy.section_budgets.get("requirement", active_policy.token_budget)
    if requirement_tokens > requirement_budget:
        warnings.append(
            ContextWarning(
                code="requirement_over_section_budget",
                message=f"Requirement 估算 {requirement_tokens} tokens，超过 section budget {requirement_budget}",
            )
        )
    total_tokens = requirement_tokens

    prepared_sources = prepare_sources(sources, active_policy, dropped)
    included_by_section: dict[ContextSectionName, list[ContextSource]] = {
        "evidence": [],
        "history": [],
        "agent_summary": [],
        "other": [],
    }

    for section_name in ("evidence", "history", "agent_summary", "other"):
        total_tokens = _fill_section(
            section_name=section_name,
            prepared_sources=prepared_sources,
            included_by_section=included_by_section,
            active_policy=active_policy,
            total_tokens=total_tokens,
            keywords=keywords,
            dropped=dropped,
            compressed=compressed,
            warnings=warnings,
            model=model,
        )

    sections = _build_sections(requirement, included_by_section, model=model)
    included_sources = [source for section in sections for source in section.sources]
    evidence_sources = included_by_section["evidence"]
    evidence_block = format_evidence_block(evidence_sources)
    if not evidence_sources:
        warnings.append(
            ContextWarning(
                code="no_evidence_included",
                message="No evidence source included; model should avoid evidence-backed claims.",
            )
        )

    citation_candidates = _citation_candidates(evidence_sources)
    section_tokens = {section.name: section.estimated_tokens for section in sections}
    report = ContextBuildReport(
        policy_name=active_policy.name,
        token_budget=active_policy.token_budget,
        estimated_tokens=sum(section.estimated_tokens for section in sections),
        section_tokens=section_tokens,
        dropped_sources=dropped,
        compressed_sources=compressed,
        citation_candidates=citation_candidates,
        warnings=warnings,
    )
    return BuiltContext(
        requirement_text=requirement,
        evidence_block=evidence_block,
        included_sources=included_sources,
        dropped_sources=dropped,
        estimated_tokens=report.estimated_tokens,
        token_budget=active_policy.token_budget,
        sections=sections,
        report=report,
    )


def _fill_section(
    *,
    section_name: ContextSectionName,
    prepared_sources: Sequence[ContextSource],
    included_by_section: dict[ContextSectionName, list[ContextSource]],
    active_policy: ContextBuildPolicy,
    total_tokens: int,
    keywords: set[str],
    dropped: list[DroppedContextSource],
    compressed: list[CompressedContextSource],
    warnings: list[ContextWarning],
    model: Optional[str],
) -> int:
    section_sources = [source for source in prepared_sources if section_for_source(source) == section_name]
    section_budget = active_policy.section_budgets.get(section_name, 0)
    if section_budget <= 0:
        for source in section_sources:
            dropped.append(drop_source(source, "section_disabled", model=model))
        if section_sources:
            warnings.append(
                ContextWarning(
                    code="section_disabled",
                    message=f"{section_name} section disabled by policy {active_policy.name}",
                )
            )
        return total_tokens

    section_tokens = 0
    for source in section_sources:
        available_total = active_policy.token_budget - total_tokens
        available_section = section_budget - section_tokens
        available = min(available_total, available_section)
        if available <= 0:
            dropped.append(drop_source(source, "token_budget_exceeded", model=model))
            continue

        source_to_insert, source_tokens, compression = fit_source(
            source,
            available_tokens=available,
            policy=active_policy,
            keywords=keywords,
            model=model,
        )
        if source_tokens <= available:
            included_by_section[section_name].append(source_to_insert)
            section_tokens += source_tokens
            total_tokens += source_tokens
            if compression is not None:
                compressed.append(compression)
                warnings.append(
                    ContextWarning(
                        code="source_compressed",
                        message=(
                            f"{source.source_id} compressed "
                            f"{compression.original_tokens}->{compression.compressed_tokens} tokens"
                        ),
                        source_id=source.source_id,
                    )
                )
        else:
            dropped.append(drop_source(source, "token_budget_exceeded", estimated_tokens=source_tokens, model=model))
    return total_tokens


def _build_sections(
    requirement: str,
    included_by_section: dict[ContextSectionName, list[ContextSource]],
    *,
    model: Optional[str],
) -> list[ContextSection]:
    sections = [
        ContextSection(
            name="requirement",
            title=SECTION_TITLES["requirement"],
            content=requirement,
            sources=[],
            estimated_tokens=estimate_tokens(requirement, model=model),
        )
    ]
    for section_name in ("evidence", "history", "agent_summary", "other"):
        sources = included_by_section.get(section_name, [])
        content = "\n\n".join(format_context_source(source) for source in sources)
        sections.append(
            ContextSection(
                name=section_name,
                title=SECTION_TITLES[section_name],
                content=content,
                sources=sources,
                estimated_tokens=estimate_tokens(content, model=model),
            )
        )
    return sections


def _citation_candidates(sources: Sequence[ContextSource]) -> list[CitationCandidate]:
    return [
        CitationCandidate(
            source_id=source.source_id,
            source_type=source.source_type,
            title=source.title,
            metadata=source.metadata,
        )
        for source in sources
        if source.source_type in EVIDENCE_TYPES
    ]
