"""Observe real PostgreSQL FTS candidates, ranks, and lexical boundaries."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app_log import add_log_arguments, configure_from_args, console, get_logger
from dotenv import load_dotenv
from rag_core import (
    ChunkPolicy,
    ChunkStrategy,
    EvidenceEligibility,
    LexicalAnalyzer,
    LexicalConfig,
    PostgresFTSRetriever,
    QueryOperator,
    RetrievalError,
    SourceRole,
    chunk_document,
    load_document,
)

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
DOCUMENT_PATH = (
    REPO_ROOT / "review_assistant/fixtures/v0/ingestion/order_rules.md"
)
QUERIES_PATH = (
    REPO_ROOT
    / "review_assistant/fixtures/v0/retrieval/lexical_queries.json"
)
log = get_logger("rag_retrieval_lab.lexical")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chunk → PostgreSQL FTS → LexicalHit 真实实验"
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=QUERIES_PATH,
        help="词面检索探针 JSON 路径",
    )
    parser.add_argument(
        "--query-operator",
        choices=("or", "and"),
        default="or",
        help="词项怎样组成 tsquery；默认 OR 以观察召回型基线",
    )
    parser.add_argument(
        "--candidate-k",
        type=int,
        default=5,
        help="每个问题最多返回多少个 lexical candidates",
    )
    add_log_arguments(parser)
    args = parser.parse_args()
    configure_from_args(args)
    json_mode = args.log_format == "json" and not args.verbose

    _load_env()
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        _render_config_error(json_mode)
        return 1

    payload = json.loads(args.queries.read_text(encoding="utf-8"))
    analyzer = LexicalAnalyzer(
        LexicalConfig(query_operator=QueryOperator(args.query_operator))
    )
    retriever = PostgresFTSRetriever(dsn, analyzer=analyzer)
    chunks = _load_chunks()

    if not json_mode:
        console.title(
            "RAG Retrieval Lab · PostgreSQL FTS",
            "真实 Chunk 入库与词面候选观察\n"
            f"dataset={payload['dataset_version']} · "
            f"operator={args.query_operator} · candidate_k={args.candidate_k}",
        )

    try:
        index_report = retriever.upsert_chunks(chunks)
        results = [
            (
                probe,
                retriever.search(probe["text"], candidate_k=args.candidate_k),
            )
            for probe in payload["queries"]
        ]
    except RetrievalError as exc:
        _render_retrieval_error(exc, json_mode)
        return 1

    if json_mode:
        _emit_json(payload, index_report, results)
    else:
        _render_summary(index_report, results, verbose=args.verbose)
    return 0


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _load_chunks():
    document = load_document(
        DOCUMENT_PATH,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        metadata={"knowledge_scope": "after_sale"},
    ).document
    result = chunk_document(
        document,
        ChunkPolicy(
            name="lexical_structure_aware",
            version="1.0.0",
            strategy=ChunkStrategy.STRUCTURE_AWARE,
            max_tokens=48,
        ),
    )
    return result.retrieval_chunks


def _render_config_error(json_mode: bool) -> None:
    if json_mode:
        log.error(
            "lexical.configuration_failed",
            "缺少 PostgreSQL 配置",
            code="database_url_missing",
        )
    else:
        console.error("缺少 DATABASE_URL，实验不会回退到 SQLite 或内存检索")
        console.hint("先按 review_assistant/README.md 初始化 PostgreSQL 和 migration")


def _render_retrieval_error(exc: RetrievalError, json_mode: bool) -> None:
    if json_mode:
        log.error(
            "lexical.failed",
            "PostgreSQL FTS 实验失败",
            code=exc.code.value,
            stage=exc.stage.value,
            error_message=exc.message,
        )
    else:
        console.error(str(exc))
        if exc.code.value == "migration_required":
            console.hint(
                "执行 review_assistant/infra/migrations/0001_create_rag_chunks.sql"
            )


def _render_summary(index_report, results, *, verbose: bool) -> None:
    console.info(
        f"indexed={index_report.indexed_chunks} · "
        f"lexical_config={index_report.lexical_config_ref} · "
        f"index_latency={index_report.latency_ms:.1f} ms"
    )
    console.table(
        ["Query", "Group", "Terms", "Hits", "Top rank", "Expectation"],
        [
            [
                probe["text"],
                probe["group"],
                " / ".join(result.diagnostics.query_terms),
                len(result.hits),
                "—" if not result.hits else f"{result.hits[0].fts_rank:.6f}",
                probe["expect"],
            ]
            for probe, result in results
        ],
        title="Lexical observations",
    )

    if verbose:
        for probe, result in results:
            console.section(f"{probe['id']} · {probe['text']}")
            console.field("tsquery", result.diagnostics.tsquery or "—")
            console.field(
                "postgres terms",
                " / ".join(result.diagnostics.postgres_query_terms),
            )
            if not result.hits:
                console.info("没有候选；先检查词项，再判断是否属于 lexical 自然边界")
                continue
            console.table(
                ["Rank", "FTS rank", "Matched", "Chunk", "Content"],
                [
                    [
                        hit.route_rank,
                        f"{hit.fts_rank:.6f}",
                        " / ".join(hit.matched_terms),
                        hit.chunk_id,
                        _preview(hit.content, 86),
                    ]
                    for hit in result.hits
                ],
            )

    console.success(
        f"{len(results)} queries · rank=postgresql_ts_rank · higher_is_better=true"
    )
    if not verbose:
        console.hint("使用 --verbose 查看 tsquery、PostgreSQL lexeme 和每个候选")


def _emit_json(payload, index_report, results) -> None:
    log.info(
        "lexical.indexed",
        "Chunk 已写入 PostgreSQL FTS",
        dataset_version=payload["dataset_version"],
        indexed_chunks=index_report.indexed_chunks,
        lexical_config_ref=index_report.lexical_config_ref,
        latency_ms=round(index_report.latency_ms, 1),
    )
    for probe, result in results:
        log.info(
            "lexical.query_observed",
            "词面检索观察完成",
            query_id=probe["id"],
            query=probe["text"],
            group=probe["group"],
            expect=probe["expect"],
            query_terms=result.diagnostics.query_terms,
            postgres_query_terms=result.diagnostics.postgres_query_terms,
            tsquery=result.diagnostics.tsquery,
            matched_chunks=result.diagnostics.matched_chunk_count,
            returned_chunks=result.diagnostics.returned_chunk_count,
            candidate_k=result.diagnostics.candidate_k,
            retriever_config_ref=result.diagnostics.retriever_config_ref,
            rank_name=result.diagnostics.rank_name,
            higher_is_better=result.diagnostics.higher_is_better,
            latency_ms=round(result.diagnostics.latency_ms, 1),
            hits=[
                {
                    "chunk_id": hit.chunk_id,
                    "document_id": hit.document_id,
                    "route_rank": hit.route_rank,
                    "fts_rank": round(hit.fts_rank, 6),
                    "matched_terms": hit.matched_terms,
                }
                for hit in result.hits
            ],
        )
    log.success(
        "lexical.completed",
        "PostgreSQL FTS 观察完成",
        queries=len(results),
    )


def _preview(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
