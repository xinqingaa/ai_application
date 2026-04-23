"""06_smart_retrieval_engine.py — 统一检索引擎演示

对应文档: docs/04_rag/05_retrieval_strategies.md  「6. 综合案例：智能检索引擎」
"""

from __future__ import annotations

import argparse
from pathlib import Path

from retrieval_metrics import DEFAULT_RETRIEVAL_EVAL_PATH, load_eval_cases
from smart_retrieval_engine import SmartRetrievalConfig, build_demo_smart_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="统一检索引擎演示")
    parser.add_argument("question", nargs="?", default="退费申请流程")
    parser.add_argument("--backend", choices=("json", "chroma"), default="chroma")
    parser.add_argument(
        "--strategy",
        choices=("similarity", "threshold", "mmr", "hybrid"),
        default="hybrid",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-k", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--mmr-lambda", type=float, default=0.35)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--filename", help="Optional filename filter.")
    parser.add_argument("--rerank", action="store_true")
    parser.add_argument("--fetch-k", type=int, default=6)
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--eval-path", default=str(DEFAULT_RETRIEVAL_EVAL_PATH))
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    engine, store = build_demo_smart_engine(
        backend=args.backend,
        reset_store=args.reset,
    )
    config = SmartRetrievalConfig(
        strategy=args.strategy,
        top_k=args.top_k,
        candidate_k=args.candidate_k,
        score_threshold=args.threshold,
        mmr_lambda=args.mmr_lambda,
        hybrid_alpha=args.alpha,
        filename_filter=args.filename,
        rerank=args.rerank,
        fetch_k=args.fetch_k,
        rerank_top_n=args.top_n,
    )

    print(f"Backend: {args.backend}")
    if args.backend == "json":
        print(f"Store path: {store.config.store_path}")
    else:
        print(f"Persist dir: {store.persist_directory}")
        print(f"Collection: {store.collection_name}")
    print(
        f"Config: strategy={config.strategy} top_k={config.top_k} "
        f"candidate_k={config.candidate_k} alpha={config.hybrid_alpha:.2f} "
        f"rerank={config.rerank}"
    )
    if config.filename_filter:
        print(f"Filename filter: {config.filename_filter}")
    print()

    if args.evaluate:
        cases = load_eval_cases(Path(args.eval_path))
        report = engine.evaluate(cases, config)
        print(
            f"[Evaluation] cases={report.case_count} "
            f"recall={report.recall:.3f} mrr={report.mrr:.3f} hit_rate={report.hit_rate:.3f}"
        )
        for case in report.cases:
            print(
                f"  - {case.case_id}: recall={case.recall:.3f} "
                f"rr={case.reciprocal_rank:.3f} hit={case.hit_rate:.0f} "
                f"chunk_ids={list(case.retrieved_chunk_ids)}"
            )
        return

    results = engine.retrieve(args.question, config)
    print(f"Question: {args.question}")
    if not results:
        print("No retrieval results.")
        return

    for result in results:
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"filename={result.chunk.metadata.get('filename')}"
        )
        print(f"  preview={result.chunk.content[:80]}")


if __name__ == "__main__":
    main()
