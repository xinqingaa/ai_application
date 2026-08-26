"""Run real structured generation across grounded, noise, and empty contexts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from _shared import load_retrieval_chunks, load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import (
    ContextSource,
    LLMClient,
    LLMError,
    build_review_context,
    get_context_policy,
)
from rag_core import (
    EvidenceEligibility,
    FixedHybridRetriever,
    GenerationStatus,
    HybridRetrieverConfig,
    PostgresChunkStore,
    PostgresDenseRetriever,
    PostgresFTSRetriever,
    PostgresVectorStore,
    RetrievalError,
    SourceRole,
    build_rag_review_context,
    embed_texts,
    generate_trusted_review,
)

PREPROCESSING_VERSION = "retrieval-text-v1"
DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
CASE_PATH = DEMO_DIR.parent / "llm_context_lab/context_cases.json"
PROBE_PATH = (
    REPO_ROOT / "source/apps/review_assistant/fixtures/rag/generation/trusted_generation_probes.json"
)
log = get_logger("rag_retrieval_lab.trusted_generation")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="真实 RAG Context → Structured Review → Citation Candidate 检查"
    )
    parser.add_argument(
        "--variants",
        default="rag_evidence,normal_noise,empty_evidence",
        help="逗号分隔：rag_evidence, normal_noise, empty_evidence",
    )
    parser.add_argument(
        "--structured-mode",
        choices=("json_schema", "json_object"),
        default="json_schema",
    )
    parser.add_argument("--config-ref", default="chat.structured_chat")
    parser.add_argument("--candidate-k", type=int, default=5)
    parser.add_argument("--final-top-k", type=int, default=5)
    add_log_arguments(parser)
    args = parser.parse_args()
    configure_from_args(args)
    json_mode = args.log_format == "json" and not args.verbose

    load_workspace_env()
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        _configuration_error(json_mode)
        return 1

    case = json.loads(CASE_PATH.read_text(encoding="utf-8"))
    probes = json.loads(PROBE_PATH.read_text(encoding="utf-8"))
    requirement = str(case["requirement_text"])
    try:
        rag_context = _build_real_rag_context(
            dsn,
            requirement,
            candidate_k=args.candidate_k,
            final_top_k=args.final_top_k,
        )
        contexts = _context_variants(
            requirement,
            rag_context,
            probes["normal_noise_source"],
        )
        selected = [name.strip() for name in args.variants.split(",") if name.strip()]
        unknown = sorted(set(selected) - set(contexts))
        if unknown:
            raise ValueError("未知 variant：" + ", ".join(unknown))
        client = LLMClient.from_default_config()
        results = [
            (
                name,
                generate_trusted_review(
                    contexts[name],
                    client=client,
                    config_ref=args.config_ref,
                    structured_mode=args.structured_mode,
                    debug=args.verbose,
                ),
            )
            for name in selected
        ]
    except (LLMError, RetrievalError, KeyError, ValueError) as exc:
        _failure(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(case, results)
    else:
        _render(case, results, verbose=args.verbose)
    return (
        1
        if any(result.status is not GenerationStatus.SUCCEEDED for _, result in results)
        else 0
    )


def _build_real_rag_context(dsn, requirement, *, candidate_k, final_top_k):
    chunks = load_retrieval_chunks()
    PostgresChunkStore(dsn).upsert_chunks(chunks)
    chunk_embeddings = embed_texts(
        [chunk.text for chunk in chunks],
        text_ids=[chunk.chunk_id for chunk in chunks],
        preprocessing_version=PREPROCESSING_VERSION,
    )
    PostgresVectorStore(dsn).upsert_embeddings(chunks, chunk_embeddings.records)
    query_embedding = embed_texts(
        [requirement],
        text_ids=["trusted-generation-requirement"],
        preprocessing_version=PREPROCESSING_VERSION,
    ).records[0]
    retrieval = FixedHybridRetriever(
        PostgresFTSRetriever(dsn),
        PostgresDenseRetriever(dsn),
    ).retrieve(
        requirement,
        query_embedding,
        config=HybridRetrieverConfig(
            lexical_candidate_k=candidate_k,
            dense_candidate_k=candidate_k,
            final_top_k=final_top_k,
            knowledge_scope="after_sale",
            source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
            evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
        ),
    )
    return build_rag_review_context(
        requirement_text=requirement,
        retrieval_result=retrieval,
        policy=get_context_policy("evidence_first"),
    ).context


def _context_variants(requirement, rag_context, noise_payload):
    noise = ContextSource(
        source_id=str(noise_payload["source_id"]),
        source_type="evidence",
        title=noise_payload.get("title"),
        content=str(noise_payload["content"]),
        metadata=noise_payload.get("metadata", {}),
    )
    return {
        "rag_evidence": rag_context,
        "normal_noise": build_review_context(
            requirement_text=requirement,
            sources=(noise,),
            policy=get_context_policy("evidence_first"),
        ),
        "empty_evidence": build_review_context(
            requirement_text=requirement,
            sources=(),
            policy=get_context_policy("evidence_first"),
        ),
    }


def _render(case, results, *, verbose: bool) -> None:
    console.title(
        "RAG Retrieval Lab · Trusted Generation Boundary",
        f"case={case['case_id']} · prompt=review.risk_review@5.0.0",
    )
    console.table(
        ["Variant", "Evidence", "Risks", "No citation", "Known", "Unknown", "Status"],
        [
            [
                name,
                result.report.evidence_state.value,
                result.report.risk_count,
                result.report.risk_without_citation_count,
                result.report.candidate_claim_count,
                result.report.unknown_source_count,
                result.status.value,
            ]
            for name, result in results
        ],
        title="Real model observations",
    )
    if verbose:
        for name, result in results:
            console.section(name)
            console.field(
                "citation candidates",
                ", ".join(result.report.citation_candidate_ids) or "—",
            )
            for index, risk in enumerate(result.risks, 1):
                claims = ", ".join(item.source_id for item in risk.citations) or "—"
                console.print(
                    f"{index}. [{risk.level.value}/{risk.category.value}] {risk.title}\n"
                    f"   {risk.rationale}\n   claims={claims}"
                )
            for check in result.report.claim_checks:
                console.field(
                    f"claim {check.risk_index}.{check.citation_index}",
                    f"{check.source_id} → {check.status.value}",
                )
    console.hint(
        "candidate 只表示 source id 来自本轮 Evidence；本实验没有验证引用内容是否支持风险"
    )


def _emit_json(case, results) -> None:
    for name, result in results:
        log.info(
            "trusted_generation.variant_observed",
            "真实可信生成边界观察完成",
            case_id=case["case_id"],
            variant=name,
            status=result.status.value,
            prompt_ref=result.report.prompt_ref,
            evidence_state=result.report.evidence_state.value,
            citation_candidate_ids=result.report.citation_candidate_ids,
            risk_count=result.report.risk_count,
            risk_without_citation_count=result.report.risk_without_citation_count,
            candidate_claim_count=result.report.candidate_claim_count,
            unknown_source_count=result.report.unknown_source_count,
            risks=[risk.model_dump(mode="json") for risk in result.risks],
        )
    log.success("trusted_generation.completed", "可信生成边界观察完成")


def _configuration_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "trusted_generation.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL；真实生成实验不会回退到假检索或假模型")


def _failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "trusted_generation.failed",
            "可信生成实验失败",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        console.hint("检查 PostgreSQL、Embedding、chat 配置和结构化输出能力")


if __name__ == "__main__":
    raise SystemExit(main())
