"""Reliable call attempt and result records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from llm_core.errors import LLMError, LLMErrorCode

T = TypeVar("T")


@dataclass(frozen=True)
class ReliableCallAttempt:
    attempt_number: int
    config_ref: str
    status: str
    latency_ms: float
    error_code: Optional[LLMErrorCode] = None
    message: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "success"


@dataclass(frozen=True)
class ReliableCallReport:
    primary_config_ref: str
    final_config_ref: Optional[str]
    attempts: list[ReliableCallAttempt] = field(default_factory=list)
    degraded: bool = False
    final_error_code: Optional[LLMErrorCode] = None
    final_message: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.final_error_code is None and self.final_config_ref is not None

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    @property
    def attempted_config_refs(self) -> list[str]:
        return [attempt.config_ref for attempt in self.attempts]


@dataclass(frozen=True)
class ReliableCallResult(Generic[T]):
    output: Optional[T]
    report: ReliableCallReport
    error: Optional[LLMError] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.output is not None
