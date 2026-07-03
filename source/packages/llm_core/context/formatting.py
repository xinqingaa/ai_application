"""Prompt formatting helpers for built context sections."""

from __future__ import annotations

from typing import Sequence

from llm_core.context.types import ContextSectionName, ContextSource

SECTION_TITLES: dict[ContextSectionName, str] = {
    "requirement": "Requirement",
    "evidence": "Evidence",
    "history": "History Summary",
    "agent_summary": "Agent Summary",
    "other": "Other Context",
}


def format_context_source(source: ContextSource) -> str:
    title = source.title or source.source_type
    lines = [f"[{source.source_id}] {title}", f"type: {source.source_type}"]
    if source.score is not None:
        lines.append(f"score: {source.score:.2f}")
    if source.metadata:
        metadata = ", ".join(f"{key}={value}" for key, value in sorted(source.metadata.items()))
        lines.append(f"metadata: {metadata}")
    lines.append(source.content)
    return "\n".join(lines).strip()


def format_evidence_block(sources: Sequence[ContextSource]) -> str:
    if not sources:
        return "（无可用证据；只能基于 Requirement 判断，并应避免编造。）"
    return "\n\n".join(format_context_source(source) for source in sources)
