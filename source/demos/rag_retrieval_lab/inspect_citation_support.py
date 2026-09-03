"""Observe deterministic quote location followed by one real support judgment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _shared import load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import ContextSource, LLMClient, LLMError, build_review_context
from llm_core.context import get_context_policy
from rag_core import CitationSupportInput, validate_citation_support

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
PROBE_PATH = (
    REPO_ROOT
    / "source/apps/review_assistant/fixtures/rag/generation/citation_support_probes.json"
)
DEFAULT_VARIANTS = ("supported", "unrelated", "contradicted", "missing_quote")
log = get_logger("rag_retrieval_lab.citation_support")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="冻结上游，观察逐字引文定位与真实 Citation 支持性判断"
    )
    parser.add_argument(
        "--variants",
        default=",".join(DEFAULT_VARIANTS),
        help="逗号分隔：supported, unrelated, contradicted, missing_quote",
    )
    parser.add_argument(
        "--structured-mode",
        choices=("json_schema", "json_object"),
        default="json_schema",
    )
    parser.add_argument("--config-ref", default="chat.structured_chat")
    add_log_arguments(parser)
    args = parser.parse_args()
    json_mode = args.log_format == "json"
    if json_mode:
        args.verbose = False
    configure_from_args(args)

    try:
        payload = json.loads(PROBE_PATH.read_text(encoding="utf-8"))
        selected = _selected_variants(args.variants, payload["variants"])
        context, inputs = _build_input(payload, selected)
        load_workspace_env()
        result = validate_citation_support(
            context,
            inputs,
            client=LLMClient.from_default_config(),
            config_ref=args.config_ref,
            structured_mode=args.structured_mode,
            debug=args.verbose,
        )
    except (json.JSONDecodeError, KeyError, ValueError, LLMError) as exc:
        _failure(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(payload, selected, result)
    else:
        _render(payload, selected, result, verbose=args.verbose)
    return 0


def _selected_variants(value: str, variants: list[dict]) -> tuple[dict, ...]:
    requested = tuple(name.strip() for name in value.split(",") if name.strip())
    if not requested:
        raise ValueError("至少选择一个 variant")
    by_name = {item["name"]: item for item in variants}
    unknown = [name for name in requested if name not in by_name]
    if unknown:
        raise ValueError("未知 variant：" + ", ".join(unknown))
    return tuple(by_name[name] for name in requested)


def _build_input(payload: dict, variants: tuple[dict, ...]):
    sources = tuple(
        ContextSource(
            source_id=item["source_id"],
            content=item["content"],
            source_type="evidence",
            title=item["title"],
            metadata=item["metadata"],
        )
        for item in variants
    )
    context = build_review_context(
        requirement_text="订单详情页新增申请售后入口。",
        sources=sources,
        policy=get_context_policy("full_context"),
    )
    inputs = tuple(
        CitationSupportInput(
            claim_id=item["name"],
            claim_text=payload["claim_text"],
            source_id=item["source_id"],
            excerpt=item["excerpt"],
        )
        for item in variants
    )
    return context, inputs


def _render(payload, selected, result, *, verbose: bool) -> None:
    expected = {item["name"]: item for item in selected}
    console.title(
        "RAG Retrieval Lab · Citation Support",
        "冻结 Claim 与逐字引文，只改变来源内容和适用条件",
    )
    console.field("fixture", f"{payload['fixture_kind']}@{payload['version']}")
    console.field("claim", payload["claim_text"])
    console.field("prompt", result.report.prompt_ref)
    if result.response is not None:
        console.field(
            "model",
            f"provider={result.response.llm.provider} · "
            f"model={result.response.llm.model} · "
            f"config={result.report.config_ref} · "
            f"structured_mode={result.report.structured_mode}",
        )
    console.table(
        ["Variant", "Quote", "Expected", "Observed", "Reason"],
        [
            [
                check.claim_id,
                check.location_status.value,
                expected[check.claim_id]["expected_verdict"] or "—",
                check.verdict.value if check.verdict else "—",
                check.reason or "模型判断前停止",
            ]
            for check in result.checks
        ],
        title="Quote location and real model observations",
    )
    console.field("validation status", result.report.status.value)
    console.field("model calls", result.report.model_call_count)
    if result.report.usage is not None:
        console.field(
            "usage",
            f"prompt={result.report.usage.prompt_tokens} · "
            f"completion={result.report.usage.completion_tokens} · "
            f"total={result.report.usage.total_tokens}",
        )
    if result.report.cost is not None:
        cost = result.report.cost
        console.field(
            "estimated cost",
            f"{cost.total_cost:.8f} {cost.currency} ({cost.price_label})"
            if cost.known
            else "unknown",
        )
    if result.report.parse_error_message:
        console.error(
            result.report.parse_error_stage or "validation",
            result.report.parse_error_message,
        )
    if verbose:
        for check in result.checks:
            console.section(check.claim_id)
            console.field("source_id", check.source_id)
            console.field("excerpt", check.excerpt)
            console.field("location", check.location_status.value)
            console.field(
                "locator",
                (
                    f"{check.source_locator} · chars={check.char_start}:{check.char_end}"
                    if check.char_start is not None
                    else "—"
                ),
            )
            console.field("verdict", check.verdict.value if check.verdict else "—")
            console.field("reason", check.reason or "—")
        if result.response is not None:
            console.field("raw structured response", result.response.llm.content)
    console.hint(
        "引文存在只允许进入支持判断；supported 也不代表整份结论证据充分"
    )


def _emit_json(payload, selected, result) -> None:
    log.info(
        "citation_support.started",
        "Citation 支持性实验身份已固定",
        fixture_kind=payload["fixture_kind"],
        fixture_version=payload["version"],
        variants=[item["name"] for item in selected],
        claim=payload["claim_text"],
    )
    log.info(
        "citation_support.observed",
        "逐字引文定位与真实支持性判断完成",
        status=result.report.status.value,
        prompt_ref=result.report.prompt_ref,
        config_ref=result.report.config_ref,
        model_call_count=result.report.model_call_count,
        usage=(
            {
                "prompt_tokens": result.report.usage.prompt_tokens,
                "completion_tokens": result.report.usage.completion_tokens,
                "total_tokens": result.report.usage.total_tokens,
            }
            if result.report.usage
            else None
        ),
        checks=[
            {
                "claim_id": check.claim_id,
                "source_id": check.source_id,
                "location_status": check.location_status.value,
                "char_start": check.char_start,
                "char_end": check.char_end,
                "verdict": check.verdict.value if check.verdict else None,
                "reason": check.reason,
            }
            for check in result.checks
        ],
    )
    log.success(
        "citation_support.completed",
        "Citation 支持性实验已形成完整报告",
        verified_claim_ids=[item.claim_id for item in result.verified_citations],
    )


def _failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "citation_support.failed",
            "Citation 支持性实验未完成",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        console.hint("检查 fixture、Chat 配置、真实模型和 Structured Output 能力")


if __name__ == "__main__":
    raise SystemExit(main())
