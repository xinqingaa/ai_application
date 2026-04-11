"""
Shared data structures for foundation_lab.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RetrievedDocument:
    doc_id: str
    title: str
    content: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    tool_input: str
    output: str


@dataclass(frozen=True)
class AskRequest:
    question: str
    engine: str = "langchain"


@dataclass
class AskResponse:
    question: str
    answer: str
    path: str
    engine: str
    mocked: bool
    used_documents: list[RetrievedDocument] = field(default_factory=list)
    used_tool: ToolResult | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
