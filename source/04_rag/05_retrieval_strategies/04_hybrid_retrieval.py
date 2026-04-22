"""04_hybrid_retrieval.py — 混合检索演示

对应文档: docs/04_rag/05_retrieval_strategies.md  第 6 节「混合检索」

教学目标:
- 看清纯向量检索和纯 BM25 各自的优势与盲区
- 理解混合检索如何取长补短
- 通过 alpha 参数观察两路分数的权重变化

运行示例:
    python 04_hybrid_retrieval.py --backend json --reset
    python 04_hybrid_retrieval.py --backend chroma --reset
    python 04_hybrid_retrieval.py "退费申请流程" --backend chroma --alpha 0.3
    python 04_hybrid_retrieval.py "购买后多久还能退款？" --alpha 0.7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import (
    DEFAULT_HYBRID_ALPHA,
    DEFAULT_TOP_K,
    DEFAULT_CANDIDATE_K,
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleBM25Scorer,
    build_demo_retriever,
    demo_source_chunks,
    hybrid_search,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="混合检索演示：向量 + BM25")
    parser.add_argument("question", nargs="?", default="退费申请流程")
    parser.add_argument("--backend", choices=("json", "chroma"), default="chroma")
    parser.add_argument("--alpha", type=float, default=DEFAULT_HYBRID_ALPHA)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--candidate-k", type=int, default=DEFAULT_CANDIDATE_K)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    retriever, _store = build_demo_retriever(
        backend=args.backend,
        provider=provider,
        reset_store=args.reset,
    )

    strategy = RetrievalStrategyConfig(
        strategy_name="similarity",
        top_k=args.top_k,
        candidate_k=args.candidate_k,
    )

    # 1. 纯向量检索
    vector_results = retriever.retrieve(args.question, strategy)

    # 2. 纯 BM25
    corpus = demo_source_chunks()
    bm25_scorer = SimpleBM25Scorer(corpus)
    bm25_results = bm25_scorer.score(args.question)

    # 3. 混合检索
    hybrid_results = hybrid_search(
        query=args.question,
        vector_results=vector_results,
        bm25_scorer=bm25_scorer,
        alpha=args.alpha,
        top_k=args.top_k,
    )

    # --- 输出 ---
    print(f"Question: {args.question}")
    print(f"Backend: {args.backend}")
    print(f"Alpha: {args.alpha} (越大越偏语义，越小越偏关键词)")
    print()

    print(f"[vector-only] top_k={args.top_k}")
    for r in vector_results:
        print(f"  score={r.score:.4f}  chunk_id={r.chunk.chunk_id}")
        print(f"    preview={r.chunk.content[:60]}...")
    print()

    print(f"[bm25-only] top {args.top_k}")
    for chunk, score in bm25_results[: args.top_k]:
        print(f"  score={score:.4f}  chunk_id={chunk.chunk_id}")
        print(f"    preview={chunk.content[:60]}...")
    print()

    print(f"[hybrid] alpha={args.alpha} top_k={args.top_k}")
    for r in hybrid_results:
        print(f"  hybrid_score={r.score:.4f}  chunk_id={r.chunk.chunk_id}")
        print(f"    preview={r.chunk.content[:60]}...")


if __name__ == "__main__":
    main()
