"""Model configuration and response types for llm_core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

ModelRole = Literal["chat", "embedding", "rerank"]


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class CapabilityTags:
    context_length: Optional[int] = None
    streaming: Optional[bool] = None
    tool_calling: Optional[bool] = None
    structured_output: Optional[bool] = None
    cost_tier: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> CapabilityTags:
        if not data:
            return cls()
        return cls(
            context_length=data.get("context_length"),
            streaming=data.get("streaming"),
            tool_calling=data.get("tool_calling"),
            structured_output=data.get("structured_output"),
            cost_tier=data.get("cost_tier"),
        )


@dataclass(frozen=True)
class ModelConfig:
    config_ref: str
    role: ModelRole
    provider: str
    model: str
    api_key_env: str
    base_url: Optional[str] = None
    default_params: dict[str, Any] = field(default_factory=dict)
    capabilities: CapabilityTags = field(default_factory=CapabilityTags)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    raw_response: Any
    usage: Optional[TokenUsage]
    latency_ms: float
    provider: str
    model: str
    config_ref: str
