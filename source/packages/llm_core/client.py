"""Unified LLM client entry point."""

from __future__ import annotations

from typing import Any, Optional

from llm_core.config import LLMResponse, ModelConfig
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.observability import print_call_log
from llm_core.providers.registry import ConfigRegistry


class LLMClient:
    def __init__(self, registry: ConfigRegistry) -> None:
        self._registry = registry

    @classmethod
    def from_default_config(cls) -> LLMClient:
        return cls(ConfigRegistry.default())

    def get_config(self, config_ref: str) -> ModelConfig:
        return self._registry.get_config(config_ref)

    def chat(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        config = self._registry.get_config(config_ref)
        if config.role != "chat":
            raise LLMError(
                code=LLMErrorCode.CAPABILITY_MISMATCH,
                message=f"{config_ref} 的 role 是 {config.role}，不能用于 chat",
                config_ref=config_ref,
            )

        params: dict[str, Any] = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(kwargs)

        provider = self._registry.get_provider(config.provider)
        response = provider.chat(messages, config, **params)

        if debug:
            merged = {**config.default_params, **params, "model": config.model}
            print_call_log(messages, merged, response)

        return response
