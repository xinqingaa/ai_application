"""
05_context_compare — compare context-building policies for one review case.

Run from the repo root:
    uv run python source/demos/02_context_lab/context_compare.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from llm_core import (
    BuiltContext,
    ContextBuildReport,
    ContextSource,
    LLMClient,
    build_review_context,
    get_context_policy,
    list_context_policy_names,
)
from llm_core.errors import LLMError
from llm_core.prompts import get_prompt, render_prompt

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
CASE_PATH = DEMO_DIR / "context_cases.json"

# 学习期实验开关。
# 真实项目里，这类值通常来自配置文件、环境变量、数据库配置或后台管理页；
# 本 demo 为了让你看清“配置如何影响上下文装配”，先集中放在脚本顶部。

# 选择本次使用的上下文策略。
# 常用值：
# - "evidence_first"：默认推荐，优先保留可引用证据，适合风险审查。
# - "tight_budget"：模拟上下文预算很紧，观察压缩和丢弃。
# - "minimal"：只保留当前需求，不带证据，观察无上下文时的差异。
# - "all"：依次打印所有策略，只做离线观察时有用。
DEFAULT_STRATEGY = "evidence_first"

# 是否调用真实 LLM。
# False：只打印 context build 诊断，不消耗 token，也不会得到模型评审结果。
# True：把构建好的上下文放进 Prompt，调用真实模型，输出 [llm_result]。
CALL_LLM = False

# 是否额外跑 minimal 策略做对照。
# True 时会先跑 minimal，再跑 DEFAULT_STRATEGY；通常和 CALL_LLM=True 一起使用，
# 用来观察“不带证据”和“带证据”时模型输出有什么差异。
COMPARE_WITH_MINIMAL = False

# 是否打印完整 system/user messages。
# True 时可以看到最终发给模型的完整输入；适合学习 Prompt + Context 如何合并。
PRINT_MESSAGES = False

# 是否打印完整 context block。
# False 时只打印预览，避免终端太长；True 时适合排查某条 source 是否真的进了 Prompt。
PRINT_FULL_CONTEXT = False

DEFAULT_CONFIG_REF = "chat.dev_chat"
DEFAULT_PROMPT_ID = "review.risk_review"
DEFAULT_PROMPT_VERSION = "4.0.0"


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _load_case(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"case file must be an object: {path}")
    return data


def _load_sources(case: dict[str, Any]) -> list[ContextSource]:
    sources: list[ContextSource] = []
    for item in case.get("sources", []):
        sources.append(
            ContextSource(
                source_id=str(item["source_id"]),
                source_type=item.get("source_type", "evidence"),
                title=item.get("title"),
                content=str(item["content"]),
                priority=int(item.get("priority", 50)),
                score=item.get("score"),
                metadata=item.get("metadata", {}),
            )
        )
    return sources


def _strategy_names(selected: str) -> list[str]:
    if selected == "all":
        return list(list_context_policy_names())
    return [selected]


def _active_strategy_names(selected: str, *, compare_with_minimal: bool) -> list[str]:
    if not compare_with_minimal:
        return _strategy_names(selected)
    if selected == "all":
        names = ["minimal", "evidence_first"]
    else:
        names = ["minimal", selected]
    return list(dict.fromkeys(names))


def _ids(values) -> str:
    return ", ".join(values) if values else "—"


def _preview(text: str, *, limit: int = 1400) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n... (truncated)"


def _print_report(report: ContextBuildReport) -> None:
    print(f"  [policy] {report.policy_name}")
    print(f"  [token_budget] {report.token_budget}")
    print(f"  [estimated_tokens] {report.estimated_tokens}")
    print("  [section_tokens]")
    for name, tokens in report.section_tokens.items():
        print(f"    [{name}] {tokens}")
    print(f"  [citation_candidates] {_ids(report.citation_source_ids)}")
    print(f"  [compressed_sources] {_ids(report.compressed_source_ids)}")
    print("  [dropped_sources]")
    if not report.dropped_sources:
        print("    —")
    for item in report.dropped_sources:
        title = f" ({item.title})" if item.title else ""
        print(f"    {item.source_id}{title} reason={item.reason} tokens={item.estimated_tokens}")
    print("  [warnings]")
    if not report.warnings:
        print("    —")
    for warning in report.warnings:
        suffix = f" source_id={warning.source_id}" if warning.source_id else ""
        print(f"    {warning.code}: {warning.message}{suffix}")


def _print_context(
    strategy: str,
    case: dict[str, Any],
    *,
    call_llm: bool,
    print_messages: bool,
    print_full_context: bool,
) -> None:
    policy = get_context_policy(strategy)
    context = build_review_context(
        requirement_text=str(case["requirement_text"]),
        sources=_load_sources(case),
        policy=policy,
    )
    assert context.report is not None

    print(f"[strategy] {strategy}")
    print("  [context_build]")
    print(f"  [included_sources] {_ids(context.included_source_ids)}")
    _print_report(context.report)
    print("  [built_context_preview]")
    context_text = context.context_block()
    print(_indent(context_text if print_full_context else _preview(context_text)))
    print()

    messages = _render_messages(context)
    if print_messages:
        _print_messages(messages)
        print()

    if call_llm:
        _call_llm(context, messages)
        print()
    else:
        print("  [llm_result] not_run")
        print("    将脚本顶部 CALL_LLM 改为 True 后，才会调用真实模型并输出评审结果。")
        print()


def _render_messages(context: BuiltContext) -> list[dict[str, str]]:
    tpl = get_prompt(DEFAULT_PROMPT_ID, version=DEFAULT_PROMPT_VERSION)
    return render_prompt(tpl, context.to_prompt_variables())


def _print_messages(messages: list[dict[str, str]]) -> None:
    print("  [messages]")
    for index, message in enumerate(messages, 1):
        print(f"    [{index}] role={message['role']}")
        print(_indent(message["content"], prefix="      "))


def _call_llm(
    context: BuiltContext,
    messages: list[dict[str, str]],
) -> None:
    _load_env()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("  [llm] skipped: OPENAI_API_KEY is not configured")
        return
    client = LLMClient.from_default_config()
    try:
        result = client.chat_structured(
            messages,
            DEFAULT_CONFIG_REF,
            structured_mode="json_object",
            temperature=0,
        )
    except LLMError as exc:
        print(f"  [llm_result] error: {exc}")
        return

    parse = result.parse
    usage = result.llm.usage.total_tokens if result.llm.usage else "—"
    if parse.ok:
        print(f"  [llm_result] parse=ok risks={parse.risk_count} tokens={usage} latency_ms={result.llm.latency_ms:.0f}")
        for index, risk in enumerate(parse.risks or [], 1):
            citation_ids = [citation.source_id for citation in risk.citations]
            print(f"    [{index}] {risk.category.value}/{risk.level.value} {risk.title} cites={_ids(citation_ids)}")
    else:
        print(f"  [llm_result] parse=fail stage={parse.error_stage} message={parse.message}")


def _indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line if line else prefix for line in text.splitlines())


def main() -> None:
    case = _load_case(CASE_PATH)
    print("[case]")
    print(f"  [id] {case.get('case_id')}")
    print(f"  [title] {case.get('title')}")
    print(f"  [source_count] {len(case.get('sources', []))}")
    print()

    call_llm = CALL_LLM or COMPARE_WITH_MINIMAL
    for strategy in _active_strategy_names(DEFAULT_STRATEGY, compare_with_minimal=COMPARE_WITH_MINIMAL):
        _print_context(
            strategy,
            case,
            call_llm=call_llm,
            print_messages=PRINT_MESSAGES,
            print_full_context=PRINT_FULL_CONTEXT,
        )


if __name__ == "__main__":
    main()
