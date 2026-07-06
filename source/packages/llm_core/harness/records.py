"""Harness run records and summary metrics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from llm_core.errors import LLMErrorCode


@dataclass(frozen=True)
class HarnessRunRecord:
    case_id: str
    title: str
    status: str
    config_ref: Optional[str]
    model: Optional[str] = None
    content_preview: str = ""
    parse_ok: Optional[bool] = None
    risk_count: Optional[int] = None
    latency_ms: float = 0.0
    total_tokens: Optional[int] = None
    error_code: Optional[LLMErrorCode] = None
    message: Optional[str] = None
    attempt_count: int = 0
    degraded: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "success"


@dataclass(frozen=True)
class HarnessSummary:
    total: int
    success_count: int
    failed_count: int
    parse_success_count: int
    degraded_count: int
    average_latency_ms: float
    error_counts: dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total if self.total else 0.0

    @property
    def parse_success_rate(self) -> float:
        return self.parse_success_count / self.total if self.total else 0.0

    @classmethod
    def from_records(cls, records: list[HarnessRunRecord]) -> "HarnessSummary":
        total = len(records)
        success_count = sum(1 for record in records if record.ok)
        failed_count = total - success_count
        parse_success_count = sum(1 for record in records if record.parse_ok is True)
        degraded_count = sum(1 for record in records if record.degraded)
        average_latency_ms = sum(record.latency_ms for record in records) / total if total else 0.0
        errors = Counter(record.error_code.value for record in records if record.error_code is not None)
        return cls(
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            parse_success_count=parse_success_count,
            degraded_count=degraded_count,
            average_latency_ms=average_latency_ms,
            error_counts=dict(errors),
        )
