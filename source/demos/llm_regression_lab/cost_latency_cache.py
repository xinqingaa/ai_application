"""Observe cost, latency, and cache boundaries from Harness records.

运行方式：
    uv run python source/demos/llm_regression_lab/cost_latency_cache.py

默认调用真实模型、不写磁盘。这个 demo 的重点不是得到“最便宜”的答案，
而是看懂真实 usage、估算成本、延迟和缓存 key 如何影响需求评审助手的调用治理。
若需要离线排查或稳定复现 cache 行为，把 USE_REAL_LLM 改为 False。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from llm_core import (
    CacheEvent,
    CacheKeyParts,
    CacheStats,
    DegradationPolicy,
    HarnessCase,
    HarnessRunConfig,
    HarnessRunRecord,
    InMemoryLLMCache,
    LLMCallingHarness,
    LLMClient,
    ReliableLLMService,
    RetryPolicy,
    build_cache_key,
    format_records_table,
    format_summary,
)
from llm_core.config import LLMResponse, TokenUsage
from llm_core.schemas.parse import parse_risk_list
from llm_core.structured import StructuredLLMResponse


DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]

# 课程主路径默认 True；fake 仅用于离线排查和稳定复现 cache 行为。
USE_REAL_LLM = True

PRIMARY_CONFIG_REF = "chat.dev_chat"
FALLBACK_CONFIG_REF = "chat.fallback_chat"

# 学习型缓存开关：只做进程内 exact-match cache，不写磁盘、不跨用户复用。
ENABLE_CACHE = True

# 修改这个值可以观察“证据上下文变化后必须 cache miss”。
CONTEXT_FINGERPRINT = "ctx-review-rules-v1"


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
        run_name="cost_latency_real" if USE_REAL_LLM else "cost_latency_fake",
        config_ref=PRIMARY_CONFIG_REF,
        retry_policy=RetryPolicy(max_attempts=1),
        degradation_policy=DegradationPolicy(fallback_config_refs=(FALLBACK_CONFIG_REF,)),
        structured_mode="json_object",
        temperature=0,
    )
    cache: InMemoryLLMCache[HarnessRunRecord] = InMemoryLLMCache()

    cold_records, cold_events = _run_with_cache(
        cases,
        harness=harness,
        config=config,
        cache=cache,
        context_fingerprint=CONTEXT_FINGERPRINT,
    )
    repeat_records, repeat_events = _run_with_cache(
        cases,
        harness=harness,
        config=config,
        cache=cache,
        context_fingerprint=CONTEXT_FINGERPRINT,
    )
    changed_context_records, changed_context_events = _run_with_cache(
        cases,
        harness=harness,
        config=config,
        cache=cache,
        context_fingerprint="ctx-review-rules-v2",
    )

    print("\n[cost_latency]")
    print(f"  [run_name] {config.run_name}")
    print(f"  [mode] {'real_llm' if USE_REAL_LLM else 'fake'}")
    print(f"  [cache] {'enabled' if ENABLE_CACHE else 'disabled'}")
    print("  [price_source] learning estimate, not provider bill")

    print("\n[records:cold]")
    print(format_records_table(cold_records))

    print("\n[summary:cold]")
    for line in format_summary(_summary(cold_records)).splitlines():
        print(f"  {line}")

    print("\n[cache_rounds]")
    _print_cache_stats("cold", CacheStats.from_events(cold_events))
    _print_cache_stats("repeat_same_input", CacheStats.from_events(repeat_events))
    _print_cache_stats("changed_context", CacheStats.from_events(changed_context_events))

    print("\n[records:repeat]")
    print(format_records_table(repeat_records))

    print("\n[budget_shape]")
    _print_budget_shape(_summary(cold_records))

    print("\n[lesson]")
    print("  成本下降只说明调用更省；是否可信仍要看引用、结构化校验和后续 eval。")
    print("  context_fingerprint 变化后 cache miss，是为了避免把旧证据下的结论复用到新材料。")


def find_and_load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _real_service() -> ReliableLLMService:
    return ReliableLLMService(LLMClient.from_default_config())


def _run_with_cache(
    cases: list[HarnessCase],
    *,
    harness: LLMCallingHarness,
    config: HarnessRunConfig,
    cache: InMemoryLLMCache[HarnessRunRecord],
    context_fingerprint: str,
) -> tuple[list[HarnessRunRecord], list[CacheEvent]]:
    records: list[HarnessRunRecord] = []
    events: list[CacheEvent] = []
    for case in cases:
        cache_key = _cache_key_for(case, config, context_fingerprint)
        cached = cache.get(cache_key) if ENABLE_CACHE else None
        if cached is not None:
            records.append(replace(cached, cache_hit=True))
            events.append(
                CacheEvent(
                    case_id=case.case_id,
                    hit=True,
                    cache_key=cache_key,
                    saved_tokens=cached.total_tokens or 0,
                    saved_estimated_cost=cached.estimated_cost,
                    saved_latency_ms=cached.latency_ms,
                )
            )
            continue

        record = harness.run_case(case, config)
        cache.set(cache_key, record)
        records.append(record)
        events.append(CacheEvent(case_id=case.case_id, hit=False, cache_key=cache_key))
    return records, events


def _cache_key_for(case: HarnessCase, config: HarnessRunConfig, context_fingerprint: str) -> str:
    return build_cache_key(
        CacheKeyParts(
            config_ref=config.config_ref,
            model="fake-model" if not USE_REAL_LLM else None,
            messages=case.messages,
            prompt_id="review.risk_review",
            prompt_version="v4",
            structured_mode=config.structured_mode,
            schema_version="review_risk_list@1",
            temperature=config.temperature,
            context_fingerprint=context_fingerprint,
        )
    )


def _summary(records: list[HarnessRunRecord]):
    from llm_core import HarnessSummary

    return HarnessSummary.from_records(records)


def _print_cache_stats(label: str, stats: CacheStats) -> None:
    cost = "-" if stats.saved_estimated_cost is None else f"${stats.saved_estimated_cost:.6f}"
    print(
        "  "
        f"{label}: hit_rate={stats.hit_rate:.0%}, "
        f"hits={stats.hit_count}, misses={stats.miss_count}, "
        f"saved_tokens={stats.saved_tokens}, saved_cost={cost}, "
        f"saved_latency_ms={stats.saved_latency_ms:.1f}"
    )


def _print_budget_shape(summary: Any) -> None:
    single_call_cost = summary.estimated_total_cost or 0
    print(f"  single_structured_call: calls={summary.total}, estimated_cost=${single_call_cost:.6f}")
    print(f"  context_enriched_call: calls={summary.total}, estimated_cost≈${single_call_cost * 1.4:.6f}")
    print(f"  multi_step_review: calls≈{summary.total * 3}, estimated_cost≈${single_call_cost * 3:.6f}")
    print("  这里只是预算形状估算；真实 RAG / Agent 链路进入后续课程。")


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
    outcomes: list[tuple[str, TokenUsage]]

    def chat(self, messages: list[dict[str, str]], config_ref: str, **kwargs: Any) -> LLMResponse:
        content, usage = self.outcomes.pop(0)
        return LLMResponse(
            content=content,
            raw_response={"simulated": True},
            usage=usage,
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
            (
                '{"risks":[{"title":"售后接口参数风险","category":"api","level":"high","rationale":"需要确认售后接口 v2 必填参数和错误码。"}]}',
                TokenUsage(prompt_tokens=1_200, completion_tokens=220, total_tokens=1_420),
            ),
            (
                '{"risks":[{"title":"优惠叠加规则风险","category":"state_flow","level":"medium","rationale":"需要确认会员折扣与优惠券优先级。"}]}',
                TokenUsage(prompt_tokens=1_350, completion_tokens=260, total_tokens=1_610),
            ),
            (
                '{"risks":[{"title":"发票历史记录权限风险","category":"exception","level":"medium","rationale":"需要确认历史抬头复用时的权限和异常输入。"}]}',
                TokenUsage(prompt_tokens=1_100, completion_tokens=210, total_tokens=1_310),
            ),
            (
                '{"risks":[{"title":"售后接口参数风险","category":"api","level":"high","rationale":"上下文变化后需要重新确认售后接口。"}]}',
                TokenUsage(prompt_tokens=1_260, completion_tokens=230, total_tokens=1_490),
            ),
            (
                '{"risks":[{"title":"优惠叠加规则风险","category":"state_flow","level":"medium","rationale":"上下文变化后需要重新确认优惠优先级。"}]}',
                TokenUsage(prompt_tokens=1_410, completion_tokens=280, total_tokens=1_690),
            ),
            (
                '{"risks":[{"title":"发票历史记录权限风险","category":"exception","level":"medium","rationale":"上下文变化后需要重新确认权限边界。"}]}',
                TokenUsage(prompt_tokens=1_160, completion_tokens=220, total_tokens=1_380),
            ),
            (
                '{"risks":[{"title":"售后重复评审风险","category":"api","level":"low","rationale":"关闭缓存后重复售后样例会再次消耗模型调用。"}]}',
                TokenUsage(prompt_tokens=1_200, completion_tokens=210, total_tokens=1_410),
            ),
            (
                '{"risks":[{"title":"优惠重复评审风险","category":"state_flow","level":"low","rationale":"关闭缓存后重复优惠样例会再次消耗模型调用。"}]}',
                TokenUsage(prompt_tokens=1_350, completion_tokens=250, total_tokens=1_600),
            ),
            (
                '{"risks":[{"title":"发票重复评审风险","category":"exception","level":"low","rationale":"关闭缓存后重复发票样例会再次消耗模型调用。"}]}',
                TokenUsage(prompt_tokens=1_100, completion_tokens=205, total_tokens=1_305),
            ),
        ]
    )


if __name__ == "__main__":
    main()
