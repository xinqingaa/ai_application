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
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: float = 0.0
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    cost_currency: str = "USD"
    cost_estimate_known: bool = False
    cache_hit: bool = False
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
    max_latency_ms: float
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_total_cost: Optional[float]
    cost_currency: str = "USD"
    cache_hit_count: int = 0
    error_counts: dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total if self.total else 0.0

    @property
    def parse_success_rate(self) -> float:
        return self.parse_success_count / self.total if self.total else 0.0

    @property
    def cache_hit_rate(self) -> float:
        return self.cache_hit_count / self.total if self.total else 0.0

    @classmethod
    def from_records(cls, records: list[HarnessRunRecord]) -> "HarnessSummary":
        total = len(records)
        success_count = sum(1 for record in records if record.ok)
        failed_count = total - success_count
        parse_success_count = sum(1 for record in records if record.parse_ok is True)
        degraded_count = sum(1 for record in records if record.degraded)
        average_latency_ms = sum(record.latency_ms for record in records) / total if total else 0.0
        max_latency_ms = max((record.latency_ms for record in records), default=0.0)
        prompt_tokens = sum(record.prompt_tokens or 0 for record in records)
        completion_tokens = sum(record.completion_tokens or 0 for record in records)
        total_tokens = sum(record.total_tokens or 0 for record in records)
        known_costs = [record.estimated_cost for record in records if record.estimated_cost is not None]
        estimated_total_cost = sum(known_costs) if known_costs else None
        cache_hit_count = sum(1 for record in records if record.cache_hit)
        errors = Counter(record.error_code.value for record in records if record.error_code is not None)
        return cls(
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            parse_success_count=parse_success_count,
            degraded_count=degraded_count,
            average_latency_ms=average_latency_ms,
            max_latency_ms=max_latency_ms,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_total_cost=estimated_total_cost,
            cache_hit_count=cache_hit_count,
            error_counts=dict(errors),
        )
