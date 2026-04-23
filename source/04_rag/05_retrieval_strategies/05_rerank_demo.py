"""05_rerank_demo.py — 两阶段检索（Rerank）演示

对应文档: docs/04_rag/05_retrieval_strategies.md  「4. Rerank 重排序」

教学目标:
- 看清"先粗筛再精排"的两阶段架构
- 理解为什么向量检索是粗筛，Rerank 是精排
- 对比有无 Rerank 的结果顺序变化

当前使用 SimpleCrossReranker（关键词交叉 F1），仅用于教学。
真实 Reranker 应使用 cross-encoder 模型，如:
  - Cohere Rerank API
  - BAAI/bge-reranker-large（本地）
  - 阿里云百炼 Reranker

运行示例:
    python 05_rerank_demo.py --backend json --reset
    python 05_rerank_demo.py --backend chroma --reset
    python 05_rerank_demo.py "购买后多久还能退款？" --backend chroma --fetch-k 6 --top-n 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import (
    DEFAULT_TOP_K,
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleCrossReranker,
    build_demo_retriever,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="两阶段检索（Rerank）演示")
    parser.add_argument("question", nargs="?", default="购买后多久还能退款？")
    parser.add_argument("--backend", choices=("json", "chroma"), default="chroma")
    parser.add_argument(
        "--fetch-k", type=int, default=6,
        help="第一阶段粗筛召回数量（向量检索 top-K）",
    )
    parser.add_argument(
        "--top-n", type=int, default=DEFAULT_TOP_K,
        help="第二阶段精排后保留数量",
    )
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    retriever, _store = build_demo_retriever(
        backend=args.backend,
        provider=provider,
        reset_store=args.reset,
    )

    # 第一阶段：向量检索粗筛（召回更多候选）
    strategy = RetrievalStrategyConfig(
        strategy_name="similarity",
        top_k=args.fetch_k,
        candidate_k=max(args.fetch_k, args.fetch_k + 2),
    )
    coarse_results = retriever.retrieve(args.question, strategy)

    # 第二阶段：Rerank 精排
    reranker = SimpleCrossReranker()
    reranked_results = reranker.rerank(
        query=args.question,
        candidates=coarse_results,
        top_n=args.top_n,
    )

    # --- 输出 ---
    print(f"Question: {args.question}")
    print(f"Backend: {args.backend}")
    print(f"两阶段架构: 向量粗筛 top-{args.fetch_k} → Rerank 精排 top-{args.top_n}")
    print()

    print(f"[Stage 1: 向量粗筛] fetch_k={args.fetch_k}")
    for i, r in enumerate(coarse_results):
        print(f"  #{i + 1}  vector_score={r.score:.4f}  chunk_id={r.chunk.chunk_id}")
        print(f"       preview={r.chunk.content[:60]}...")
    print()

    print(f"[Stage 2: Rerank 精排] top_n={args.top_n}")
    for i, r in enumerate(reranked_results):
        print(f"  #{i + 1}  rerank_score={r.score:.4f}  chunk_id={r.chunk.chunk_id}")
        print(f"       preview={r.chunk.content[:60]}...")
    print()

    # 对比变化
    coarse_ids = [r.chunk.chunk_id for r in coarse_results[: args.top_n]]
    reranked_ids = [r.chunk.chunk_id for r in reranked_results]
    if coarse_ids != reranked_ids:
        print("[变化] Rerank 改变了排序:")
        print(f"  粗筛 top-{args.top_n}: {coarse_ids}")
        print(f"  精排 top-{args.top_n}: {reranked_ids}")
    else:
        print("[无变化] Rerank 未改变 top-N 排序（对当前 toy reranker 和 demo 语料属正常现象）")

    print()
    print("注意: 当前使用 SimpleCrossReranker（关键词 F1），仅用于教学。")
    print("真实 Reranker 使用 cross-encoder 模型，效果远强于此。")


if __name__ == "__main__":
    main()
