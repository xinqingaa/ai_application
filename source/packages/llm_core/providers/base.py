"""Provider protocol definitions."""

from __future__ import annotations

from typing import Any, Protocol

from llm_core.config import LLMResponse, ModelConfig


class ChatProvider(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
        **params: Any,
    ) -> LLMResponse:
        ...
