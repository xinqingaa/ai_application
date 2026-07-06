"""Streaming event primitives for LLM calls."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from uuid import uuid4

StreamEventType = Literal["message_start", "token", "message_done", "error", "done"]


@dataclass(frozen=True)
class LLMStreamEvent:
    """One application-level event emitted during a streaming model call."""

    type: StreamEventType
    run_id: str
    sequence: int
    delta: Optional[str] = None
    content: Optional[str] = None
    message: Optional[str] = None
    code: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    config_ref: Optional[str] = None
    latency_ms: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.type,
            "run_id": self.run_id,
            "sequence": self.sequence,
        }
        optional = {
            "delta": self.delta,
            "content": self.content,
            "message": self.message,
            "code": self.code,
            "provider": self.provider,
            "model": self.model,
            "config_ref": self.config_ref,
            "latency_ms": self.latency_ms,
        }
        for key, value in optional.items():
            if value is not None:
                data[key] = value
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class StreamEventBuilder:
    """Assign run id, sequence and elapsed time to stream events."""

    def __init__(self, *, run_id: Optional[str] = None) -> None:
        self.run_id = run_id or uuid4().hex
        self._sequence = 0
        self._t0 = time.perf_counter()

    def event(
        self,
        type: StreamEventType,
        *,
        delta: Optional[str] = None,
        content: Optional[str] = None,
        message: Optional[str] = None,
        code: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        config_ref: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        include_latency: bool = False,
    ) -> LLMStreamEvent:
        self._sequence += 1
        latency_ms = None
        if include_latency:
            latency_ms = round((time.perf_counter() - self._t0) * 1000, 1)
        return LLMStreamEvent(
            type=type,
            run_id=self.run_id,
            sequence=self._sequence,
            delta=delta,
            content=content,
            message=message,
            code=code,
            provider=provider,
            model=model,
            config_ref=config_ref,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )


def encode_sse(event: LLMStreamEvent) -> str:
    """Encode one event as Server-Sent Events text."""

    return (
        f"id: {event.run_id}:{event.sequence}\n"
        f"event: {event.type}\n"
        f"data: {event.to_json()}\n\n"
    )
