from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_core import (
    DegradationPolicy,
    LLMError,
    LLMErrorCode,
    ReliableLLMService,
    RetryPolicy,
)
from llm_core.config import LLMResponse
from llm_core.schemas.parse import parse_risk_list
from llm_core.structured import StructuredLLMResponse


def _response(content: str, config_ref: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        raw_response=None,
        usage=None,
        latency_ms=1.0,
        provider="fake",
        model="fake-model",
        config_ref=config_ref,
    )


@dataclass
class FakeClient:
    outcomes: list[Any]

    def __post_init__(self) -> None:
        self.calls: list[str] = []

    def chat(self, messages: list[dict[str, str]], config_ref: str, **kwargs: Any) -> LLMResponse:
        self.calls.append(config_ref)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, str):
            return _response(outcome, config_ref)
        return outcome

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        **kwargs: Any,
    ) -> StructuredLLMResponse:
        self.calls.append(config_ref)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        llm = _response(str(outcome), config_ref)
        return StructuredLLMResponse(
            llm=llm,
            parse=parse_risk_list(str(outcome)),
            structured_mode="json_object",
            request_params={},
        )


def test_reliable_chat_retries_timeout_then_success() -> None:
    client = FakeClient(
        [
            LLMError(LLMErrorCode.TIMEOUT, "first timeout", config_ref="chat.dev_chat"),
            "ok",
        ]
    )
    service = ReliableLLMService(client)  # type: ignore[arg-type]

    result = service.chat(
        [{"role": "user", "content": "hello"}],
        "chat.dev_chat",
        retry_policy=RetryPolicy(max_attempts=2),
        degradation_policy=DegradationPolicy(fallback_config_refs=()),
    )

    assert result.ok
    assert result.output is not None
    assert result.output.content == "ok"
    assert client.calls == ["chat.dev_chat", "chat.dev_chat"]
    assert result.report.attempt_count == 2
    assert result.report.degraded is False


def test_reliable_chat_does_not_retry_auth_error() -> None:
    client = FakeClient([LLMError(LLMErrorCode.AUTH, "bad key", config_ref="chat.dev_chat")])
    service = ReliableLLMService(client)  # type: ignore[arg-type]

    result = service.chat(
        [{"role": "user", "content": "hello"}],
        "chat.dev_chat",
        retry_policy=RetryPolicy(max_attempts=3),
        degradation_policy=DegradationPolicy(fallback_config_refs=("chat.fallback_chat",)),
    )

    assert not result.ok
    assert result.error is not None
    assert result.error.code == LLMErrorCode.AUTH
    assert client.calls == ["chat.dev_chat"]
    assert result.report.attempt_count == 1


def test_reliable_chat_falls_back_after_primary_retries() -> None:
    client = FakeClient(
        [
            LLMError(LLMErrorCode.TIMEOUT, "timeout 1", config_ref="chat.dev_chat"),
            LLMError(LLMErrorCode.TIMEOUT, "timeout 2", config_ref="chat.dev_chat"),
            "fallback ok",
        ]
    )
    service = ReliableLLMService(client)  # type: ignore[arg-type]

    result = service.chat(
        [{"role": "user", "content": "hello"}],
        "chat.dev_chat",
        retry_policy=RetryPolicy(max_attempts=2),
        degradation_policy=DegradationPolicy(fallback_config_refs=("chat.fallback_chat",)),
    )

    assert result.ok
    assert result.output is not None
    assert result.output.config_ref == "chat.fallback_chat"
    assert result.report.degraded is True
    assert client.calls == ["chat.dev_chat", "chat.dev_chat", "chat.fallback_chat"]


def test_reliable_structured_treats_parse_failure_as_schema_error() -> None:
    client = FakeClient(["not json"])
    service = ReliableLLMService(client)  # type: ignore[arg-type]

    result = service.chat_structured(
        [{"role": "user", "content": "return risks"}],
        "chat.structured_chat",
        retry_policy=RetryPolicy(max_attempts=1),
        degradation_policy=DegradationPolicy(fallback_config_refs=()),
        structured_mode="json_object",
    )

    assert not result.ok
    assert result.error is not None
    assert result.error.code == LLMErrorCode.SCHEMA_PARSE
    assert result.report.final_error_code == LLMErrorCode.SCHEMA_PARSE
    assert result.report.attempts[0].error_code == LLMErrorCode.SCHEMA_PARSE


def test_empty_text_response_is_a_visible_failure() -> None:
    client = FakeClient([""])
    service = ReliableLLMService(client)  # type: ignore[arg-type]

    result = service.chat(
        [{"role": "user", "content": "hello"}],
        "chat.dev_chat",
        retry_policy=RetryPolicy(max_attempts=1),
        degradation_policy=DegradationPolicy(fallback_config_refs=()),
    )

    assert not result.ok
    assert result.error is not None
    assert result.error.code == LLMErrorCode.EMPTY_RESPONSE
