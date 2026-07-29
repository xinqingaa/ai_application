"""Stable structured events shared by packages, demos, apps, and products."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from app_log.redaction import redact

LogLevel = Literal["debug", "info", "warning", "error"]


@dataclass(frozen=True)
class LogEvent:
    event_name: str
    message: str
    component: str
    level: LogLevel = "info"
    run_id: str | None = None
    operation: str | None = None
    status: str | None = None
    duration_ms: float | None = None
    fields: Mapping[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["fields"] = redact(dict(self.fields))
        return {key: value for key, value in data.items() if value is not None}
