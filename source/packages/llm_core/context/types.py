"""Data contracts for context construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

ContextSourceType = Literal[
    "requirement",
    "evidence",
    "business_rule",
    "api_doc",
    "client_note",
    "history",
    "history_review",
    "agent_summary",
    "tool_result",
    "other",
]

ContextSectionName = Literal["requirement", "evidence", "history", "agent_summary", "other"]


@dataclass(frozen=True)
class ContextSource:
    """One candidate context unit that may be inserted into a prompt."""

    source_id: str
    content: str
    source_type: ContextSourceType = "evidence"
    title: Optional[str] = None
    priority: int = 50
    score: Optional[float] = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_id = self.source_id.strip()
        content = self.content.strip()
        if not source_id:
            raise ValueError("ContextSource.source_id 不能为空")
        if not content:
            raise ValueError(f"ContextSource({source_id}) content 不能为空")
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("ContextSource.score 必须在 0 到 1 之间")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "content", content)
        if self.title is not None:
            object.__setattr__(self, "title", self.title.strip() or None)
        object.__setattr__(self, "metadata", {str(k): str(v) for k, v in self.metadata.items()})


@dataclass(frozen=True)
class ContextBuildPolicy:
    """Budget and ranking policy for one context-building experiment."""

    name: str
    token_budget: int
    section_budgets: dict[ContextSectionName, int]
    allow_compression: bool = True
    max_source_tokens: Optional[int] = 180
    min_compression_tokens: int = 48
    include_source_types: Optional[set[ContextSourceType]] = None

    def __post_init__(self) -> None:
        if self.token_budget <= 0:
            raise ValueError("ContextBuildPolicy.token_budget 必须大于 0")
        if self.max_source_tokens is not None and self.max_source_tokens <= 0:
            raise ValueError("ContextBuildPolicy.max_source_tokens 必须大于 0")
        if self.min_compression_tokens <= 0:
            raise ValueError("ContextBuildPolicy.min_compression_tokens 必须大于 0")


@dataclass(frozen=True)
class DroppedContextSource:
    source_id: str
    reason: str
    estimated_tokens: int
    source_type: ContextSourceType = "other"
    title: Optional[str] = None


@dataclass(frozen=True)
class CompressedContextSource:
    source_id: str
    original_tokens: int
    compressed_tokens: int
    reason: str = "source_token_cap"


@dataclass(frozen=True)
class CitationCandidate:
    source_id: str
    source_type: ContextSourceType
    title: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextWarning:
    code: str
    message: str
    source_id: Optional[str] = None


@dataclass(frozen=True)
class ContextSection:
    name: ContextSectionName
    title: str
    content: str
    sources: list[ContextSource]
    estimated_tokens: int

    @property
    def source_ids(self) -> list[str]:
        return [source.source_id for source in self.sources]


@dataclass(frozen=True)
class ContextBuildReport:
    """Diagnostics for debugging why a context looks the way it does."""

    policy_name: str
    token_budget: int
    estimated_tokens: int
    section_tokens: dict[ContextSectionName, int]
    dropped_sources: list[DroppedContextSource]
    compressed_sources: list[CompressedContextSource]
    citation_candidates: list[CitationCandidate]
    warnings: list[ContextWarning]

    @property
    def compressed_source_ids(self) -> list[str]:
        return [source.source_id for source in self.compressed_sources]

    @property
    def citation_source_ids(self) -> list[str]:
        return [candidate.source_id for candidate in self.citation_candidates]


@dataclass(frozen=True)
class BuiltContext:
    """Prompt-ready context plus budget diagnostics."""

    requirement_text: str
    evidence_block: str
    included_sources: list[ContextSource]
    dropped_sources: list[DroppedContextSource]
    estimated_tokens: int
    token_budget: int
    sections: list[ContextSection] = field(default_factory=list)
    report: Optional[ContextBuildReport] = None

    @property
    def included_source_ids(self) -> list[str]:
        return [source.source_id for source in self.included_sources]

    @property
    def dropped_source_ids(self) -> list[str]:
        return [source.source_id for source in self.dropped_sources]

    @property
    def citation_candidates(self) -> list[CitationCandidate]:
        if self.report is None:
            return []
        return self.report.citation_candidates

    def section_content(self, name: ContextSectionName) -> str:
        for section in self.sections:
            if section.name == name:
                return section.content
        return ""

    def context_block(self) -> str:
        parts: list[str] = []
        for section in self.sections:
            if not section.content:
                continue
            parts.append(f"## {section.title}\n{section.content}")
        return "\n\n".join(parts).strip()

    def to_prompt_variables(self) -> dict[str, str]:
        return {
            "requirement_text": self.requirement_text,
            "evidence_block": self.evidence_block,
            "history_block": self.section_content("history"),
            "agent_summary_block": self.section_content("agent_summary"),
            "context_block": self.context_block(),
        }
