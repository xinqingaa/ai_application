"""Observe real Embedding + pgvector Dense Retrieval over traceable Chunks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from _shared import (
    QUERIES_PATH,
    load_query_payload,
    load_retrieval_chunks,
    load_workspace_env,
)
from app_log import add_log_arguments, configure_from_args, console, get_logger
from llm_core import LLMError
from rag_core import (
    DenseSearchMode,
    EvidenceEligibility,
    PostgresChunkStore,
    PostgresDenseRetriever,
    PostgresVectorStore,
    RetrievalError,
    SourceRole,
    embed_texts,
)

PREPROCESSING_VERSION = "retrieval-text-v1"
log = get_logger("rag_retrieval_lab.dense")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chunk → real Embedding → pgvector → DenseHit 真实实验"
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=QUERIES_PATH,
        help="共享检索探针 JSON 路径",
    )
    parser.add_argument(
        "--candidate-k",
        type=int,
        default=5,
        help="每个问题最多返回多少个 dense candidates",
    )
    parser.add_argument(
        "--search-mode",
        choices=("exact", "hnsw", "compare"),
        default="compare",
        help="exact 正确性基线、HNSW 索引路线或两者对照",
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

    payload = load_query_payload(args.queries)
    chunks = load_retrieval_chunks()
    chunk_store = PostgresChunkStore(dsn)
    vector_store = PostgresVectorStore(dsn)
    retriever = PostgresDenseRetriever(dsn)

    if not json_mode:
        console.title(
            "RAG Retrieval Lab · pgvector Dense Retrieval",
            "真实 Chunk、真实 Embedding 与向量候选观察\n"
            f"dataset={payload['dataset_version']} · "
            f"mode={args.search_mode} · candidate_k={args.candidate_k}",
        )

    try:
        chunk_report = chunk_store.upsert_chunks(chunks)
        chunk_embeddings = embed_texts(
            [chunk.text for chunk in chunks],
            text_ids=[chunk.chunk_id for chunk in chunks],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        vector_report = vector_store.upsert_embeddings(
            chunks,
            chunk_embeddings.records,
        )
        hnsw_report = None
        if args.search_mode in ("hnsw", "compare"):
            hnsw_report = vector_store.ensure_hnsw_index(vector_report.embedding_space)

        query_embeddings = embed_texts(
            [probe["text"] for probe in payload["queries"]],
            text_ids=[probe["id"] for probe in payload["queries"]],
            preprocessing_version=PREPROCESSING_VERSION,
        )
        results = _search_all(
            retriever,
            payload["queries"],
            query_embeddings.records,
            candidate_k=args.candidate_k,
            search_mode=args.search_mode,
        )
    except (LLMError, RetrievalError, ValueError) as exc:
        _render_failure(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(
            payload,
            chunk_report,
            vector_report,
            hnsw_report,
            chunk_embeddings.response,
            query_embeddings.response,
            results,
        )
    else:
        _render_summary(
            chunk_report,
            vector_report,
            hnsw_report,
            chunk_embeddings.response,
            query_embeddings.response,
            results,
            verbose=args.verbose,
        )
    return 0


def _search_all(
    retriever,
    probes,
    query_records,
    *,
    candidate_k: int,
    search_mode: str,
):
    modes = {
        "exact": (DenseSearchMode.EXACT,),
        "hnsw": (DenseSearchMode.HNSW,),
        "compare": (DenseSearchMode.EXACT, DenseSearchMode.HNSW),
    }[search_mode]
    results = []
    for probe, record in zip(probes, query_records, strict=True):
        route_results = {
            mode.value: retriever.search(
                record,
                candidate_k=candidate_k,
                knowledge_scope="after_sale",
                source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
                evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
                mode=mode,
                inspect_plan=mode is DenseSearchMode.HNSW,
            )
            for mode in modes
        }
        results.append((probe, route_results))
    return results


def _render_config_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "dense.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL，实验不会回退到内存向量库")
        console.hint("先按 source/apps/review_assistant/README.md 执行 0001 和 0002 migration")


def _render_failure(exc: Exception, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "dense.failed",
            "Dense Retrieval 实验失败",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    else:
        console.error(str(exc))
        console.hint(
            "依次检查真实 Embedding 配置、0001/0002 migration、Embedding 空间和向量维度"
        )


def _render_summary(
    chunk_report,
    vector_report,
    hnsw_report,
    chunk_response,
    query_response,
    results,
    *,
    verbose: bool,
) -> None:
    space = vector_report.embedding_space
    console.info(
        f"chunks={chunk_report.indexed_chunks} · "
        f"vectors={vector_report.indexed_embeddings} · "
        f"space={space.space_ref}"
    )
    console.info(
        f"provider={space.provider} · model={space.model} · "
        f"dimensions={space.dimensions} · preprocessing={space.preprocessing_version}"
    )
    console.info(
        f"chunk_embedding={chunk_response.latency_ms:.1f} ms · "
        f"query_embedding={query_response.latency_ms:.1f} ms"
    )
    if hnsw_report:
        console.info(
            f"HNSW index={hnsw_report.index_name} · "
            f"setup={hnsw_report.latency_ms:.1f} ms"
        )

    rows = []
    for probe, routes in results:
        exact = routes.get("exact")
        hnsw = routes.get("hnsw")
        primary = exact or hnsw
        top = primary.hits[0] if primary.hits else None
        rows.append(
            [
                probe["text"],
                probe["group"],
                len(primary.hits),
                "—" if top is None else f"{top.cosine_distance:.6f}",
                "—" if top is None else _preview(top.content, 58),
                "—"
                if hnsw is None
                else ("yes" if hnsw.diagnostics.index_used else "no"),
                probe["observations"]["dense"],
            ]
        )
    console.table(
        ["Query", "Group", "Hits", "Top distance", "Top Chunk", "HNSW used", "Observe"],
        rows,
        title="Dense observations · cosine distance 越小越近",
    )

    if verbose:
        for probe, routes in results:
            console.section(f"{probe['id']} · {probe['text']}")
            for route_name, result in routes.items():
                diagnostics = result.diagnostics
                console.field(
                    route_name,
                    f"indexed={diagnostics.indexed_chunk_count} · "
                    f"visible={diagnostics.visible_chunk_count} · "
                    f"returned={diagnostics.returned_chunk_count} · "
                    f"index_used={diagnostics.index_used} · "
                    f"plan={' → '.join(diagnostics.plan_node_types) or 'not inspected'}",
                )
                console.table(
                    ["Rank", "Distance", "Similarity", "Chunk", "Content"],
                    [
                        [
                            hit.route_rank,
                            f"{hit.cosine_distance:.6f}",
                            f"{hit.cosine_similarity:.6f}",
                            hit.chunk_id,
                            _preview(hit.content, 86),
                        ]
                        for hit in result.hits
                    ],
                )

    console.success(
        f"{len(results)} queries · distance=pgvector_cosine_distance · "
        "lower_is_better=true"
    )
    if hnsw_report and any(
        route.get("hnsw") and not route["hnsw"].diagnostics.index_used
        for _, route in results
    ):
        console.hint(
            "HNSW 已创建，但小数据集上 PostgreSQL 可能选择顺序扫描；这不等于索引损坏"
        )
    if not verbose:
        console.hint("使用 --verbose 查看每个候选、可见数量和查询计划")


def _emit_json(
    payload,
    chunk_report,
    vector_report,
    hnsw_report,
    chunk_response,
    query_response,
    results,
) -> None:
    space = vector_report.embedding_space
    log.info(
        "dense.indexed",
        "Chunk 向量已写入 pgvector",
        dataset_version=payload["dataset_version"],
        indexed_chunks=chunk_report.indexed_chunks,
        indexed_embeddings=vector_report.indexed_embeddings,
        embedding_space_ref=space.space_ref,
        provider=space.provider,
        model=space.model,
        dimensions=space.dimensions,
        preprocessing_version=space.preprocessing_version,
        hnsw_index=None if hnsw_report is None else hnsw_report.index_name,
        chunk_embedding_latency_ms=round(chunk_response.latency_ms, 1),
        query_embedding_latency_ms=round(query_response.latency_ms, 1),
    )
    for probe, routes in results:
        for route_name, result in routes.items():
            diagnostics = result.diagnostics
            log.info(
                "dense.query_observed",
                "向量检索观察完成",
                query_id=probe["id"],
                query=probe["text"],
                group=probe["group"],
                observe=probe["observations"]["dense"],
                search_mode=route_name,
                indexed_chunks=diagnostics.indexed_chunk_count,
                visible_chunks=diagnostics.visible_chunk_count,
                returned_chunks=diagnostics.returned_chunk_count,
                index_name=diagnostics.index_name,
                index_used=diagnostics.index_used,
                plan_node_types=diagnostics.plan_node_types,
                latency_ms=round(diagnostics.latency_ms, 1),
                hits=[
                    {
                        "chunk_id": hit.chunk_id,
                        "route_rank": hit.route_rank,
                        "cosine_distance": round(hit.cosine_distance, 6),
                        "cosine_similarity": round(hit.cosine_similarity, 6),
                    }
                    for hit in result.hits
                ],
            )
    log.success("dense.completed", "pgvector Dense Retrieval 观察完成")


def _preview(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
