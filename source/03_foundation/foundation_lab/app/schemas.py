"""
定义 foundation_lab 在各层之间传递的共享数据结构。

这些 dataclass 的目标不是追求复杂建模，而是先把 retriever、tool、service
之间的数据边界固定下来。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RetrievedDocument:
    """表示 retriever 返回的一条文档片段。"""

    doc_id: str
    title: str
    content: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolResult:
    """表示工具执行后的标准化结果。"""

    tool_name: str
    tool_input: str
    output: str


@dataclass(frozen=True)
class AskRequest:
    """表示最小问答请求。"""

    question: str
    engine: str = "langchain"


@dataclass
class AskResponse:
    """表示 service 层返回给脚本或 API 的统一响应。"""

    question: str
    answer: str
    path: str
    engine: str
    mocked: bool
    used_documents: list[RetrievedDocument] = field(default_factory=list)
    used_tool: ToolResult | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
