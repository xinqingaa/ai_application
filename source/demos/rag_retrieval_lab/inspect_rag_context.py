"""Build prompt-ready context from the fixed Retriever's real candidates."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from _shared import load_retrieval_chunks, load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import ContextSource, LLMError, get_context_policy
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
)

PREPROCESSING_VERSION = "retrieval-text-v1"
DEMO_DIR = Path(__file__).resolve().parent
CASE_PATH = DEMO_DIR.parent / "llm_context_lab/context_cases.json"
log = get_logger("rag_retrieval_lab.rag_context")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RetrievalResult → ContextSource → BuiltContext 真实实验"
    )
    parser.add_argument(
        "--policies",
        default="evidence_first,tight_budget",
        help="逗号分隔的 llm_core context policy",
    )
    parser.add_argument("--candidate-k", type=int, default=5)
    parser.add_argument("--final-top-k", type=int, default=5)
    parser.add_argument(
        "--without-history",
        action="store_true",
        help="不加入历史评审辅助材料，用于单变量对照",
    )
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
    requirement = str(case["requirement_text"])
    chunks = load_retrieval_chunks()
    config = HybridRetrieverConfig(
        lexical_candidate_k=args.candidate_k,
        dense_candidate_k=args.candidate_k,
        final_top_k=args.final_top_k,
        knowledge_scope="after_sale",
        source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
        evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
    )
    try:
        PostgresChunkStore(dsn).upsert_chunks(chunks)
        chunk_embeddings = embed_texts(
            [chunk.text for chunk in chunks],
            text_ids=[chunk.chunk_id for chunk in chunks],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        PostgresVectorStore(dsn).upsert_embeddings(chunks, chunk_embeddings.records)
        query_embedding = embed_texts(
            [requirement],
            text_ids=[str(case["case_id"])],
            preprocessing_version=PREPROCESSING_VERSION,
        ).records[0]
        retrieval = FixedHybridRetriever(
            PostgresFTSRetriever(dsn),
            PostgresDenseRetriever(dsn),
        ).retrieve(requirement, query_embedding, config=config)
        history = () if args.without_history else _history_sources(case)
        builds = [
            build_rag_review_context(
                requirement_text=requirement,
                retrieval_result=retrieval,
                additional_sources=history,
                policy=get_context_policy(name.strip()),
            )
            for name in args.policies.split(",")
            if name.strip()
        ]
    except (LLMError, RetrievalError, KeyError, ValueError) as exc:
        _failure(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(case, retrieval, builds)
    else:
        _render(case, retrieval, builds, verbose=args.verbose)
    return 1 if retrieval.report.partial_failure else 0


def _history_sources(case) -> tuple[ContextSource, ...]:
    return tuple(
        ContextSource(
            source_id=str(item["source_id"]),
            content=str(item["content"]),
            source_type="history_review",
            title=item.get("title"),
            priority=int(item.get("priority", 50)),
            score=item.get("score"),
            metadata=item.get("metadata", {}),
        )
        for item in case.get("sources", [])
        if item.get("source_type") == "history_review"
    )


def _render(case, retrieval, builds, *, verbose: bool) -> None:
    console.title(
        "RAG Retrieval Lab · RetrievalResult to Context",
        f"case={case['case_id']} · retrieved={len(retrieval.candidates)}",
    )
    console.table(
        ["Fusion", "Chunk", "Routes", "Locator", "Content"],
        [
            [
                candidate.fusion_rank,
                candidate.chunk_id,
                "+".join(candidate.matched_routes),
                candidate.source_spans[0].locator.describe(),
                _preview(candidate.content, 60),
            ]
            for candidate in retrieval.candidates
        ],
        title="RetrievalReport · found candidates",
    )
    for build in builds:
        context = build.context
        report = context.report
        assert report is not None
        console.section(f"ContextBuildReport · {report.policy_name}")
        console.field("retrieved", ", ".join(build.mapping.mapped_source_ids) or "—")
        console.field("included", ", ".join(context.included_source_ids) or "—")
        console.field("dropped", ", ".join(context.dropped_source_ids) or "—")
        console.field(
            "citation candidates", ", ".join(report.citation_source_ids) or "—"
        )
        console.field(
            "budget",
            f"estimated={report.estimated_tokens} / limit={report.token_budget}",
        )
        if verbose:
            console.table(
                ["Chunk", "Mapping", "Type", "Route ranks", "Locator"],
                [
                    [
                        item.chunk_id,
                        item.reason,
                        item.source_type,
                        ", ".join(f"{name}:{rank}" for name, rank in item.route_ranks),
                        " | ".join(item.source_locators),
                    ]
                    for item in build.mapping.decisions
                ],
                title="Retrieval → ContextSource mapping",
            )
            console.print(context.context_block())
    console.success(
        "同一 RetrievalResult 已按不同预算装配；检索报告与上下文报告保持分层"
    )
    console.hint(
        "候选已检索但未 included 时，先看 ContextBuildReport 的 dropped reason"
    )


def _emit_json(case, retrieval, builds) -> None:
    log.info(
        "rag_context.retrieved",
        "固定 Retriever 已形成候选",
        case_id=case["case_id"],
        retriever_config_ref=retrieval.report.retriever_config_ref,
        retrieved_chunk_ids=[item.chunk_id for item in retrieval.candidates],
    )
    for build in builds:
        report = build.context.report
        assert report is not None
        log.info(
            "rag_context.built",
            "RAG Context 装配完成",
            policy=report.policy_name,
            retrieved_source_ids=build.mapping.mapped_source_ids,
            included_source_ids=build.context.included_source_ids,
            dropped=[
                {"source_id": item.source_id, "reason": item.reason}
                for item in report.dropped_sources
            ],
            citation_source_ids=report.citation_source_ids,
            estimated_tokens=report.estimated_tokens,
            token_budget=report.token_budget,
        )
    log.success("rag_context.completed", "RAG Context 观察完成")


def _configuration_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "rag_context.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL；RAG Context 实验不会使用静态假检索结果")


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
        console.hint("检查真实 Embedding、PostgreSQL、migration、policy 与来源位置")


def _preview(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
