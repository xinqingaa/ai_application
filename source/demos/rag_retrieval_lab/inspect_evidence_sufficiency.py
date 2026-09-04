"""Observe real evidence-sufficiency judgments while changing only knowledge scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _shared import load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import LLMClient, LLMError
from rag_core import (
    EvidenceClaim,
    EvidenceRequirement,
    EvidenceScopeSource,
    CitationSupportVerdict,
    VerifiedCitation,
    decide_evidence_sufficiency,
)

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
PROBE_PATH = (
    REPO_ROOT
    / "source/apps/review_assistant/fixtures/rag/generation/evidence_sufficiency_probes.json"
)
DEFAULT_VARIANTS = ("full_scope", "missing_error_contract", "empty_scope")
log = get_logger("rag_retrieval_lab.evidence_sufficiency")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="冻结 Claim 与上游已验证 Citation，只改变 knowledge scope"
    )
    parser.add_argument(
        "--variants",
        default=",".join(DEFAULT_VARIANTS),
        help="逗号分隔：full_scope, missing_error_contract, empty_scope",
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
        load_workspace_env()
        client = LLMClient.from_default_config()
        results = [
            (variant, _run_variant(payload, variant, client, args))
            for variant in selected
        ]
    except (json.JSONDecodeError, KeyError, ValueError, LLMError) as exc:
        _failure(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(payload, results)
    else:
        _render(payload, results, verbose=args.verbose)
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


def _run_variant(payload: dict, variant: dict, client, args):
    claims = tuple(
        EvidenceClaim(item["claim_id"], item["claim_text"])
        for item in payload["claims"]
    )
    requirements = tuple(
        EvidenceRequirement(
            item["requirement_id"],
            item["required_fact"],
            item["expected_source_role"],
            tuple(item["affected_claim_ids"]),
        )
        for item in payload["coverage_requirements"]
    )
    source_index = {item["source_id"]: item for item in payload["sources"]}
    active = tuple(source_index[item] for item in variant["active_source_ids"])
    sources = tuple(
        EvidenceScopeSource(
            item["source_id"],
            item["source_role"],
            item["content"],
            item["source_locator"],
        )
        for item in active
    )
    claim_texts = {item.claim_id: item.claim_text for item in claims}
    citations = tuple(
        VerifiedCitation(
            claim_id=item["citation"]["claim_id"],
            claim_text=claim_texts[item["citation"]["claim_id"]],
            source_id=item["source_id"],
            excerpt=item["citation"]["excerpt"],
            source_locator=item["source_locator"],
            char_start=0,
            char_end=len(item["citation"]["excerpt"]),
            verdict=CitationSupportVerdict.SUPPORTED,  # Fixed upstream input; this lab does not retest section 17.
            reason=item["citation"]["reason"],
        )
        for item in active
    )
    return decide_evidence_sufficiency(
        claims,
        citations,
        requirements,
        sources,
        client=client,
        config_ref=args.config_ref,
        structured_mode=args.structured_mode,
        debug=args.verbose,
    )


def _render(payload: dict, results, *, verbose: bool) -> None:
    console.title(
        "RAG Retrieval Lab · Evidence Sufficiency",
        "冻结 Claim 与已验证 Citation，只改变 knowledge scope",
    )
    console.field("fixture", f"{payload['fixture_kind']}@{payload['version']}")
    for variant, result in results:
        console.section(variant["name"])
        decision = result.decision.kind.value if result.decision else "—"
        console.field("expected decision", variant["expected_decision"])
        console.field("observed decision", decision)
        console.field(
            "active sources", ", ".join(variant["active_source_ids"]) or "（无）"
        )
        console.field("validation status", result.report.status.value)
        console.field("model calls", result.report.model_call_count)
        if result.decision:
            console.table(
                ["Requirement", "Coverage", "Citation claims", "Reason"],
                [
                    [
                        check.requirement_id,
                        check.verdict.value,
                        ", ".join(check.citation_claim_ids) or "—",
                        check.reason,
                    ]
                    for check in result.decision.coverage
                ],
                title="Coverage observations",
            )
            for gap in result.decision.gaps:
                console.field("follow-up", gap.question)
        if result.report.usage:
            console.field(
                "usage",
                f"prompt={result.report.usage.prompt_tokens} · "
                f"completion={result.report.usage.completion_tokens} · "
                f"total={result.report.usage.total_tokens}",
            )
        if result.report.parse_error_message:
            console.error(
                result.report.parse_error_stage or "validation",
                result.report.parse_error_message,
            )
        if verbose and result.response:
            console.field("raw structured response", result.response.llm.content)
    console.hint("refusal 是合法的证据结论；真实依赖或输出契约失败不产生它。")


def _emit_json(payload: dict, results) -> None:
    log.info(
        "evidence_sufficiency.started",
        "Evidence sufficiency 探针身份已固定",
        fixture_kind=payload["fixture_kind"],
        fixture_version=payload["version"],
        variants=[item[0]["name"] for item in results],
    )
    for variant, result in results:
        log.info(
            "evidence_sufficiency.observed",
            "知识范围改变后的充分性观察完成",
            variant=variant["name"],
            expected_decision=variant["expected_decision"],
            observed_decision=(result.decision.kind.value if result.decision else None),
            validation_status=result.report.status.value,
            model_call_count=result.report.model_call_count,
            gaps=(
                [
                    {
                        "requirement_id": gap.requirement_id,
                        "affected_claim_ids": list(gap.affected_claim_ids),
                        "question": gap.question,
                    }
                    for gap in result.decision.gaps
                ]
                if result.decision
                else []
            ),
        )


def _failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "evidence_sufficiency.failed",
            "实验没有形成充分性报告",
            error_type=type(exc).__name__,
            error=str(exc),
        )
    else:
        console.error(type(exc).__name__, str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
