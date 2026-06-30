"""OpenAI-compatible chat provider."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from llm_core.config import LLMResponse, ModelConfig, TokenUsage
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.streaming import LLMStreamEvent, StreamEventBuilder


class OpenAICompatProvider:
    name = "openai_compat"

    def _client_for_config(self, config: ModelConfig) -> OpenAI:
        api_key = os.environ.get(config.api_key_env, "").strip()
        if not api_key:
            raise LLMError(
                code=LLMErrorCode.AUTH,
                message=f"环境变量 {config.api_key_env} 未配置",
                config_ref=config.config_ref,
            )

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if config.base_url:
            client_kwargs["base_url"] = config.base_url
        return OpenAI(**client_kwargs)

    def _map_exception(self, exc: Exception, config: ModelConfig) -> LLMError:
        if isinstance(exc, RateLimitError):
            return LLMError(
                code=LLMErrorCode.RATE_LIMIT,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            )
        if isinstance(exc, (APITimeoutError, APIConnectionError)):
            return LLMError(
                code=LLMErrorCode.TIMEOUT,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            )
        if isinstance(exc, APIStatusError):
            code = LLMErrorCode.AUTH if exc.status_code in (401, 403) else LLMErrorCode.PROVIDER_ERROR
            return LLMError(
                code=code,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            )
        if isinstance(exc, LLMError):
            return exc
        return LLMError(
            code=LLMErrorCode.UNKNOWN,
            message=str(exc),
            config_ref=config.config_ref,
            raw=exc,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
        **params: Any,
    ) -> LLMResponse:
        client = self._client_for_config(config)
        request_params = {**config.default_params, **params}
        request_params.setdefault("model", config.model)
        request_params["messages"] = messages

        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(**request_params)
        except Exception as exc:
            raise self._map_exception(exc, config) from exc

        latency_ms = (time.perf_counter() - t0) * 1000
        content = ""
        if resp.choices:
            content = resp.choices[0].message.content or ""

        usage = None
        if resp.usage:
            usage = TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )

        return LLMResponse(
            content=content,
            raw_response=resp,
            usage=usage,
            latency_ms=latency_ms,
            provider=self.name,
            model=resp.model or config.model,
            config_ref=config.config_ref,
        )

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
        **params: Any,
    ) -> Iterator[LLMStreamEvent]:
        raw_run_id = params.pop("_run_id", None)
        run_id = str(raw_run_id) if raw_run_id else ""
        builder = StreamEventBuilder(run_id=run_id or None)
        model_name = config.model
        content_parts: list[str] = []

        yield builder.event(
            "message_start",
            provider=self.name,
            model=model_name,
            config_ref=config.config_ref,
        )

        try:
            client = self._client_for_config(config)
            request_params = {**config.default_params, **params}
            request_params.setdefault("model", config.model)
            request_params["messages"] = messages
            request_params["stream"] = True

            stream = client.chat.completions.create(**request_params)
            for chunk in stream:
                model_name = getattr(chunk, "model", None) or model_name
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue
                content_parts.append(delta)
                yield builder.event(
                    "token",
                    delta=delta,
                    provider=self.name,
                    model=model_name,
                    config_ref=config.config_ref,
                )

            yield builder.event(
                "message_done",
                content="".join(content_parts),
                provider=self.name,
                model=model_name,
                config_ref=config.config_ref,
                include_latency=True,
            )
        except Exception as exc:
            error = self._map_exception(exc, config)
            yield builder.event(
                "error",
                code=error.code.value,
                message=error.message,
                provider=self.name,
                model=model_name,
                config_ref=config.config_ref,
                include_latency=True,
            )
        finally:
            yield builder.event(
                "done",
                provider=self.name,
                model=model_name,
                config_ref=config.config_ref,
                include_latency=True,
            )
