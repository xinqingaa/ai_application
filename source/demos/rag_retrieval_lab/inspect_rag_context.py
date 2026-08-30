"""Build prompt-ready Context from lesson 14's fixed real retrieval result."""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
import os

from _shared import load_query_payload, load_retrieval_chunks, load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import ContextBuildPolicy, LLMError, get_context_policy
from rag_core import (
    EmbeddingSpace,
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
)

PREPROCESSING_VERSION = "retrieval-text-v1"
DEFAULT_QUERY_ID = "surface_match"
log = get_logger("rag_retrieval_lab.rag_context")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="固定 RetrievalResult → ContextSource → BuiltContext 真实实验"
    )
    parser.add_argument(
        "--query-id",
        default=DEFAULT_QUERY_ID,
        help=f"retrieval_queries.json 中的 query id（默认：{DEFAULT_QUERY_ID}）",
    )
    parser.add_argument(
        "--policy",
        default="full_context",
        help="llm_core Context policy（默认：full_context）",
    )
    parser.add_argument(
        "--evidence-budget",
        type=int,
        help="只覆盖所选 policy 的 Evidence 分区预算；不改变 Retriever",
    )
    add_log_arguments(parser)
    args = parser.parse_args()
    json_mode = args.log_format == "json"
    if json_mode:
        # JSON Lines is a machine-readable contract; --verbose must not switch
        # the shared logger back to Rich terminal output.
        args.verbose = False
    configure_from_args(args)

    load_workspace_env()
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        _configuration_error(json_mode)
        return 1

    try:
        payload = load_query_payload()
        probe = _select_query(payload, args.query_id)
        chunks = load_retrieval_chunks()
        context_policy = _context_policy(args.policy, args.evidence_budget)
        retriever_config = HybridRetrieverConfig(
            lexical_candidate_k=5,
            dense_candidate_k=5,
            final_top_k=3,
            knowledge_scope="after_sale",
            source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
            evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
        )
    except (KeyError, ValueError) as exc:
        _failure(exc, json_mode)
        return 1

    try:
        PostgresChunkStore(dsn).upsert_chunks(chunks)
        chunk_embeddings = embed_texts(
            [chunk.text for chunk in chunks],
            text_ids=[chunk.chunk_id for chunk in chunks],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        PostgresVectorStore(dsn).upsert_embeddings(chunks, chunk_embeddings.records)
        query_embeddings = embed_texts(
            [probe["text"]],
            text_ids=[probe["id"]],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        retrieval = FixedHybridRetriever(
            PostgresFTSRetriever(dsn),
            PostgresDenseRetriever(dsn),
        ).retrieve(
            probe["text"],
            query_embeddings.records[0],
            config=retriever_config,
        )
        build = build_rag_review_context(
            requirement_text=probe["text"],
            retrieval_result=retrieval,
            policy=context_policy,
        )
    except (LLMError, RetrievalError, KeyError, ValueError) as exc:
        _failure(exc, json_mode)
        return 1

    unexpected = _unexpected_candidate_ids(chunks, retrieval)
    render_args = {
        "payload": payload,
        "probe": probe,
        "chunks": chunks,
        "chunk_embeddings": chunk_embeddings,
        "query_embeddings": query_embeddings,
        "retriever_config": retriever_config,
        "retrieval": retrieval,
        "context_policy": context_policy,
        "build": build,
        "unexpected": unexpected,
    }
    if json_mode:
        _emit_json(**render_args)
    else:
        _render(**render_args, verbose=args.verbose)

    return 1 if retrieval.report.partial_failure or unexpected else 0


def _select_query(payload: dict, query_id: str) -> dict:
    selected = tuple(
        probe for probe in payload["queries"] if probe["id"] == query_id
    )
    if not selected:
        available = ", ".join(probe["id"] for probe in payload["queries"])
        raise ValueError(f"未知 query_id={query_id}；可选值：{available}")
    return selected[0]


def _context_policy(name: str, evidence_budget: int | None) -> ContextBuildPolicy:
    policy = get_context_policy(name)
    if evidence_budget is None:
        return policy
    if evidence_budget < 0:
        raise ValueError("evidence_budget 不能小于 0")
    section_budgets = dict(policy.section_budgets)
    section_budgets["evidence"] = evidence_budget
    return replace(policy, section_budgets=section_budgets)


def _policy_payload(policy: ContextBuildPolicy) -> dict:
    return {
        "name": policy.name,
        "token_budget": policy.token_budget,
        "section_budgets": dict(sorted(policy.section_budgets.items())),
        "allow_compression": policy.allow_compression,
        "max_source_tokens": policy.max_source_tokens,
        "min_compression_tokens": policy.min_compression_tokens,
        "include_source_types": (
            None
            if policy.include_source_types is None
            else sorted(policy.include_source_types)
        ),
    }


def _policy_ref(policy: ContextBuildPolicy) -> str:
    canonical = json.dumps(
        _policy_payload(policy),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"context-policy@1.0.0:{digest}"


def _render(
    *,
    payload,
    probe,
    chunks,
    chunk_embeddings,
    query_embeddings,
    retriever_config,
    retrieval,
    context_policy,
    build,
    unexpected,
    verbose: bool,
) -> None:
    space = EmbeddingSpace.from_records(chunk_embeddings.records)
    report = build.context.report
    assert report is not None

    console.title(
        "RAG Retrieval Lab · RetrievalResult to BuiltContext",
        "沿用固定 Retriever 的同一份资料和 surface_match=申请售后",
    )
    console.field("dataset", payload["dataset_version"])
    console.field("query", f"{probe['id']}={probe['text']}")
    console.field("retriever config", retriever_config.config_ref)
    console.field(
        "embedding",
        f"space={space.space_ref} · provider={space.provider} · model={space.model} "
        f"· dimensions={space.dimensions} · preprocessing={space.preprocessing_version}",
    )
    console.field(
        "embedding latency",
        f"chunks={chunk_embeddings.response.latency_ms:.1f} ms · "
        f"query={query_embeddings.response.latency_ms:.1f} ms",
    )
    console.field("current fixture chunks", ", ".join(chunk.chunk_id for chunk in chunks))
    console.field(
        "retrieval",
        f"final={len(retrieval.candidates)} · partial_failure="
        f"{'yes' if retrieval.report.partial_failure else 'no'} · "
        f"latency={retrieval.report.latency_ms:.1f} ms",
    )
    console.table(
        ["Route", "Execution", "Post-threshold", "Visible", "Candidate", "Passed"],
        [
            [
                route_name,
                route.execution_status.value,
                route.post_threshold_status.value,
                route.visible_chunk_count,
                route.candidate_count,
                route.passed_threshold_count,
            ]
            for route_name, route in retrieval.report.route_reports.items()
        ],
        title="RetrievalReport · upstream facts",
    )

    console.field("context policy", f"{context_policy.name} · {_policy_ref(context_policy)}")
    console.field(
        "context controls",
        f"total={context_policy.token_budget} · "
        f"evidence={context_policy.section_budgets.get('evidence', 0)} · "
        f"compression={'on' if context_policy.allow_compression else 'off'} · "
        f"max_source={context_policy.max_source_tokens}",
    )
    console.table(
        ["Fusion", "Chunk / source", "Mapping", "Type", "Reason", "Locator"],
        [
            [
                item.fusion_rank,
                item.source_id,
                item.status.value,
                item.source_type,
                item.reason,
                " | ".join(item.source_locators),
            ]
            for item in build.mapping.decisions
        ],
        title="RetrievalResult → ContextSource",
    )
    console.table(
        ["Section", "Used", "Budget"],
        [
            [
                section,
                report.section_tokens.get(section, 0),
                context_policy.section_budgets.get(section, 0),
            ]
            for section in (
                "requirement",
                "evidence",
                "history",
                "agent_summary",
                "other",
            )
        ],
        title="ContextBuildReport · section budget",
    )
    console.field("included", ", ".join(build.context.included_source_ids) or "—")
    console.field("citation candidates", ", ".join(report.citation_source_ids) or "—")
    console.field(
        "context estimate",
        f"estimated={report.estimated_tokens} / total={report.token_budget}",
    )
    if report.dropped_sources:
        console.table(
            ["Source", "Type", "Estimated", "Reason"],
            [
                [item.source_id, item.source_type, item.estimated_tokens, item.reason]
                for item in report.dropped_sources
            ],
            title="Dropped sources",
        )
    if report.compressed_sources:
        console.table(
            ["Source", "Original", "Compressed", "Reason"],
            [
                [
                    item.source_id,
                    item.original_tokens,
                    item.compressed_tokens,
                    item.reason,
                ]
                for item in report.compressed_sources
            ],
            title="Compressed sources",
        )
    for warning in report.warnings:
        console.warning(
            f"context warning: {warning.code} · {warning.message}"
            + ("" if warning.source_id is None else f" · source={warning.source_id}")
        )
    if verbose:
        console.section("BuiltContext · model-visible block")
        console.print(build.context.context_block())

    if unexpected:
        console.warning(
            "候选中出现不属于当前两个 fixture Chunk 的身份："
            f"{', '.join(unexpected)}。本轮仍展示诊断，但退出状态为 1；"
            "请使用干净课程数据库或先按明确更新策略处理旧 Chunk，再做 Context 归因。"
        )
    elif retrieval.report.partial_failure:
        console.warning("Retriever 存在失败路线；Context 仅为部分结果，退出状态为 1")
    else:
        console.success("同一 RetrievalResult 已完成 Context 装配，来源身份保持可追踪")
    console.hint("候选未进入模型输入时，先看 mapping，再看 dropped/compressed reason")


def _emit_json(
    *,
    payload,
    probe,
    chunks,
    chunk_embeddings,
    query_embeddings,
    retriever_config,
    retrieval,
    context_policy,
    build,
    unexpected,
) -> None:
    space = EmbeddingSpace.from_records(chunk_embeddings.records)
    report = build.context.report
    assert report is not None
    log.info(
        "rag_context.started",
        "Context 实验固定输入已准备",
        dataset_version=payload["dataset_version"],
        query_id=probe["id"],
        query=probe["text"],
        retriever_config_ref=retriever_config.config_ref,
        embedding_space_ref=space.space_ref,
        provider=space.provider,
        model=space.model,
        dimensions=space.dimensions,
        preprocessing_version=space.preprocessing_version,
        chunk_embedding_latency_ms=round(chunk_embeddings.response.latency_ms, 1),
        query_embedding_latency_ms=round(query_embeddings.response.latency_ms, 1),
        current_fixture_chunk_ids=[chunk.chunk_id for chunk in chunks],
    )
    log.info(
        "rag_context.retrieval_observed",
        "固定 Retriever 的 RetrievalResult 已交给 Context",
        routes={
            name: {
                "execution_status": route.execution_status.value,
                "post_threshold_status": route.post_threshold_status.value,
                "visible": route.visible_chunk_count,
                "candidates": route.candidate_count,
                "passed_threshold": route.passed_threshold_count,
                "error_code": route.error_code,
                "error_message": route.error_message,
            }
            for name, route in retrieval.report.route_reports.items()
        },
        retrieved_chunk_ids=[item.chunk_id for item in retrieval.candidates],
        unexpected_candidate_ids=unexpected,
        partial_failure=retrieval.report.partial_failure,
        latency_ms=retrieval.report.latency_ms,
    )
    log.info(
        "rag_context.built",
        "RAG Context 装配完成",
        context_policy_ref=_policy_ref(context_policy),
        context_policy=_policy_payload(context_policy),
        mapping_decisions=[
            {
                "chunk_id": item.chunk_id,
                "source_id": item.source_id,
                "fusion_rank": item.fusion_rank,
                "source_type": item.source_type,
                "status": item.status.value,
                "reason": item.reason,
                "source_locators": item.source_locators,
                "route_ranks": item.route_ranks,
                "native_scores": item.native_scores,
            }
            for item in build.mapping.decisions
        ],
        included_source_ids=build.context.included_source_ids,
        dropped=[
            {
                "source_id": item.source_id,
                "source_type": item.source_type,
                "estimated_tokens": item.estimated_tokens,
                "reason": item.reason,
            }
            for item in report.dropped_sources
        ],
        compressed=[
            {
                "source_id": item.source_id,
                "original_tokens": item.original_tokens,
                "compressed_tokens": item.compressed_tokens,
                "reason": item.reason,
            }
            for item in report.compressed_sources
        ],
        citation_source_ids=report.citation_source_ids,
        section_tokens=report.section_tokens,
        estimated_tokens=report.estimated_tokens,
        token_budget=report.token_budget,
        warnings=[
            {
                "code": item.code,
                "message": item.message,
                "source_id": item.source_id,
            }
            for item in report.warnings
        ],
        context_block=build.context.context_block(),
    )
    if unexpected or retrieval.report.partial_failure:
        log.warning(
            "rag_context.completed_with_warning",
            "Context 观察完成，但本轮不能作为干净单变量对照",
            unexpected_candidate_ids=unexpected,
            partial_failure=retrieval.report.partial_failure,
        )
    else:
        log.success("rag_context.completed", "RAG Context 观察完成")


def _unexpected_candidate_ids(chunks, retrieval) -> list[str]:
    current_ids = {chunk.chunk_id for chunk in chunks}
    observed_ids = {item.chunk_id for item in retrieval.report.final_selection}
    return sorted(observed_ids - current_ids)


def _configuration_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "rag_context.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL；RAG Context 实验不会使用静态候选或假向量")
        console.hint("先按产品 README 准备数据库、migration 和真实 Embedding")


def _failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "rag_context.failed",
            "RAG Context 实验失败",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        if isinstance(exc, (KeyError, ValueError)):
            console.hint("检查 query_id、policy 和 evidence_budget 输入契约")
        else:
            console.hint("检查真实 Embedding、PostgreSQL 与 migration")


if __name__ == "__main__":
    raise SystemExit(main())
