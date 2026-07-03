"""Source ranking, section mapping, and dedupe rules."""

from __future__ import annotations

import re
from typing import Optional, Sequence

from llm_core.context.formatting import format_context_source
from llm_core.context.tokenization import estimate_tokens
from llm_core.context.types import (
    ContextBuildPolicy,
    ContextSectionName,
    ContextSource,
    DroppedContextSource,
)

EVIDENCE_TYPES = {"evidence", "business_rule", "api_doc", "client_note"}

SOURCE_SECTION: dict[str, ContextSectionName] = {
    "requirement": "requirement",
    "evidence": "evidence",
    "business_rule": "evidence",
    "api_doc": "evidence",
    "client_note": "evidence",
    "history": "history",
    "history_review": "history",
    "agent_summary": "agent_summary",
    "tool_result": "agent_summary",
    "other": "other",
}

SOURCE_TYPE_WEIGHT: dict[str, int] = {
    "business_rule": 95,
    "api_doc": 90,
    "evidence": 80,
    "client_note": 70,
    "agent_summary": 55,
    "tool_result": 45,
    "history_review": 35,
    "history": 30,
    "other": 10,
}


def prepare_sources(
    sources: Sequence[ContextSource],
    policy: ContextBuildPolicy,
    dropped: list[DroppedContextSource],
) -> list[ContextSource]:
    by_id: dict[str, ContextSource] = {}
    by_content: dict[str, ContextSource] = {}
    for source in sources:
        if policy.include_source_types is not None and source.source_type not in policy.include_source_types:
            dropped.append(drop_source(source, "source_type_excluded"))
            continue

        normalized = normalize_content(source.content)
        existing = by_id.get(source.source_id)
        if existing is not None:
            better = max((existing, source), key=source_rank)
            loser = source if better is existing else existing
            dropped.append(drop_source(loser, "duplicate_source_id"))
            if better is source:
                existing_normalized = normalize_content(existing.content)
                if by_content.get(existing_normalized) is existing:
                    by_content.pop(existing_normalized)
                by_id[source.source_id] = source
                by_content[normalized] = source
            continue

        existing_content = by_content.get(normalized)
        if existing_content is not None:
            better = max((existing_content, source), key=source_rank)
            loser = source if better is existing_content else existing_content
            dropped.append(drop_source(loser, "duplicate_content"))
            if better is source:
                by_id.pop(existing_content.source_id, None)
                by_id[source.source_id] = source
                by_content[normalized] = source
            continue

        by_id[source.source_id] = source
        by_content[normalized] = source

    return sorted(by_id.values(), key=source_rank, reverse=True)


def section_for_source(source: ContextSource) -> ContextSectionName:
    return SOURCE_SECTION.get(source.source_type, "other")


def source_rank(source: ContextSource) -> tuple[int, int, float, str]:
    return (
        SOURCE_TYPE_WEIGHT.get(source.source_type, 0),
        source.priority,
        source.score if source.score is not None else 0.0,
        source.source_id,
    )


def drop_source(
    source: ContextSource,
    reason: str,
    *,
    estimated_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> DroppedContextSource:
    return DroppedContextSource(
        source_id=source.source_id,
        source_type=source.source_type,
        title=source.title,
        reason=reason,
        estimated_tokens=estimated_tokens
        if estimated_tokens is not None
        else estimate_tokens(format_context_source(source), model=model),
    )


def normalize_content(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()
