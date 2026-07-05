"""Compare retry and fallback behavior for 02_llm/06.

运行方式：
    uv run python source/demos/02_reliability_errors/reliability_compare.py

本 demo 默认使用本地模拟，不消耗模型额度。若想观察真实模型调用，把
USE_REAL_LLM 改为 True；仍然运行同一条命令。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llm_core import (
    DegradationPolicy,
    LLMClient,
    LLMError,
    LLMErrorCode,
    ReliableCallResult,
    ReliableLLMService,
    RetryPolicy,
)
from llm_core.config import LLMResponse
from llm_core.schemas.parse import parse_risk_list
from llm_core.structured import StructuredLLMResponse

# 默认案例：
# - "timeout_then_success"：第一次超时，第二次重试成功。
# - "primary_timeout_then_fallback"：主模型连续超时，切到 fallback 成功。
# - "auth_error"：鉴权失败，不重试、不降级。
# - "schema_failure"：模拟结构化解析失败，本节先观察失败可见。
DEFAULT_CASE = "timeout_then_success"

# 是否调用真实模型。默认 False，避免学习 demo 一运行就消耗额度。
USE_REAL_LLM = False

# 是否打印发送给模型的 messages。真实调用排查时再打开。
PRINT_MESSAGES = False

# 是否打印每次 attempt 的详细错误。学习 06 时建议保持 True。
PRINT_ATTEMPT_DETAIL = True

# 是否同时跑一组“无重试”对照，帮助观察 retry 的价值。
COMPARE_WITH_NO_RETRY = True

PRIMARY_CONFIG_REF = "chat.dev_chat"
FALLBACK_CONFIG_REF = "chat.fallback_chat"

MESSAGES = [
    {
        "role": "system",
        "content": "你是需求评审助手，请用简短中文回答。",
    },
    {
        "role": "user",
        "content": "订单详情页新增申请售后入口，研发侧最需要先确认什么？",
    },
]


def main() -> None:
    if USE_REAL_LLM:
        result = _run_real_call()
        _print_case("real_llm", "真实模型调用：观察可靠调用外壳如何记录 attempt。")
        _print_messages()
        _print_result(result)
        _print_lesson("真实调用通常不会稳定触发失败；06 更关注失败出现时 report 是否能解释。")
        return

    if COMPARE_WITH_NO_RETRY:
        _run_case(DEFAULT_CASE, compare_no_retry=True)
    _run_case(DEFAULT_CASE, compare_no_retry=False)


def _run_case(case_id: str, *, compare_no_retry: bool) -> None:
    case = _make_case(case_id)
    service = ReliableLLMService(case.client)  # type: ignore[arg-type]
    retry_policy = RetryPolicy(max_attempts=1 if compare_no_retry else case.max_attempts)
    degradation_policy = DegradationPolicy(fallback_config_refs=case.fallback_config_refs)
    label = f"{case_id} / {'no_retry' if compare_no_retry else 'reliable'}"

    _print_case(label, case.description)
    _print_call_plan(retry_policy, degradation_policy)
    _print_messages()
    if case_id == "schema_failure":
        result = service.chat_structured(
            MESSAGES,
            PRIMARY_CONFIG_REF,
            retry_policy=retry_policy,
            degradation_policy=degradation_policy,
            structured_mode="json_object",
            temperature=0,
        )
    else:
        result = service.chat(
            MESSAGES,
            PRIMARY_CONFIG_REF,
            retry_policy=retry_policy,
            degradation_policy=degradation_policy,
            temperature=0,
        )
    _print_result(result)
    _print_lesson(case.lesson)


def _run_real_call() -> ReliableCallResult[LLMResponse]:
    client = LLMClient.from_default_config()
    service = ReliableLLMService(client)
    return service.chat(
        MESSAGES,
        PRIMARY_CONFIG_REF,
        retry_policy=RetryPolicy(max_attempts=2),
        degradation_policy=DegradationPolicy(fallback_config_refs=(FALLBACK_CONFIG_REF,)),
        temperature=0,
    )


@dataclass
class DemoCase:
    client: "FakeClient"
    description: str
    lesson: str
    max_attempts: int = 2
    fallback_config_refs: tuple[str, ...] = ()


class FakeClient:
    def __init__(self, outcomes: list[Any]) -> None:
        self._outcomes = outcomes

    def chat(self, messages: list[dict[str, str]], config_ref: str, **kwargs: Any) -> LLMResponse:
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return LLMResponse(
            content=str(outcome),
            raw_response={"simulated": True},
            usage=None,
            latency_ms=1.0,
            provider="fake",
            model="fake-model",
            config_ref=config_ref,
        )

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


def _make_case(case_id: str) -> DemoCase:
    if case_id == "timeout_then_success":
        return DemoCase(
            client=FakeClient(
                [
                    LLMError(LLMErrorCode.TIMEOUT, "第一次请求超时", config_ref=PRIMARY_CONFIG_REF),
                    "先确认入口展示条件、售后接口 v2 必填参数、重复申请拦截和三端一致性。",
                ]
            ),
            description="主模型第一次超时，第二次重试成功。",
            lesson="可重试错误不等于任务失败；关键是限制次数并记录每次 attempt。",
        )
    if case_id == "primary_timeout_then_fallback":
        return DemoCase(
            client=FakeClient(
                [
                    LLMError(LLMErrorCode.TIMEOUT, "主模型第一次超时", config_ref=PRIMARY_CONFIG_REF),
                    LLMError(LLMErrorCode.TIMEOUT, "主模型第二次超时", config_ref=PRIMARY_CONFIG_REF),
                    "fallback 返回：先确认 after_sale_eligible、v2 参数、错误码和弱网跳转上下文。",
                ]
            ),
            description="主模型达到重试上限后，降级到 fallback 模型成功。",
            lesson="降级不是静默成功；report.degraded=True 必须暴露给后续 trace、成本和质量判断。",
            fallback_config_refs=(FALLBACK_CONFIG_REF,),
        )
    if case_id == "auth_error":
        return DemoCase(
            client=FakeClient([LLMError(LLMErrorCode.AUTH, "API key 无效", config_ref=PRIMARY_CONFIG_REF)]),
            description="鉴权失败：不重试、不降级，直接失败可见。",
            lesson="不可恢复错误应快速失败；继续重试只会浪费时间并掩盖配置问题。",
            max_attempts=3,
            fallback_config_refs=(FALLBACK_CONFIG_REF,),
        )
    if case_id == "schema_failure":
        return DemoCase(
            client=FakeClient(["不是合法 JSON"]),
            description="普通 chat 返回了文本；结构化失败应在 reliable structured 调用里暴露。",
            lesson="本 case 只提醒：parse=fail 不是模型调用成功，06 会把它归入可靠性报告。",
        )
    available = "timeout_then_success, primary_timeout_then_fallback, auth_error, schema_failure"
    raise ValueError(f"未知 DEFAULT_CASE={case_id!r}，可选：{available}")


def _print_case(case_id: str, description: str) -> None:
    print("\n[case]")
    print(f"  [id] {case_id}")
    print(f"  [description] {description}")


def _print_call_plan(retry_policy: RetryPolicy, degradation_policy: DegradationPolicy) -> None:
    print("\n[call_plan]")
    print(f"  [primary] {PRIMARY_CONFIG_REF}")
    print(f"  [fallbacks] {_join_or_dash(degradation_policy.fallback_config_refs)}")
    print(f"  [max_attempts_per_config] {retry_policy.max_attempts}")
    print(f"  [retryable_errors] {_join_or_dash(error.value for error in retry_policy.retryable_errors)}")
    print(f"  [fallback_on_errors] {_join_or_dash(error.value for error in degradation_policy.fallback_on_errors)}")


def _print_messages() -> None:
    if not PRINT_MESSAGES:
        return
    print("\n[messages]")
    for index, message in enumerate(MESSAGES, start=1):
        print(f"  [{index}] role={message['role']}")
        print(f"      {message['content']}")


def _print_result(result: ReliableCallResult[Any]) -> None:
    print("\n[attempts]")
    for attempt in result.report.attempts:
        if attempt.ok:
            print(
                f"  [{attempt.attempt_number}] config={attempt.config_ref} "
                f"status=success latency_ms={attempt.latency_ms:.1f}"
            )
        else:
            message = f" message={attempt.message}" if PRINT_ATTEMPT_DETAIL and attempt.message else ""
            print(
                f"  [{attempt.attempt_number}] config={attempt.config_ref} "
                f"status=failed code={attempt.error_code.value if attempt.error_code else 'unknown'}{message}"
            )

    print("\n[final]")
    if result.ok and result.output is not None:
        answer = getattr(result.output, "content", None)
        if answer is None and hasattr(result.output, "llm"):
            answer = result.output.llm.content
        print("  [status] success")
        print(f"  [final_config] {result.report.final_config_ref}")
        print(f"  [degraded] {str(result.report.degraded).lower()}")
        print(f"  [answer] {answer}")
    else:
        print("  [status] failed")
        print(f"  [final_error] {result.report.final_error_code.value if result.report.final_error_code else 'unknown'}")
        print(f"  [message] {result.report.final_message or '—'}")


def _print_lesson(text: str) -> None:
    print("\n[lesson]")
    print(f"  {text}")


def _join_or_dash(values: Any) -> str:
    items = [str(value) for value in values]
    return ", ".join(items) if items else "—"


if __name__ == "__main__":
    # 保持脚本可从任意工作目录运行时更容易定位自身；不写文件。
    _ = Path(__file__).resolve()
    main()
