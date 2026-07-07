from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_core import (
    DegradationPolicy,
    HarnessCase,
    HarnessRunConfig,
    LLMCallingHarness,
    LLMError,
    LLMErrorCode,
    ReliableLLMService,
    RetryPolicy,
)
from llm_core.config import LLMResponse
from llm_core.config import TokenUsage
from llm_core.schemas.parse import parse_risk_list
from llm_core.structured import StructuredLLMResponse


def _response(content: str, config_ref: str, usage: TokenUsage | None = None) -> LLMResponse:
    return LLMResponse(
        content=content,
        raw_response=None,
        usage=usage,
        latency_ms=1.0,
        provider="fake",
        model="fake-model",
        config_ref=config_ref,
    )


@dataclass
class FakeClient:
    outcomes: list[Any]

    def chat(self, messages: list[dict[str, str]], config_ref: str, **kwargs: Any) -> LLMResponse:
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, LLMResponse):
            return outcome
        return _response(str(outcome), config_ref)

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        config_ref: str,
        **kwargs: Any,
    ) -> StructuredLLMResponse:
        response = self.chat(messages, config_ref, **kwargs)
        return StructuredLLMResponse(
            llm=response,
            parse=parse_risk_list(response.content),
            structured_mode="json_object",
            request_params={},
        )


def _case(case_id: str) -> HarnessCase:
    return HarnessCase.from_user_input(
        case_id=case_id,
        title=f"case {case_id}",
        user_input="订单详情页新增申请售后入口，请识别风险。",
    )


def test_harness_records_success_and_schema_failure() -> None:
    client = FakeClient(
        [
            '{"risks":[{"title":"接口参数风险","category":"api","level":"high","rationale":"需确认售后接口 v2 参数"}]}',
            "not json",
        ]
    )
    harness = LLMCallingHarness(ReliableLLMService(client))  # type: ignore[arg-type]

    records, summary = harness.run_cases(
        [_case("S1"), _case("S2")],
        HarnessRunConfig(
            run_name="unit",
            retry_policy=RetryPolicy(max_attempts=1),
            degradation_policy=DegradationPolicy(fallback_config_refs=()),
        ),
    )

    assert records[0].ok
    assert records[0].parse_ok is True
    assert records[0].risk_count == 1
    assert not records[1].ok
    assert records[1].error_code == LLMErrorCode.SCHEMA_PARSE
    assert summary.total == 2
    assert summary.success_count == 1
    assert summary.failed_count == 1
    assert summary.parse_success_count == 1
    assert summary.error_counts == {"schema_parse": 1}


def test_harness_keeps_reliability_attempts_and_degraded_flag() -> None:
    client = FakeClient(
        [
            LLMError(LLMErrorCode.TIMEOUT, "primary timeout", config_ref="chat.dev_chat"),
            '{"risks":[{"title":"fallback 风险","category":"interaction","level":"medium","rationale":"需确认入口展示条件"}]}',
        ]
    )
    harness = LLMCallingHarness(ReliableLLMService(client))  # type: ignore[arg-type]

    records, summary = harness.run_cases(
        [_case("S1")],
        HarnessRunConfig(
            run_name="fallback",
            retry_policy=RetryPolicy(max_attempts=1),
            degradation_policy=DegradationPolicy(fallback_config_refs=("chat.fallback_chat",)),
        ),
    )

    assert records[0].ok
    assert records[0].config_ref == "chat.fallback_chat"
    assert records[0].attempt_count == 2
    assert records[0].degraded is True
    assert summary.degraded_count == 1


def test_harness_summary_includes_tokens_cost_and_latency() -> None:
    client = FakeClient(
        [
            _response(
                '{"risks":[{"title":"接口风险","category":"api","level":"high","rationale":"需确认接口参数"}]}',
                "chat.dev_chat",
                TokenUsage(prompt_tokens=1_000, completion_tokens=500, total_tokens=1_500),
            )
        ]
    )
    harness = LLMCallingHarness(ReliableLLMService(client))  # type: ignore[arg-type]

    records, summary = harness.run_cases(
        [_case("S1")],
        HarnessRunConfig(
            run_name="cost",
            retry_policy=RetryPolicy(max_attempts=1),
            degradation_policy=DegradationPolicy(fallback_config_refs=()),
        ),
    )

    assert records[0].prompt_tokens == 1_000
    assert records[0].completion_tokens == 500
    assert records[0].total_tokens == 1_500
    assert records[0].estimated_cost == 0.00045
    assert summary.prompt_tokens == 1_000
    assert summary.completion_tokens == 500
    assert summary.total_tokens == 1_500
    assert summary.estimated_total_cost == 0.00045
