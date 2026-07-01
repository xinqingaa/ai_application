"""Context construction primitives for review-oriented LLM calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence

ContextSourceType = Literal[
    "requirement",
    "evidence",
    "history",
    "agent_summary",
    "tool_result",
    "other",
]


@dataclass(frozen=True)
class ContextSource:
    """One traceable context unit that may be inserted into a prompt."""

    source_id: str
    content: str
    source_type: ContextSourceType = "evidence"
    title: Optional[str] = None
    priority: int = 50
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_id = self.source_id.strip()
        content = self.content.strip()
        if not source_id:
            raise ValueError("ContextSource.source_id 不能为空")
        if not content:
            raise ValueError(f"ContextSource({source_id}) content 不能为空")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "content", content)
        if self.title is not None:
            object.__setattr__(self, "title", self.title.strip() or None)


@dataclass(frozen=True)
class DroppedContextSource:
    source_id: str
    reason: str
    estimated_tokens: int


@dataclass(frozen=True)
class BuiltContext:
    """Prompt-ready context plus budget diagnostics."""

    requirement_text: str
    evidence_block: str
    included_sources: list[ContextSource]
    dropped_sources: list[DroppedContextSource]
    estimated_tokens: int
    token_budget: int

    @property
    def included_source_ids(self) -> list[str]:
        return [source.source_id for source in self.included_sources]

    @property
    def dropped_source_ids(self) -> list[str]:
        return [source.source_id for source in self.dropped_sources]

    def to_prompt_variables(self) -> dict[str, str]:
        return {
            "requirement_text": self.requirement_text,
            "evidence_block": self.evidence_block,
        }


def estimate_tokens(text: str, *, model: Optional[str] = None) -> int:
    """Estimate tokens for budget decisions without requiring a live API call."""

    cleaned = text.strip()
    if not cleaned:
        return 0
    try:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(model or "gpt-4o-mini")
        except Exception:
            encoding = tiktoken.get_encoding("o200k_base")
        return len(encoding.encode(cleaned))
    except Exception:
        return max(1, len(cleaned) // 2)


def build_review_context(
    *,
    requirement_text: str,
    sources: Sequence[ContextSource] = (),
    token_budget: int = 1200,
    model: Optional[str] = None,
) -> BuiltContext:
    """Build a traceable context block for review prompts.

    The budget applies to inserted requirement and evidence materials, not to the
    entire provider context window or final answer.
    """

    requirement = requirement_text.strip()
    if not requirement:
        raise ValueError("requirement_text 不能为空")
    if token_budget <= 0:
        raise ValueError("token_budget 必须大于 0")

    included: list[ContextSource] = []
    dropped: list[DroppedContextSource] = []
    total_tokens = estimate_tokens(requirement, model=model)

    for source in _dedupe_sources(sources):
        formatted = format_context_source(source)
        source_tokens = estimate_tokens(formatted, model=model)
        if total_tokens + source_tokens <= token_budget:
            included.append(source)
            total_tokens += source_tokens
        else:
            dropped.append(
                DroppedContextSource(
                    source_id=source.source_id,
                    reason="token_budget_exceeded",
                    estimated_tokens=source_tokens,
                )
            )

    evidence_block = format_evidence_block(included)
    return BuiltContext(
        requirement_text=requirement,
        evidence_block=evidence_block,
        included_sources=included,
        dropped_sources=dropped,
        estimated_tokens=total_tokens,
        token_budget=token_budget,
    )


def format_context_source(source: ContextSource) -> str:
    title = source.title or source.source_type
    lines = [f"[{source.source_id}] {title}", source.content]
    if source.metadata:
        metadata = ", ".join(f"{key}={value}" for key, value in sorted(source.metadata.items()))
        lines.insert(1, f"metadata: {metadata}")
    return "\n".join(lines).strip()


def format_evidence_block(sources: Sequence[ContextSource]) -> str:
    if not sources:
        return "（无可用证据；只能基于 Requirement 判断，并应避免编造。）"
    return "\n\n".join(format_context_source(source) for source in sources)


def _dedupe_sources(sources: Sequence[ContextSource]) -> list[ContextSource]:
    by_id: dict[str, ContextSource] = {}
    for source in sources:
        existing = by_id.get(source.source_id)
        if existing is None or source.priority > existing.priority:
            by_id[source.source_id] = source
    return sorted(by_id.values(), key=lambda item: (-item.priority, item.source_id))
