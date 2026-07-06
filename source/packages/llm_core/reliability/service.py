"""Reliability wrapper for LLM calls.

The base LLMClient keeps provider calls small and direct. This module is the
application-side shell that decides which errors are retryable, when fallback is
allowed, and how to report every attempt.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from llm_core.client import LLMClient
from llm_core.config import LLMResponse
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.reliability.policies import DegradationPolicy, RetryPolicy
from llm_core.reliability.report import ReliableCallAttempt, ReliableCallReport, ReliableCallResult
from llm_core.schemas.review import ReviewRiskList
from llm_core.structured import StructuredLLMResponse, StructuredMode

T = TypeVar("T")


Validator = Callable[[T], Optional[LLMError]]
CallFn = Callable[[str], T]


class ReliableLLMService:
    """Adds retry, fallback, and attempt reporting around LLMClient calls."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def chat(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        *,
        retry_policy: Optional[RetryPolicy] = None,
        degradation_policy: Optional[DegradationPolicy] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> ReliableCallResult[LLMResponse]:
        return self._run(
            primary_config_ref=config_ref,
            retry_policy=retry_policy or RetryPolicy(),
            degradation_policy=degradation_policy or DegradationPolicy(),
            call_fn=lambda active_ref: self._client.chat(
                messages,
                active_ref,
                temperature=temperature,
                max_tokens=max_tokens,
                debug=debug,
                **kwargs,
            ),
            validator=_validate_non_empty_response,
        )

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        *,
        response_model: type[BaseModel] = ReviewRiskList,
        structured_mode: StructuredMode = "json_schema",
        schema_name: str = "review_risk_list",
        retry_policy: Optional[RetryPolicy] = None,
        degradation_policy: Optional[DegradationPolicy] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> ReliableCallResult[StructuredLLMResponse]:
        return self._run(
            primary_config_ref=config_ref,
            retry_policy=retry_policy or RetryPolicy(),
            degradation_policy=degradation_policy or DegradationPolicy(),
            call_fn=lambda active_ref: self._client.chat_structured(
                messages,
                active_ref,
                response_model=response_model,
                structured_mode=structured_mode,
                schema_name=schema_name,
                temperature=temperature,
                max_tokens=max_tokens,
                debug=debug,
                **kwargs,
            ),
            validator=_validate_structured_response,
        )

    def _run(
        self,
        *,
        primary_config_ref: str,
        retry_policy: RetryPolicy,
        degradation_policy: DegradationPolicy,
        call_fn: CallFn[T],
        validator: Optional[Validator[T]] = None,
    ) -> ReliableCallResult[T]:
        attempts: list[ReliableCallAttempt] = []
        last_error: Optional[LLMError] = None
        config_refs = [primary_config_ref, *degradation_policy.fallback_config_refs]

        for config_index, active_ref in enumerate(config_refs):
            for attempt_number in range(1, retry_policy.max_attempts + 1):
                t0 = time.perf_counter()
                try:
                    output = call_fn(active_ref)
                    validation_error = validator(output) if validator else None
                    if validation_error is not None:
                        raise validation_error

                    attempts.append(
                        ReliableCallAttempt(
                            attempt_number=attempt_number,
                            config_ref=active_ref,
                            status="success",
                            latency_ms=(time.perf_counter() - t0) * 1000,
                        )
                    )
                    return ReliableCallResult(
                        output=output,
                        report=ReliableCallReport(
                            primary_config_ref=primary_config_ref,
                            final_config_ref=active_ref,
                            attempts=attempts,
                            degraded=active_ref != primary_config_ref,
                        ),
                    )
                except LLMError as exc:
                    last_error = exc
                    attempts.append(
                        ReliableCallAttempt(
                            attempt_number=attempt_number,
                            config_ref=active_ref,
                            status="failed",
                            latency_ms=(time.perf_counter() - t0) * 1000,
                            error_code=exc.code,
                            message=exc.message,
                        )
                    )

                    if retry_policy.should_retry(exc.code, attempt_number):
                        if retry_policy.backoff_seconds > 0:
                            time.sleep(retry_policy.backoff_seconds)
                        continue
                    break

            if last_error is None:
                break
            has_next_config = config_index < len(config_refs) - 1
            if not has_next_config or not degradation_policy.should_fallback(last_error.code):
                break

        final_error = last_error or LLMError(
            code=LLMErrorCode.UNKNOWN,
            message="可靠调用结束，但没有得到结果",
            config_ref=primary_config_ref,
        )
        return ReliableCallResult(
            output=None,
            error=final_error,
            report=ReliableCallReport(
                primary_config_ref=primary_config_ref,
                final_config_ref=None,
                attempts=attempts,
                degraded=any(attempt.config_ref != primary_config_ref for attempt in attempts),
                final_error_code=final_error.code,
                final_message=final_error.message,
            ),
        )


def _validate_non_empty_response(response: LLMResponse) -> Optional[LLMError]:
    if response.content.strip():
        return None
    return LLMError(
        code=LLMErrorCode.EMPTY_RESPONSE,
        message="模型返回为空",
        config_ref=response.config_ref,
        raw=response,
    )


def _validate_structured_response(response: StructuredLLMResponse) -> Optional[LLMError]:
    if response.parse.ok:
        return None
    stage = response.parse.error_stage or "unknown"
    code = LLMErrorCode.EMPTY_RESPONSE if stage == "empty" else LLMErrorCode.SCHEMA_PARSE
    return LLMError(
        code=code,
        message=response.parse.message or f"结构化解析失败: {stage}",
        config_ref=response.llm.config_ref,
        raw=response,
    )
