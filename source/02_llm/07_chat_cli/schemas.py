"""
schemas.py
第七章综合项目的数据结构：消息、会话、使用量、成本、风控、命令状态
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MessageRecord:
    """一条进入会话历史的消息记录。"""

    role: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UsageStats:
    """模型返回的 token 使用量。"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class CostStats:
    """把 usage 和单价结合后的成本视图。"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_price_per_million: float | None
    output_price_per_million: float | None
    estimated_cost: float | None


@dataclass
class RetryLog:
    """一次重试的过程记录。"""

    attempt: int
    wait_seconds: float
    category: str
    message: str


@dataclass
class ErrorInfo:
    """归一化后的错误信息，供 CLI 和 API 统一展示。"""

    category: str
    retryable: bool
    message: str
    user_hint: str


@dataclass
class SafetyAssessment:
    """对用户输入做的基础安全评估结果。"""

    risk_score: int
    blocked: bool
    reasons: list[str]
    normalized_text: str


@dataclass
class ProjectSession:
    """项目级会话对象，保存配置、历史消息和累计统计。"""

    session_id: str
    provider: str
    model: str
    system_prompt: str
    json_mode: bool = False
    stream_mode: bool = False
    temperature: float = 0.3
    max_tokens: int = 500
    keep_last_messages: int = 12
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: list[MessageRecord] = field(default_factory=list)
    accumulated_prompt_tokens: int = 0
    accumulated_completion_tokens: int = 0
    accumulated_total_tokens: int = 0
    accumulated_estimated_cost: float = 0.0
    turn_count: int = 0
    latest_request_preview: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnResult:
    """服务层完成一轮请求后，对外返回的统一结果。"""

    ok: bool
    session_id: str
    provider: str
    model: str
    reply: str | None
    mocked: bool
    from_cache: bool
    json_mode: bool
    stream_mode: bool
    elapsed_ms: float
    usage: UsageStats | None
    cost: CostStats | None
    retries: list[RetryLog]
    safety: SafetyAssessment
    request_preview: dict[str, Any]
    session_estimated_tokens: int
    error: ErrorInfo | None = None


@dataclass
class CLIState:
    """CLI 展示和切换命令时真正关心的轻量状态视图。"""

    session_id: str
    provider: str
    model: str
    system_prompt: str
    json_mode: bool
    stream_mode: bool
    temperature: float
    max_tokens: int
    keep_last_messages: int
