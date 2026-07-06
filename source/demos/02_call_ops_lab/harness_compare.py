"""Run a small local calling harness for 02_llm/07.

运行方式：
    uv run python source/demos/02_call_ops_lab/harness_compare.py

默认使用本地 fake client，不调用真实模型。若想观察真实模型在同一批 case
上的表现，把 USE_REAL_LLM 改为 True；仍然运行同一条命令。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from llm_core import (
    DegradationPolicy,
    HarnessCase,
    HarnessRunConfig,
    LLMCallingHarness,
    LLMClient,
    LLMError,
    LLMErrorCode,
    ReliableLLMService,
    RetryPolicy,
    format_records_table,
    format_summary,
)
from llm_core.config import LLMResponse
from llm_core.schemas.parse import parse_risk_list
from llm_core.structured import StructuredLLMResponse


DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]

# 默认 False，保证学习 demo 一运行不会消耗模型额度。
USE_REAL_LLM = True

# 真实模型路径下建议保持 True，便于看每条 case 的内容预览。
PRINT_RECORD_DETAIL = True

PRIMARY_CONFIG_REF = "chat.dev_chat"
FALLBACK_CONFIG_REF = "chat.fallback_chat"


def main() -> None:
    find_and_load_env()
    cases = [
        _case("S1", "售后入口", "订单详情页新增申请售后入口。"),
        _case("S2", "优惠券叠加", "结算页新增优惠券和会员折扣叠加。"),
        _case("S3", "发票改造", "企业发票抬头支持历史记录复用。"),
    ]
    service = _real_service() if USE_REAL_LLM else ReliableLLMService(_fake_client())  # type: ignore[arg-type]
    harness = LLMCallingHarness(service)
    config = HarnessRunConfig(
        run_name="risk_review_v4_real" if USE_REAL_LLM else "risk_review_v4_fake",
        config_ref=PRIMARY_CONFIG_REF,
        retry_policy=RetryPolicy(max_attempts=2 if USE_REAL_LLM else 1),
        degradation_policy=DegradationPolicy(fallback_config_refs=(FALLBACK_CONFIG_REF,)),
    )
    records, summary = harness.run_cases(cases, config)

    print("\n[harness]")
    print(f"  [run_name] {config.run_name}")
    print(f"  [cases] {len(cases)}")
    print(f"  [mode] {'real_llm' if USE_REAL_LLM else 'fake'}")
    print(f"  [structured] {str(config.structured).lower()}")

    print("\n[records]")
    print(format_records_table(records))

    print("\n[summary]")
    for line in format_summary(summary).splitlines():
        print(f"  {line}")

    if PRINT_RECORD_DETAIL:
        print("\n[detail]")
        for record in records:
            print(f"  [{record.case_id}] {record.content_preview or record.message or '-'}")

    print("\n[lesson]")
    print("  Harness 不判断答案是否绝对正确；它先把同一批 case 的调用结果记录成可对比事实。")


def find_and_load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _real_service() -> ReliableLLMService:
    return ReliableLLMService(LLMClient.from_default_config())


def _case(case_id: str, title: str, user_input: str) -> HarnessCase:
    return HarnessCase.from_user_input(
        case_id=case_id,
        title=title,
        user_input=user_input,
        system_prompt=(
            "你是需求评审助手。请只基于用户输入识别研发风险，"
            "用 JSON 对象回答，根字段必须是 risks。每个风险包含 title、"
            "category、level、rationale。category 只能使用 interaction、"
            "state_flow、api、multi_platform、exception、other；level 只能使用 high、medium、low。"
        ),
        expected_focus=("接口契约", "状态规则", "端侧展示"),
        tags=("risk_review",),
    )


@dataclass
class FakeClient:
    outcomes: list[Any]

    def chat(self, messages: list[dict[str, str]], config_ref: str, **kwargs: Any) -> LLMResponse:
        outcome = self.outcomes.pop(0)
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


def _fake_client() -> FakeClient:
    return FakeClient(
        [
            '{"risks":[{"title":"售后接口参数风险","category":"api","level":"high","rationale":"需要确认售后接口 v2 必填参数和错误码。"}]}',
            LLMError(LLMErrorCode.TIMEOUT, "主模型超时", config_ref="chat.dev_chat"),
            '{"risks":[{"title":"优惠叠加规则风险","category":"state_flow","level":"medium","rationale":"fallback 返回：需要确认会员折扣与优惠券优先级。"}]}',
            "不是合法 JSON",
            "fallback 仍然不是合法 JSON",
        ]
    )


if __name__ == "__main__":
    main()
