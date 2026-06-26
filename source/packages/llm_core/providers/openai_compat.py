"""OpenAI-compatible chat provider."""

from __future__ import annotations

import os
import time
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from llm_core.config import LLMResponse, ModelConfig, TokenUsage
from llm_core.errors import LLMError, LLMErrorCode


class OpenAICompatProvider:
    name = "openai_compat"

    def chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
        **params: Any,
    ) -> LLMResponse:
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

        client = OpenAI(**client_kwargs)
        request_params = {**config.default_params, **params}
        request_params.setdefault("model", config.model)
        request_params["messages"] = messages

        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(**request_params)
        except RateLimitError as exc:
            raise LLMError(
                code=LLMErrorCode.RATE_LIMIT,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            ) from exc
        except APITimeoutError as exc:
            raise LLMError(
                code=LLMErrorCode.TIMEOUT,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            ) from exc
        except APIConnectionError as exc:
            raise LLMError(
                code=LLMErrorCode.TIMEOUT,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            ) from exc
        except APIStatusError as exc:
            code = LLMErrorCode.AUTH if exc.status_code in (401, 403) else LLMErrorCode.PROVIDER_ERROR
            raise LLMError(
                code=code,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            ) from exc
        except Exception as exc:
            raise LLMError(
                code=LLMErrorCode.UNKNOWN,
                message=str(exc),
                config_ref=config.config_ref,
                raw=exc,
            ) from exc

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
