"""Call logging and unified demo terminal output."""

from __future__ import annotations

import json
import sys
from io import StringIO
from typing import Any, Optional, TextIO

from llm_core.config import LLMResponse, TokenUsage


class DemoLog:
    """Unified [tag] terminal output for demos, debug, and call logs."""

    def __init__(self, *, out: Optional[TextIO] = None, err: Optional[TextIO] = None) -> None:
        self._out = out or sys.stdout
        self._err = err or sys.stderr

    def emit(self, text: str = "", *, err: bool = False) -> None:
        stream = self._err if err else self._out
        stream.write(text)
        stream.write("\n")
        stream.flush()

    def blank(self) -> None:
        self.emit("")

    def section(self, name: str) -> None:
        self.emit(f"[{name}]")

    def field(self, name: str, value: Any = None, *, indent: int = 0) -> None:
        pad = "  " * indent
        if value is None:
            self.emit(f"{pad}[{name}]")
        else:
            self.emit(f"{pad}[{name}] {value}")

    def item(self, index: int | str, text: str, *, indent: int = 1) -> None:
        pad = "  " * indent
        self.emit(f"{pad}[{index}] {text}")

    def text(self, name: str, content: str, *, indent: int = 1) -> None:
        pad = "  " * indent
        self.emit(f"{pad}[{name}]")
        if not content:
            self.emit(f"{pad}  (empty)")
            return
        for line in content.splitlines():
            self.emit(f"{pad}  {line}")

    def error(self, name: str, message: str, *, indent: int = 0) -> None:
        pad = "  " * indent
        self.emit(f"{pad}[{name}] {message}", err=True)

    def hint(self, message: str) -> None:
        self.emit(f"[hint] {message}")

    def capture(self) -> "_CaptureLog":
        return _CaptureLog()


class _CaptureLog(DemoLog):
    """Collect log lines into a string (for format_call_log)."""

    def __init__(self) -> None:
        super().__init__(out=StringIO(), err=StringIO())
        self._buffer = self._out  # type: ignore[assignment]

    def getvalue(self) -> str:
        assert isinstance(self._buffer, StringIO)
        return self._buffer.getvalue().rstrip("\n")


demo_log = DemoLog()


def _format_messages(messages: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for i, msg in enumerate(messages, start=1):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        lines.append(f"--- message {i} [{role}] ---")
        lines.append(content)
    return "\n".join(lines)


def _format_usage(usage: Optional[TokenUsage]) -> str:
    if usage is None:
        return "(not provided)"
    return json.dumps(
        {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
        ensure_ascii=False,
        indent=2,
    )


def render_experiment_messages_once(
    log: DemoLog,
    messages: list[dict[str, str]],
) -> None:
    """Print full rendered messages once for verbose structured demos."""
    log.text("messages", _format_messages(messages), indent=1)
    log.blank()


def render_structured_mode_verbose(
    log: DemoLog,
    *,
    request_params: dict[str, Any],
    response: LLMResponse,
    parse_result: str,
) -> None:
    """Print raw request and response for one structured output mode."""
    log.text(
        "request_params",
        json.dumps(request_params, ensure_ascii=False, indent=2),
        indent=1,
    )
    log.text("assistant_raw", response.content, indent=1)
    log.text("usage", _format_usage(response.usage), indent=1)
    log.field("parse_result", parse_result, indent=1)


def render_call_log(
    log: DemoLog,
    messages: list[dict[str, str]],
    params: dict[str, Any],
    response: LLMResponse,
) -> None:
    log.section("call_detail")
    log.field("config_ref", response.config_ref, indent=1)
    log.field("provider", response.provider, indent=1)
    log.field("model", response.model, indent=1)
    log.field("latency_ms", round(response.latency_ms, 1), indent=1)
    log.text("request_params", json.dumps(params, ensure_ascii=False, indent=2), indent=1)
    log.text("messages", _format_messages(messages), indent=1)
    log.text("assistant_content", response.content, indent=1)
    log.text("usage", _format_usage(response.usage), indent=1)


def format_call_log(
    messages: list[dict[str, str]],
    params: dict[str, Any],
    response: LLMResponse,
) -> str:
    capture = demo_log.capture()
    render_call_log(capture, messages, params, response)
    return capture.getvalue()


def print_call_log(
    messages: list[dict[str, str]],
    params: dict[str, Any],
    response: LLMResponse,
    *,
    log: Optional[DemoLog] = None,
) -> None:
    target = log or demo_log
    render_call_log(target, messages, params, response)
