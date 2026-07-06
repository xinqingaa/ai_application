"""Retry and degradation policies for reliable LLM calls."""

from __future__ import annotations

from dataclasses import dataclass

from llm_core.errors import LLMErrorCode

DEFAULT_RETRYABLE_ERRORS = (
    LLMErrorCode.RATE_LIMIT,
    LLMErrorCode.TIMEOUT,
    LLMErrorCode.PROVIDER_ERROR,
)

DEFAULT_FALLBACK_ERRORS = (
    LLMErrorCode.RATE_LIMIT,
    LLMErrorCode.TIMEOUT,
    LLMErrorCode.CAPABILITY_MISMATCH,
    LLMErrorCode.PROVIDER_ERROR,
    LLMErrorCode.SCHEMA_PARSE,
    LLMErrorCode.EMPTY_RESPONSE,
)


@dataclass(frozen=True)
class RetryPolicy:
    """How many times one config_ref may be attempted before moving on."""

    max_attempts: int = 2
    retryable_errors: tuple[LLMErrorCode, ...] = DEFAULT_RETRYABLE_ERRORS
    backoff_seconds: float = 0.0

    def should_retry(self, code: LLMErrorCode, attempt_number: int) -> bool:
        return attempt_number < self.max_attempts and code in self.retryable_errors


@dataclass(frozen=True)
class DegradationPolicy:
    """Fallback model policy for one reliable call."""

    fallback_config_refs: tuple[str, ...] = ("chat.fallback_chat",)
    fallback_on_errors: tuple[LLMErrorCode, ...] = DEFAULT_FALLBACK_ERRORS

    def should_fallback(self, code: LLMErrorCode) -> bool:
        return bool(self.fallback_config_refs) and code in self.fallback_on_errors
