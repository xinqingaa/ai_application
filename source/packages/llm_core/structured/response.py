"""Structured chat helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel

from llm_core.config import LLMResponse, ModelConfig
from llm_core.schemas.parse import StructuredParseResult, parse_risk_list

StructuredMode = Literal["json_schema", "json_object", "none"]


@dataclass(frozen=True)
class StructuredLLMResponse:
    llm: LLMResponse
    parse: StructuredParseResult
    structured_mode: StructuredMode
    request_params: dict[str, Any]


def merge_chat_request_params(
    config: ModelConfig,
    call_params: dict[str, Any],
) -> dict[str, Any]:
    """Merge models.yaml defaults with per-call params (as sent to the provider)."""
    merged = {**config.default_params, **call_params}
    merged.setdefault("model", config.model)
    return merged


def build_response_format(
    response_model: type[BaseModel],
    mode: StructuredMode,
    *,
    schema_name: str = "response",
) -> dict[str, Any] | None:
    if mode == "none":
        return None
    if mode == "json_object":
        return {"type": "json_object"}
    schema = response_model.model_json_schema()
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True,
        },
    }


def parse_structured_content(content: str) -> StructuredParseResult:
    return parse_risk_list(content)
