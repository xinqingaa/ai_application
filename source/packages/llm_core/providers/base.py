"""Provider protocol definitions."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol

from llm_core.config import LLMResponse, ModelConfig
from llm_core.streaming import LLMStreamEvent


class ChatProvider(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
        **params: Any,
    ) -> LLMResponse:
        ...

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
        **params: Any,
    ) -> Iterator[LLMStreamEvent]:
        ...
