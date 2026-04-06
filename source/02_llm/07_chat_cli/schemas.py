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
    role: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UsageStats:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class CostStats:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_price_per_million: float | None
    output_price_per_million: float | None
    estimated_cost: float | None


@dataclass
class RetryLog:
    attempt: int
    wait_seconds: float
    category: str
    message: str


@dataclass
class ErrorInfo:
    category: str
    retryable: bool
    message: str
    user_hint: str


@dataclass
class SafetyAssessment:
    risk_score: int
    blocked: bool
    reasons: list[str]
    normalized_text: str


@dataclass
class ProjectSession:
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
    session_id: str
    provider: str
    model: str
    system_prompt: str
    json_mode: bool
    stream_mode: bool
    temperature: float
    max_tokens: int
    keep_last_messages: int
