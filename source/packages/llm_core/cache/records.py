"""Cache hit/miss records for demo diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CacheEvent:
    case_id: str
    hit: bool
    cache_key: str
    saved_tokens: int = 0
    saved_estimated_cost: Optional[float] = None
    saved_latency_ms: float = 0.0


@dataclass(frozen=True)
class CacheStats:
    total: int
    hit_count: int
    miss_count: int
    saved_tokens: int
    saved_estimated_cost: Optional[float]
    saved_latency_ms: float

    @property
    def hit_rate(self) -> float:
        return self.hit_count / self.total if self.total else 0.0

    @classmethod
    def from_events(cls, events: list[CacheEvent]) -> "CacheStats":
        known_costs = [event.saved_estimated_cost for event in events if event.saved_estimated_cost is not None]
        saved_estimated_cost = sum(known_costs) if known_costs else None
        return cls(
            total=len(events),
            hit_count=sum(1 for event in events if event.hit),
            miss_count=sum(1 for event in events if not event.hit),
            saved_tokens=sum(event.saved_tokens for event in events),
            saved_estimated_cost=saved_estimated_cost,
            saved_latency_ms=sum(event.saved_latency_ms for event in events),
        )
