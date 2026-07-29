"""Structured application logger backed by Rich or JSON Lines."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Literal, TextIO

from app_log.console import console
from app_log.events import LogEvent, LogLevel
from app_log.redaction import redact

LogFormat = Literal["compact", "verbose", "json", "quiet"]
_ROOT_LOGGER_NAME = "ai_application"


class AppLogger:
    def __init__(self, component: str) -> None:
        self.component = component
        self._logger = logging.getLogger(f"{_ROOT_LOGGER_NAME}.{component}")

    def debug(self, event_name: str, message: str, **fields: Any) -> None:
        self._emit("debug", event_name, message, fields)

    def info(self, event_name: str, message: str, **fields: Any) -> None:
        self._emit("info", event_name, message, fields)

    def success(self, event_name: str, message: str, **fields: Any) -> None:
        self._emit("info", event_name, message, {"status": "success", **fields})

    def warning(self, event_name: str, message: str, **fields: Any) -> None:
        self._emit("warning", event_name, message, fields)

    def error(self, event_name: str, message: str, **fields: Any) -> None:
        self._emit("error", event_name, message, fields)

    def _emit(
        self,
        level: LogLevel,
        event_name: str,
        message: str,
        fields: dict[str, Any],
    ) -> None:
        safe_fields = redact(fields)
        event = LogEvent(
            event_name=event_name,
            message=message,
            component=self.component,
            level=level,
            run_id=_string_or_none(safe_fields.pop("run_id", None)),
            operation=_string_or_none(safe_fields.pop("operation", None)),
            status=_string_or_none(safe_fields.pop("status", None)),
            duration_ms=_float_or_none(safe_fields.pop("duration_ms", None)),
            fields=safe_fields,
        )
        self._logger.log(_level_number(level), message, extra={"app_event": event})


class _RichEventHandler(logging.Handler):
    def __init__(self, *, verbose: bool) -> None:
        super().__init__()
        self.verbose = verbose

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "app_event", None)
        if not isinstance(event, LogEvent):
            return
        fields = dict(event.fields)
        if event.run_id is not None:
            fields["run_id"] = event.run_id
        if event.operation is not None:
            fields["operation"] = event.operation
        if event.status is not None:
            fields["status"] = event.status
        if event.duration_ms is not None:
            fields["duration_ms"] = event.duration_ms
        console.log_event(
            level=event.level,
            component=event.component,
            event_name=event.event_name,
            message=event.message,
            fields=fields,
            verbose=self.verbose,
        )


class _JsonEventHandler(logging.Handler):
    def __init__(self, *, out: TextIO, err: TextIO) -> None:
        super().__init__()
        self.out = out
        self.err = err

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "app_event", None)
        if not isinstance(event, LogEvent):
            return
        target = self.err if event.level in {"warning", "error"} else self.out
        target.write(json.dumps(event.to_dict(), ensure_ascii=False, default=str))
        target.write("\n")
        target.flush()


def get_logger(component: str) -> AppLogger:
    normalized = component.removeprefix(f"{_ROOT_LOGGER_NAME}.")
    return AppLogger(normalized)


def configure_logging(
    *,
    log_format: LogFormat = "compact",
    level: str = "INFO",
    color: str = "auto",
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> None:
    if log_format not in {"compact", "verbose", "json", "quiet"}:
        raise ValueError("log_format 必须是 compact、verbose、json 或 quiet")
    if log_format == "json":
        console.configure(color=color)
    else:
        console.configure(
            color=color,
            out=out or sys.stdout,
            err=err or sys.stderr,
        )
    root = logging.getLogger(_ROOT_LOGGER_NAME)
    root.handlers.clear()
    root.propagate = False
    root.setLevel(logging.DEBUG)
    threshold = logging.WARNING if log_format == "quiet" else getattr(logging, level.upper())

    if log_format == "json":
        handler: logging.Handler = _JsonEventHandler(
            out=out or sys.stdout,
            err=err or sys.stderr,
        )
    else:
        handler = _RichEventHandler(verbose=log_format == "verbose")
    handler.setLevel(threshold)
    root.addHandler(handler)


def _level_number(level: LogLevel) -> int:
    return {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }[level]


def _string_or_none(value: Any) -> str | None:
    return None if value is None else str(value)


def _float_or_none(value: Any) -> float | None:
    return None if value is None else float(value)


logging.getLogger(_ROOT_LOGGER_NAME).addHandler(logging.NullHandler())
