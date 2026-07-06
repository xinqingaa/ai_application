"""Harness input cases and run configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from llm_core.reliability import DegradationPolicy, RetryPolicy
from llm_core.structured import StructuredMode


@dataclass(frozen=True)
class HarnessCase:
    case_id: str
    title: str
    messages: list[dict[str, str]]
    expected_focus: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_user_input(
        cls,
        *,
        case_id: str,
        title: str,
        user_input: str,
        system_prompt: str = "你是需求评审助手，请基于输入识别研发风险。",
        expected_focus: tuple[str, ...] = (),
        tags: tuple[str, ...] = (),
        metadata: Optional[dict[str, Any]] = None,
    ) -> "HarnessCase":
        return cls(
            case_id=case_id,
            title=title,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            expected_focus=expected_focus,
            tags=tags,
            metadata=metadata or {},
        )


@dataclass(frozen=True)
class HarnessRunConfig:
    run_name: str
    config_ref: str = "chat.dev_chat"
    structured: bool = True
    structured_mode: StructuredMode = "json_object"
    temperature: float = 0
    max_tokens: Optional[int] = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    degradation_policy: DegradationPolicy = field(default_factory=DegradationPolicy)
