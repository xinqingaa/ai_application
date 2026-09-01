"""Observe real structured generation and Citation Candidate membership."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from _shared import load_query_payload, load_retrieval_chunks, load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import (
    BuiltContext,
    ContextSource,
    LLMClient,
    LLMError,
    build_review_context,
    get_context_policy,
)
from rag_core import (
    EvidenceEligibility,
    FixedHybridRetriever,
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
DEFAULT_QUERY_ID = "surface_match"
DEFAULT_CONTEXT_POLICY = "full_context"
VARIANT_NAMES = ("rag_evidence", "normal_noise", "empty_evidence")
DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
CASE_PATH = DEMO_DIR.parent / "llm_context_lab/context_cases.json"
PROBE_PATH = (
    REPO_ROOT
    / "source/apps/review_assistant/fixtures/rag/generation/trusted_generation_probes.json"
)
log = get_logger("rag_retrieval_lab.trusted_generation")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="固定 Retrieval → Context → 真实结构化生成 → 来源声明集合检查"
    )
    parser.add_argument(
        "--variants",
        default=",".join(VARIANT_NAMES),
        help="逗号分隔：rag_evidence, normal_noise, empty_evidence",
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
        selected = _selected_variants(args.variants)
        query_payload = load_query_payload()
        query_probe = _select_query(query_payload, DEFAULT_QUERY_ID)
        requirement_case = json.loads(CASE_PATH.read_text(encoding="utf-8"))
        requirement = str(requirement_case["requirement_text"])
        probes = json.loads(PROBE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        _failure(exc, json_mode)
        return 1

    load_workspace_env()
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        _configuration_error(json_mode)
        return 1

    retriever_config = HybridRetrieverConfig(
        lexical_candidate_k=5,
        dense_candidate_k=5,
        final_top_k=3,
        knowledge_scope="after_sale",
        source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
        evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
    )
    context_policy = get_context_policy(DEFAULT_CONTEXT_POLICY)

    try:
        upstream = _build_real_rag_context(
            dsn,
            retrieval_query=str(query_probe["text"]),
            requirement=requirement,
            retriever_config=retriever_config,
            context_policy_name=DEFAULT_CONTEXT_POLICY,
        )
        _require_clean_upstream(upstream)
        contexts = _context_variants(
            requirement,
            upstream["context"],
            probes["normal_noise_source"],
            context_policy_name=DEFAULT_CONTEXT_POLICY,
        )
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

    render_args = {
        "query_payload": query_payload,
        "query_probe": query_probe,
        "requirement_case": requirement_case,
        "retriever_config": retriever_config,
        "context_policy": context_policy,
        "upstream": upstream,
        "contexts": contexts,
        "results": results,
    }
    if json_mode:
        _emit_json(**render_args)
    else:
        _render(**render_args, verbose=args.verbose)

    # GenerationStatus is an observed business result. The experiment process
    # succeeds once every selected real call produced a complete report.
    return 0


def _selected_variants(value: str) -> tuple[str, ...]:
    selected = tuple(name.strip() for name in value.split(",") if name.strip())
    if not selected:
        raise ValueError("至少选择一个 variant")
    unknown = sorted(set(selected) - set(VARIANT_NAMES))
    if unknown:
        raise ValueError("未知 variant：" + ", ".join(unknown))
    return selected


def _select_query(payload: dict, query_id: str) -> dict:
    selected = tuple(probe for probe in payload["queries"] if probe["id"] == query_id)
    if not selected:
        available = ", ".join(probe["id"] for probe in payload["queries"])
        raise ValueError(f"未知 query_id={query_id}；可选值：{available}")
    return selected[0]


def _build_real_rag_context(
    dsn,
    *,
    retrieval_query: str,
    requirement: str,
    retriever_config: HybridRetrieverConfig,
    context_policy_name: str,
) -> dict:
    chunks = load_retrieval_chunks()
    PostgresChunkStore(dsn).upsert_chunks(chunks)
    chunk_embeddings = embed_texts(
        [chunk.text for chunk in chunks],
        text_ids=[chunk.chunk_id for chunk in chunks],
        preprocessing_version=PREPROCESSING_VERSION,
    )
    PostgresVectorStore(dsn).upsert_embeddings(chunks, chunk_embeddings.records)
    query_embeddings = embed_texts(
        [retrieval_query],
        text_ids=[DEFAULT_QUERY_ID],
        preprocessing_version=PREPROCESSING_VERSION,
    )
    retrieval = FixedHybridRetriever(
        PostgresFTSRetriever(dsn),
        PostgresDenseRetriever(dsn),
    ).retrieve(
        retrieval_query,
        query_embeddings.records[0],
        config=retriever_config,
    )
    build = build_rag_review_context(
        requirement_text=requirement,
        retrieval_result=retrieval,
        policy=get_context_policy(context_policy_name),
    )
    return {
        "chunks": chunks,
        "chunk_embeddings": chunk_embeddings,
        "query_embeddings": query_embeddings,
        "retrieval": retrieval,
        "build": build,
        "context": build.context,
    }


def _require_clean_upstream(upstream: dict) -> None:
    chunks = upstream["chunks"]
    retrieval = upstream["retrieval"]
    expected_ids = {chunk.chunk_id for chunk in chunks}
    unexpected = sorted(
        candidate.chunk_id
        for candidate in retrieval.candidates
        if candidate.chunk_id not in expected_ids
    )
    if retrieval.report.partial_failure:
        raise ValueError("固定 Retriever 存在部分路线失败；先完成第 14、15 节排查")
    if unexpected:
        raise ValueError("数据库包含非当前 fixture 候选：" + ", ".join(unexpected))


def _context_variants(
    requirement: str,
    rag_context: BuiltContext,
    noise_payload: dict,
    *,
    context_policy_name: str,
) -> dict[str, BuiltContext]:
    noise = ContextSource(
        source_id=str(noise_payload["source_id"]),
        source_type="evidence",
        title=noise_payload.get("title"),
        content=str(noise_payload["content"]),
        metadata=noise_payload.get("metadata", {}),
    )
    policy = get_context_policy(context_policy_name)
    return {
        "rag_evidence": rag_context,
        "normal_noise": build_review_context(
            requirement_text=requirement,
            sources=(noise,),
            policy=policy,
        ),
        "empty_evidence": build_review_context(
            requirement_text=requirement,
            sources=(),
            policy=policy,
        ),
    }


def _render(
    *,
    query_payload,
    query_probe,
    requirement_case,
    retriever_config,
    context_policy,
    upstream,
    contexts,
    results,
    verbose: bool,
) -> None:
    retrieval = upstream["retrieval"]
    first_result = results[0][1]
    console.title(
        "RAG Retrieval Lab · Trusted Generation",
        "固定第 15 节上游，只改变模型本轮看到的 Evidence",
    )
    console.field("dataset", query_payload["dataset_version"])
    console.field("retrieval query", f"{query_probe['id']}={query_probe['text']}")
    console.field(
        "requirement",
        f"{requirement_case['case_id']}={requirement_case['title']}",
    )
    console.field("retriever config", retriever_config.config_ref)
    console.field(
        "retrieval",
        f"final={len(retrieval.candidates)} · partial_failure=no · "
        f"latency={retrieval.report.latency_ms:.1f} ms",
    )
    console.field(
        "context policy",
        f"{context_policy.name} · token_budget={context_policy.token_budget} · "
        f"evidence_budget={context_policy.section_budgets['evidence']}",
    )
    console.field("prompt", first_result.report.prompt_ref)
    console.field(
        "model",
        f"provider={first_result.response.llm.provider} · "
        f"model={first_result.response.llm.model} · "
        f"config={first_result.report.config_ref} · "
        f"structured_mode={first_result.report.structured_mode}",
    )
    console.table(
        [
            "Variant",
            "Evidence",
            "Allowed",
            "Risks",
            "No citation",
            "Known",
            "Unknown",
            "Status",
        ],
        [
            [
                name,
                result.report.evidence_state.value,
                len(result.report.citation_candidate_ids),
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
            context = contexts[name]
            console.section(name)
            console.field(
                "included source ids",
                ", ".join(context.included_source_ids) or "—",
            )
            console.field(
                "citation candidates",
                ", ".join(result.report.citation_candidate_ids) or "—",
            )
            console.field(
                "context tokens",
                f"estimated={context.estimated_tokens} / budget={context.token_budget}",
            )
            console.print(
                context.context_block() or "（Context 只有 Requirement，无 Evidence）"
            )
            console.field("raw structured response", result.response.llm.content)
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
            console.field("generation status", result.status.value)
    console.hint("succeeded 只表示结构合法且已声明 ID 未越界；本实验不验证内容支持性")


def _emit_json(
    *,
    query_payload,
    query_probe,
    requirement_case,
    retriever_config,
    context_policy,
    upstream,
    contexts,
    results,
) -> None:
    retrieval = upstream["retrieval"]
    log.info(
        "trusted_generation.started",
        "可信生成实验身份已固定",
        dataset_version=query_payload["dataset_version"],
        retrieval_query_id=query_probe["id"],
        retrieval_query=query_probe["text"],
        requirement_case_id=requirement_case["case_id"],
        retriever_config_ref=retriever_config.config_ref,
        context_policy=context_policy.name,
        retrieval_candidate_ids=[item.chunk_id for item in retrieval.candidates],
    )
    for name, result in results:
        context = contexts[name]
        log.info(
            "trusted_generation.variant_observed",
            "真实可信生成边界观察完成",
            variant=name,
            status=result.status.value,
            provider=result.response.llm.provider,
            model=result.response.llm.model,
            config_ref=result.report.config_ref,
            prompt_ref=result.report.prompt_ref,
            structured_mode=result.report.structured_mode,
            evidence_state=result.report.evidence_state.value,
            included_source_ids=context.included_source_ids,
            citation_candidate_ids=result.report.citation_candidate_ids,
            parse_ok=result.report.parse_ok,
            parse_error_stage=result.report.parse_error_stage,
            risk_count=result.report.risk_count,
            risk_without_citation_count=result.report.risk_without_citation_count,
            candidate_claim_count=result.report.candidate_claim_count,
            unknown_source_count=result.report.unknown_source_count,
            risks=[risk.model_dump(mode="json") for risk in result.risks],
        )
    log.success(
        "trusted_generation.completed",
        "所有选定 variant 都已完成真实调用和结果检查",
        generation_statuses={name: result.status.value for name, result in results},
    )


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
            "可信生成实验未完成",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        console.hint("检查实验输入、PostgreSQL、Embedding、Chat 配置和结构化输出能力")


if __name__ == "__main__":
    raise SystemExit(main())
