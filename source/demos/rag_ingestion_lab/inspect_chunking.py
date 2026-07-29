"""Compare how valid chunking policies reorganize one loaded document."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from app_log import add_log_arguments, configure_from_args, console, get_logger
from rag_core import (
    Chunk,
    ChunkPolicy,
    ChunkResult,
    ChunkStrategy,
    EvidenceEligibility,
    SourceRole,
    chunk_document,
    load_document,
)

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
FIXTURE_PATH = (
    REPO_ROOT / "review_assistant" / "fixtures" / "v0" / "ingestion" / "order_rules.md"
)
log = get_logger("rag_ingestion_lab.chunking")

RELATIONSHIPS = {
    "order eligibility + exception": (
        "Only paid and completed",
        "Virtual goods",
    ),
    "API + client constraint": (
        "source_channel",
        "Flutter client",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="DocumentElement → Chunk 策略对照")
    parser.add_argument(
        "--policy",
        choices=("all", "element", "fixed", "structure", "parent-child"),
        default="all",
        help="只观察一个策略；默认比较全部策略",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=24,
        help="fixed、structure 和 child 的 token 上限",
    )
    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=4,
        help="fixed 和 child 的 overlap token 数",
    )
    parser.add_argument(
        "--parent-max-tokens",
        type=int,
        default=64,
        help="parent chunk 的 token 上限",
    )
    add_log_arguments(parser)
    args = parser.parse_args()
    configure_from_args(args)
    json_mode = args.log_format == "json" and not args.verbose

    document = load_document(
        FIXTURE_PATH,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        metadata={"knowledge_scope": "after_sale"},
    ).document
    try:
        policies = _policies(
            selected=args.policy,
            max_tokens=args.max_tokens,
            overlap_tokens=args.overlap_tokens,
            parent_max_tokens=args.parent_max_tokens,
        )
    except ValueError as exc:
        parser.error(str(exc))
    results = [(policy, chunk_document(document, policy)) for policy in policies]

    if json_mode:
        _emit_json(results)
    else:
        _render_compact(document.elements, results)
        if args.verbose:
            _render_details(results)
        console.success(
            f"{len(document.elements)} elements · {len(results)} policies · "
            f"{sum(len(result.chunks) for _, result in results)} generated chunks"
        )
        if not args.verbose:
            console.hint("使用 --verbose 查看 chunk_id、文本、parent 和来源跨度")
    return 0


def _policies(
    *,
    selected: str,
    max_tokens: int,
    overlap_tokens: int,
    parent_max_tokens: int,
) -> list[ChunkPolicy]:
    selected_names = (
        ("element", "fixed", "structure", "parent-child")
        if selected == "all"
        else (selected,)
    )
    candidates: list[ChunkPolicy] = []
    if "element" in selected_names:
        candidates.append(
            ChunkPolicy(
                name="element_baseline",
                version="1.0.0",
                strategy=ChunkStrategy.ELEMENT,
                max_tokens=max_tokens,
                parent_max_tokens=parent_max_tokens,
            )
        )
    if "fixed" in selected_names:
        candidates.append(
            ChunkPolicy(
                name="fixed_window",
                version="1.0.0",
                strategy=ChunkStrategy.FIXED_WINDOW,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                parent_max_tokens=parent_max_tokens,
            )
        )
    if "structure" in selected_names:
        candidates.append(
            ChunkPolicy(
                name="structure_aware",
                version="1.0.0",
                strategy=ChunkStrategy.STRUCTURE_AWARE,
                max_tokens=max_tokens,
                parent_max_tokens=parent_max_tokens,
            )
        )
    if "parent-child" in selected_names:
        candidates.append(
            ChunkPolicy(
                name="parent_child",
                version="1.0.0",
                strategy=ChunkStrategy.PARENT_CHILD,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                parent_max_tokens=parent_max_tokens,
            )
        )
    return candidates


def _render_compact(
    elements: Iterable[object],
    results: list[tuple[ChunkPolicy, ChunkResult]],
) -> None:
    console.title(
        "Chunking Lab",
        f"为什么解析元素不能直接等同于检索单元\nfixture={FIXTURE_PATH.name}",
    )
    console.info(
        f"Loader produced {len(tuple(elements))} source-shaped DocumentElements"
    )
    console.table(
        (
            "Policy",
            "Retrieval",
            "Parent",
            "Tokens min/median/p95/max",
            "Repeated",
            "Spans",
        ),
        (
            (
                policy.name,
                len(result.retrieval_chunks),
                len(result.parent_chunks),
                (
                    f"{result.report.min_tokens}/"
                    f"{result.report.median_tokens}/"
                    f"{result.report.p95_tokens}/"
                    f"{result.report.max_tokens}"
                ),
                (
                    f"{result.report.repeated_tokens} "
                    f"({result.report.repetition_ratio:.0%})"
                ),
                result.report.source_span_count,
            )
            for policy, result in results
        ),
    )
    console.section("Where related facts live")
    console.table(
        ("Relationship", *(policy.name for policy, _ in results)),
        (
            (
                name,
                *(_relationship_location(result, phrases) for _, result in results),
            )
            for name, phrases in RELATIONSHIPS.items()
        ),
    )
    console.info("这些状态描述内容怎样被组织，不代表某个策略已经通过真实检索评估")


def _render_details(
    results: list[tuple[ChunkPolicy, ChunkResult]],
) -> None:
    for policy, result in results:
        console.section(
            f"{policy.name} · {policy.fingerprint} · {policy.strategy.value}"
        )
        console.table(
            ("#", "Kind", "Tokens", "Parent", "Chunk ID", "Text"),
            (
                (
                    chunk.ordinal,
                    chunk.kind.value,
                    chunk.token_count,
                    chunk.parent_chunk_id or "—",
                    chunk.chunk_id,
                    " ".join(chunk.text.split())[:120],
                )
                for chunk in result.chunks
            ),
        )
        for chunk in result.chunks:
            console.field(chunk.chunk_id, f"{len(chunk.source_spans)} source spans")
            for span in chunk.source_spans:
                console.item(
                    f"{span.start_char}:{span.end_char}",
                    (
                        f"{span.element_id} · {span.locator.describe()} · "
                        f"{' '.join(span.text.split())[:100]}"
                    ),
                    indent=1,
                )


def _relationship_location(
    result: ChunkResult,
    phrases: tuple[str, str],
) -> str:
    if any(_contains_all(chunk, phrases) for chunk in result.retrieval_chunks):
        return "same retrieval chunk"
    if any(_contains_all(chunk, phrases) for chunk in result.parent_chunks):
        return "same parent"
    return "separate chunks"


def _contains_all(chunk: Chunk, phrases: tuple[str, str]) -> bool:
    return all(phrase in chunk.text for phrase in phrases)


def _emit_json(
    results: list[tuple[ChunkPolicy, ChunkResult]],
) -> None:
    for policy, result in results:
        log.info(
            "chunking.policy_observed",
            "切分策略观察完成",
            policy_name=policy.name,
            policy_version=policy.version,
            policy_fingerprint=policy.fingerprint,
            strategy=policy.strategy.value,
            retrieval_chunks=len(result.retrieval_chunks),
            parent_chunks=len(result.parent_chunks),
            min_tokens=result.report.min_tokens,
            median_tokens=result.report.median_tokens,
            p95_tokens=result.report.p95_tokens,
            max_tokens=result.report.max_tokens,
            repeated_tokens=result.report.repeated_tokens,
            repetition_ratio=result.report.repetition_ratio,
            source_spans=result.report.source_span_count,
            relationships={
                name: _relationship_location(result, phrases)
                for name, phrases in RELATIONSHIPS.items()
            },
        )
    log.success(
        "chunking.completed",
        "Chunking 策略对照完成",
        policies=len(results),
    )


if __name__ == "__main__":
    raise SystemExit(main())
