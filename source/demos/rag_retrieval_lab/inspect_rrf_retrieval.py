"""Compare lexical, dense, and reciprocal-rank-fused candidates."""

from __future__ import annotations

import argparse
import os

from _shared import load_query_payload, load_retrieval_chunks, load_workspace_env
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import LLMError
from rag_core import (
    DenseSearchMode,
    EvidenceEligibility,
    PostgresChunkStore,
    PostgresDenseRetriever,
    PostgresFTSRetriever,
    PostgresVectorStore,
    RetrievalError,
    RouteStatus,
    SourceRole,
    dense_ranked_route,
    embed_texts,
    failed_ranked_route,
    lexical_ranked_route,
    reciprocal_rank_fusion,
)

PREPROCESSING_VERSION = "retrieval-text-v1"
log = get_logger("rag_retrieval_lab.rrf")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LexicalHit + DenseHit → RRF candidates 真实实验"
    )
    parser.add_argument("--candidate-k", type=int, default=5)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument(
        "--dense-mode",
        choices=("exact", "hnsw"),
        default="exact",
        help="默认 exact 以隔离融合变量；可切换 HNSW 观察索引路线",
    )
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
    chunk_store = PostgresChunkStore(dsn)
    lexical_retriever = PostgresFTSRetriever(dsn)
    vector_store = PostgresVectorStore(dsn)
    dense_retriever = PostgresDenseRetriever(dsn)
    dense_mode = DenseSearchMode(args.dense_mode)

    if not json_mode:
        console.title(
            "RAG Retrieval Lab · Reciprocal Rank Fusion",
            "同一 Chunk、同一问题下比较 lexical / dense / RRF\n"
            f"dataset={payload['dataset_version']} · candidate_k={args.candidate_k} "
            f"· rrf_k={args.rrf_k} · dense={dense_mode.value}",
        )

    try:
        chunk_store.upsert_chunks(chunks)
        chunk_embeddings = embed_texts(
            [chunk.text for chunk in chunks],
            text_ids=[chunk.chunk_id for chunk in chunks],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        vector_report = vector_store.upsert_embeddings(
            chunks,
            chunk_embeddings.records,
        )
        if dense_mode is DenseSearchMode.HNSW:
            vector_store.ensure_hnsw_index(vector_report.embedding_space)
        query_embeddings = embed_texts(
            [probe["text"] for probe in payload["queries"]],
            text_ids=[probe["id"] for probe in payload["queries"]],
            preprocessing_version=PREPROCESSING_VERSION,
        )
    except (LLMError, RetrievalError, ValueError) as exc:
        _render_failure(exc, json_mode)
        return 1

    observations = []
    for probe, query_record in zip(
        payload["queries"], query_embeddings.records, strict=True
    ):
        lexical_route = _lexical_route(
            lexical_retriever,
            probe["text"],
            candidate_k=args.candidate_k,
        )
        dense_route = _dense_route(
            dense_retriever,
            query_record,
            candidate_k=args.candidate_k,
            mode=dense_mode,
        )
        fused = reciprocal_rank_fusion(
            (lexical_route, dense_route),
            rrf_k=args.rrf_k,
        )
        observations.append((probe, lexical_route, dense_route, fused))

    if json_mode:
        _emit_json(payload, vector_report.embedding_space, observations)
    else:
        _render_summary(
            vector_report.embedding_space,
            observations,
            verbose=args.verbose,
        )
    return 1 if any(item[3].diagnostics.failed_routes for item in observations) else 0


def _lexical_route(retriever, query: str, *, candidate_k: int):
    try:
        return lexical_ranked_route(retriever.search(query, candidate_k=candidate_k))
    except RetrievalError as exc:
        return failed_ranked_route(
            "lexical",
            error_code=exc.code.value,
            error_message=exc.message,
        )


def _dense_route(retriever, query_record, *, candidate_k: int, mode):
    try:
        result = retriever.search(
            query_record,
            candidate_k=candidate_k,
            knowledge_scope="after_sale",
            source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
            evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
            mode=mode,
        )
        return dense_ranked_route(result)
    except RetrievalError as exc:
        return failed_ranked_route(
            "dense",
            error_code=exc.code.value,
            error_message=exc.message,
        )


def _render_config_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "rrf.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL，RRF 实验不会改用本地假候选")
        console.hint("先按 review_assistant/README.md 执行数据库准备")


def _render_failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "rrf.failed",
            "RRF 实验准备失败",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        console.hint("检查真实 Embedding 配置、PostgreSQL 与两条 migration")


def _render_summary(space, observations, *, verbose: bool) -> None:
    console.info(
        f"space={space.space_ref} · model={space.model} · dimensions={space.dimensions}"
    )
    console.table(
        ["Query", "Lexical", "Dense", "RRF top", "Routes", "Observe"],
        [
            [
                probe["text"],
                _route_top(lexical),
                _route_top(dense),
                "—"
                if not fused.candidates
                else _preview(fused.candidates[0].content, 48),
                f"{lexical.status.value}/{dense.status.value}",
                _observation(probe),
            ]
            for probe, lexical, dense, fused in observations
        ],
        title="Rank-only fusion observations",
    )

    if verbose:
        for probe, lexical, dense, fused in observations:
            console.section(f"{probe['id']} · {probe['text']}")
            console.field(
                "routes",
                f"lexical={lexical.status.value}:{len(lexical.candidates)} · "
                f"dense={dense.status.value}:{len(dense.candidates)}",
            )
            if fused.diagnostics.failed_routes:
                console.error(
                    "route failed: " + ", ".join(fused.diagnostics.failed_routes)
                )
            console.table(
                ["Fusion", "RRF", "Routes", "Route ranks", "Native values", "Content"],
                [
                    [
                        candidate.fusion_rank,
                        f"{candidate.rrf_score:.6f}",
                        " + ".join(candidate.matched_routes),
                        " / ".join(
                            f"{item.route_name}:{item.route_rank}"
                            for item in candidate.contributions
                        ),
                        " / ".join(
                            f"{item.native_score_name}={item.native_score:.6f}"
                            for item in candidate.contributions
                        ),
                        _preview(candidate.content, 80),
                    ]
                    for candidate in fused.candidates
                ],
            )

    console.success(
        f"{len(observations)} queries · fusion=RRF · raw scores were not added"
    )
    console.hint(
        "RRF 只形成融合候选；final_top_k、route threshold 和淘汰原因属于后续 Retriever 契约"
    )


def _emit_json(payload, space, observations) -> None:
    log.info(
        "rrf.started",
        "RRF 共享实验已准备",
        dataset_version=payload["dataset_version"],
        embedding_space_ref=space.space_ref,
    )
    for probe, lexical, dense, fused in observations:
        log.info(
            "rrf.query_observed",
            "RRF 融合观察完成",
            query_id=probe["id"],
            query=probe["text"],
            route_statuses={
                "lexical": lexical.status.value,
                "dense": dense.status.value,
            },
            route_candidate_counts=fused.diagnostics.route_candidate_counts,
            distinct_candidates=fused.diagnostics.distinct_candidate_count,
            overlap_candidates=fused.diagnostics.overlap_candidate_count,
            failed_routes=fused.diagnostics.failed_routes,
            fusion_config_ref=fused.diagnostics.fusion_config_ref,
            candidates=[
                {
                    "chunk_id": candidate.chunk_id,
                    "fusion_rank": candidate.fusion_rank,
                    "rrf_score": round(candidate.rrf_score, 8),
                    "contributions": [
                        {
                            "route": item.route_name,
                            "route_rank": item.route_rank,
                            "reciprocal_rank": round(item.reciprocal_rank, 8),
                            "native_score_name": item.native_score_name,
                            "native_score": item.native_score,
                            "higher_is_better": item.higher_is_better,
                        }
                        for item in candidate.contributions
                    ],
                }
                for candidate in fused.candidates
            ],
        )
    log.success("rrf.completed", "RRF 观察完成", queries=len(observations))


def _route_top(route) -> str:
    if route.status is RouteStatus.FAILED:
        return f"failed:{route.error_code}"
    if not route.candidates:
        return "empty"
    return _preview(route.candidates[0].content, 42)


def _observation(probe) -> str:
    if probe["id"] == "synonym_boundary":
        return "观察 dense 是否补回 lexical 漏掉的同义候选"
    if probe["id"] == "exact_identifier":
        return "观察 lexical 精确标识优势是否被保留"
    if probe["id"] == "normal_noise":
        return "观察融合是否也会保留单路噪声"
    return "比较两路排名、重合候选与融合位置"


def _preview(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
