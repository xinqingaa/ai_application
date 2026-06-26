"""Call logging helpers for debugging and learning."""

from __future__ import annotations

import json
from typing import Any, Optional

from llm_core.config import LLMResponse, TokenUsage


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


def format_call_log(
    messages: list[dict[str, str]],
    params: dict[str, Any],
    response: LLMResponse,
) -> str:
    sections = [
        "=" * 60,
        f"config_ref: {response.config_ref}",
        f"provider: {response.provider}",
        f"model (request/response): {response.model}",
        f"latency_ms: {round(response.latency_ms, 1)}",
        "",
        "【request params】",
        json.dumps(params, ensure_ascii=False, indent=2),
        "",
        "【messages】",
        _format_messages(messages),
        "",
        "【assistant content】",
        response.content,
        "",
        "【usage】",
        _format_usage(response.usage),
        "=" * 60,
    ]
    return "\n".join(sections)


def print_call_log(
    messages: list[dict[str, str]],
    params: dict[str, Any],
    response: LLMResponse,
) -> None:
    print(format_call_log(messages, params, response))
