"""Observe the fixed V0 retrieval control order and diagnostic report."""

from __future__ import annotations

import argparse
import os

from _shared import load_query_payload, load_retrieval_chunks, load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import LLMError
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
    embed_texts,
)

PREPROCESSING_VERSION = "retrieval-text-v1"
log = get_logger("rag_retrieval_lab.retrieval_contract")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pre-filter → route threshold → RRF → final_top_k 真实实验"
    )
    parser.add_argument("--lexical-candidate-k", type=int, default=5)
    parser.add_argument("--dense-candidate-k", type=int, default=5)
    parser.add_argument("--lexical-min-rank", type=float)
    parser.add_argument("--dense-max-distance", type=float)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--final-top-k", type=int, default=3)
    parser.add_argument("--knowledge-scope", default="after_sale")
    add_log_arguments(parser)
    args = parser.parse_args()
    configure_from_args(args)
    json_mode = args.log_format == "json" and not args.verbose

    load_workspace_env()
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        _render_config_error(json_mode)
        return 1

    payload = load_query_payload()
    chunks = load_retrieval_chunks()
    config = HybridRetrieverConfig(
        lexical_candidate_k=args.lexical_candidate_k,
        dense_candidate_k=args.dense_candidate_k,
        lexical_min_rank=args.lexical_min_rank,
        dense_max_distance=args.dense_max_distance,
        rrf_k=args.rrf_k,
        final_top_k=args.final_top_k,
        knowledge_scope=args.knowledge_scope,
        source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
        evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
    )

    chunk_store = PostgresChunkStore(dsn)
    vector_store = PostgresVectorStore(dsn)
    retriever = FixedHybridRetriever(
        PostgresFTSRetriever(dsn),
        PostgresDenseRetriever(dsn),
    )
    if not json_mode:
        console.title(
            "RAG Retrieval Lab · Fixed Retriever Contract",
            "同一批资料和问题，观察候选在哪个控制阶段被保留或淘汰\n"
            f"config={config.config_ref}",
        )

    try:
        chunk_store.upsert_chunks(chunks)
        chunk_embeddings = embed_texts(
            [chunk.text for chunk in chunks],
            text_ids=[chunk.chunk_id for chunk in chunks],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        vector_store.upsert_embeddings(chunks, chunk_embeddings.records)
        query_embeddings = embed_texts(
            [probe["text"] for probe in payload["queries"]],
            text_ids=[probe["id"] for probe in payload["queries"]],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        observations = [
            (
                probe,
                retriever.retrieve(probe["text"], record, config=config),
            )
            for probe, record in zip(
                payload["queries"], query_embeddings.records, strict=True
            )
        ]
    except (LLMError, RetrievalError, ValueError) as exc:
        _render_failure(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(payload, config, observations)
    else:
        _render_summary(config, observations, verbose=args.verbose)
    return 1 if any(result.report.partial_failure for _, result in observations) else 0


def _render_config_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "retrieval_contract.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL；实验不会改用内存候选或假向量")
        console.hint("先按 review_assistant/README.md 准备数据库和真实 Embedding")


def _render_failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "retrieval_contract.failed",
            "固定 Retriever 实验准备失败",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        console.hint("检查真实 Embedding 配置、PostgreSQL 与全部 migration")


def _render_summary(config, observations, *, verbose: bool) -> None:
    console.field("control order", " → ".join(observations[0][1].report.control_order))
    console.field(
        "route controls",
        f"lexical k={config.lexical_candidate_k}, min_rank={config.lexical_min_rank} · "
        f"dense k={config.dense_candidate_k}, max_distance={config.dense_max_distance}",
    )
    console.field(
        "final controls",
        f"rrf_k={config.rrf_k} · final_top_k={config.final_top_k} · "
        f"scope={config.knowledge_scope}",
    )
    console.table(
        ["Query", "Lexical", "Dense", "Fused", "Final", "No-result reason"],
        [
            [
                probe["text"],
                _route_counts(result.report.route_reports["lexical"]),
                _route_counts(result.report.route_reports["dense"]),
                result.report.fusion_diagnostics.distinct_candidate_count,
                len(result.candidates),
                "—"
                if result.report.no_result_reason is None
                else result.report.no_result_reason.value,
            ]
            for probe, result in observations
        ],
        title="Where candidates changed",
    )

    if verbose:
        for probe, result in observations:
            console.section(f"{probe['id']} · {probe['text']}")
            for route_name, route in result.report.route_reports.items():
                console.field(
                    route_name,
                    f"status={route.execution_status.value} · indexed={route.indexed_chunk_count} "
                    f"· visible={route.visible_chunk_count} · candidates={route.candidate_count} "
                    f"· passed={route.passed_threshold_count} "
                    f"· dropped={route.dropped_threshold_count}",
                )
                if route.error_code:
                    console.error(
                        f"{route_name}: {route.error_code} · {route.error_message}"
                    )
            console.table(
                ["Route", "Chunk", "Native value", "Direction", "Decision"],
                [
                    [
                        item.route_name,
                        item.chunk_id,
                        f"{item.native_score_name}={item.native_score:.6f}",
                        "higher" if item.higher_is_better else "lower",
                        item.reason,
                    ]
                    for item in result.report.threshold_decisions
                ],
                title="Route threshold decisions",
            )
            console.table(
                ["Fusion", "Chunk", "RRF", "Final decision", "Content"],
                [
                    [
                        item.fusion_rank,
                        item.chunk_id,
                        f"{item.rrf_score:.6f}",
                        item.reason,
                        _candidate_preview(result, item.chunk_id),
                    ]
                    for item in result.report.final_selection
                ],
                title="RRF and final_top_k decisions",
            )

    console.success(f"{len(observations)} queries · report={config.config_ref}")
    console.hint("比较参数时一次只改一个；空结果先看 no_result_reason，再看各阶段数量")


def _emit_json(payload, config, observations) -> None:
    log.info(
        "retrieval_contract.started",
        "固定 Retriever 实验已准备",
        dataset_version=payload["dataset_version"],
        retriever_config_ref=config.config_ref,
    )
    for probe, result in observations:
        report = result.report
        log.info(
            "retrieval_contract.query_observed",
            "固定 Retriever 观察完成",
            query_id=probe["id"],
            query=probe["text"],
            control_order=report.control_order,
            routes={
                name: {
                    "execution_status": route.execution_status.value,
                    "indexed": route.indexed_chunk_count,
                    "visible": route.visible_chunk_count,
                    "matched": route.matched_chunk_count,
                    "candidates": route.candidate_count,
                    "passed_threshold": route.passed_threshold_count,
                    "dropped_threshold": route.dropped_threshold_count,
                    "error_code": route.error_code,
                }
                for name, route in report.route_reports.items()
            },
            fused=report.fusion_diagnostics.distinct_candidate_count,
            selected=len(result.candidates),
            no_result_reason=(
                None
                if report.no_result_reason is None
                else report.no_result_reason.value
            ),
            threshold_decisions=[item.__dict__ for item in report.threshold_decisions],
            final_selection=[item.__dict__ for item in report.final_selection],
        )
    log.success(
        "retrieval_contract.completed",
        "固定 Retriever 观察完成",
        queries=len(observations),
    )


def _route_counts(route) -> str:
    if route.error_code:
        return f"failed:{route.error_code}"
    return (
        f"visible {route.visible_chunk_count} → candidate {route.candidate_count} "
        f"→ pass {route.passed_threshold_count}"
    )


def _candidate_preview(result, chunk_id: str) -> str:
    candidates = {candidate.chunk_id: candidate for candidate in result.candidates}
    candidate = candidates.get(chunk_id)
    if candidate is None:
        return "— (not in final_top_k)"
    compact = " ".join(candidate.content.split())
    return compact if len(compact) <= 60 else compact[:59] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
