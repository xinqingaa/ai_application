"""
05_context_compare — compare context-building policies for one review case.

Default run is offline and does not call an LLM:
    python context_compare.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from llm_core import (
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


def _print_context(strategy: str, case: dict[str, Any], call_llm: bool) -> None:
    policy = get_context_policy(strategy)
    context = build_review_context(
        requirement_text=str(case["requirement_text"]),
        sources=_load_sources(case),
        policy=policy,
    )
    assert context.report is not None

    print(f"[strategy] {strategy}")
    print(f"  [included_sources] {_ids(context.included_source_ids)}")
    _print_report(context.report)
    print("  [prompt_preview]")
    print(_indent(_preview(context.context_block())))
    print()

    if call_llm:
        _call_llm(context)
        print()


def _call_llm(context) -> None:
    _load_env()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("  [llm] skipped: OPENAI_API_KEY is not configured")
        return
    client = LLMClient.from_default_config()
    tpl = get_prompt(DEFAULT_PROMPT_ID, version=DEFAULT_PROMPT_VERSION)
    messages = render_prompt(tpl, context.to_prompt_variables())
    try:
        result = client.chat_structured(
            messages,
            DEFAULT_CONFIG_REF,
            structured_mode="json_object",
            temperature=0,
        )
    except LLMError as exc:
        print(f"  [llm] error: {exc}")
        return

    parse = result.parse
    if parse.ok:
        print(f"  [llm] parse=ok risks={parse.risk_count} tokens={result.llm.usage.total_tokens if result.llm.usage else '—'}")
        for index, risk in enumerate(parse.risks or [], 1):
            citation_ids = [citation.source_id for citation in risk.citations]
            print(f"    [{index}] {risk.category.value}/{risk.level.value} {risk.title} cites={_ids(citation_ids)}")
    else:
        print(f"  [llm] parse=fail stage={parse.error_stage} message={parse.message}")


def _indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line if line else prefix for line in text.splitlines())


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare llm_core context-building policies.")
    parser.add_argument(
        "--strategy",
        default="all",
        choices=("all", *list_context_policy_names()),
        help="Context policy to run. Default: all",
    )
    parser.add_argument(
        "--call-llm",
        action="store_true",
        help="Optionally call chat_structured with json_object after building context.",
    )
    args = parser.parse_args()

    case = _load_case(CASE_PATH)
    print("[case]")
    print(f"  [id] {case.get('case_id')}")
    print(f"  [title] {case.get('title')}")
    print(f"  [source_count] {len(case.get('sources', []))}")
    print()

    for strategy in _strategy_names(args.strategy):
        _print_context(strategy, case, call_llm=args.call_llm)


if __name__ == "__main__":
    main()
