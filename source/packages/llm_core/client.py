"""Unified LLM client entry point."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional

from pydantic import BaseModel

from llm_core.config import LLMResponse, ModelConfig
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.observability import demo_log, render_call_log
from llm_core.providers.registry import ConfigRegistry
from llm_core.schemas.review import ReviewRiskList
from llm_core.streaming import LLMStreamEvent, StreamEventBuilder
from llm_core.structured import (
    StructuredLLMResponse,
    StructuredMode,
    build_response_format,
    merge_chat_request_params,
    parse_structured_content,
)


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
            render_call_log(demo_log, messages, merged, response)

        return response

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[LLMStreamEvent]:
        config = self._registry.get_config(config_ref)
        run_id = kwargs.pop("run_id", None)
        if config.role != "chat":
            builder = StreamEventBuilder(run_id=run_id)
            yield builder.event(
                "error",
                code=LLMErrorCode.CAPABILITY_MISMATCH.value,
                message=f"{config_ref} 的 role 是 {config.role}，不能用于 stream_chat",
                config_ref=config_ref,
            )
            yield builder.event("done", config_ref=config_ref)
            return
        if config.capabilities.streaming is False:
            builder = StreamEventBuilder(run_id=run_id)
            yield builder.event(
                "error",
                code=LLMErrorCode.CAPABILITY_MISMATCH.value,
                message=f"{config_ref} 未声明支持 streaming",
                config_ref=config_ref,
            )
            yield builder.event("done", config_ref=config_ref)
            return

        params: dict[str, Any] = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(kwargs)
        params["_run_id"] = run_id

        provider = self._registry.get_provider(config.provider)
        yield from provider.stream_chat(messages, config, **params)

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        *,
        response_model: type[BaseModel] = ReviewRiskList,
        structured_mode: StructuredMode = "json_schema",
        schema_name: str = "review_risk_list",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> StructuredLLMResponse:
        """Chat with optional response_format, then parse content into ReviewRisk list."""
        config = self._registry.get_config(config_ref)
        call_params: dict[str, Any] = dict(kwargs)
        response_format = build_response_format(
            response_model,
            structured_mode,
            schema_name=schema_name,
        )
        if response_format is not None:
            call_params["response_format"] = response_format
        if temperature is not None:
            call_params["temperature"] = temperature
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens

        request_params = merge_chat_request_params(config, call_params)

        llm = self.chat(
            messages,
            config_ref,
            debug=debug,
            **call_params,
        )
        parse = parse_structured_content(llm.content)
        return StructuredLLMResponse(
            llm=llm,
            parse=parse,
            structured_mode=structured_mode,
            request_params=request_params,
        )
