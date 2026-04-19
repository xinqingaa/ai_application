import argparse

from retrieval_basics import (
    InMemoryVectorStore,
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    demo_embedded_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one retrieval strategy against the demo store.")
    parser.add_argument(
        "question",
        nargs="?",
        default="退款规则是什么？",
        help="Question to retrieve against the demo store.",
    )
    parser.add_argument(
        "--strategy",
        choices=("similarity", "threshold", "mmr"),
        default="similarity",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-k", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--mmr-lambda", type=float, default=0.35)
    parser.add_argument("--filename", help="Optional filename filter.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = InMemoryVectorStore(demo_embedded_chunks(provider))
    retriever = SimpleRetriever(store=store, provider=provider)
    strategy = RetrievalStrategyConfig(
        strategy_name=args.strategy,
        top_k=args.top_k,
        candidate_k=args.candidate_k,
        score_threshold=args.threshold,
        mmr_lambda=args.mmr_lambda,
        filename_filter=args.filename,
    )
    results = retriever.retrieve(args.question, strategy)

    print(f"Question: {args.question}")
    print(
        f"Strategy: {args.strategy} top_k={args.top_k} candidate_k={args.candidate_k} "
        f"threshold={args.threshold:.2f} mmr_lambda={args.mmr_lambda:.2f}"
    )
    if args.filename:
        print(f"Filename filter: {args.filename}")

    if not results:
        print("No retrieval results.")
        return

    for result in results:
        preview = result.chunk.content[:80]
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id}"
        )
        print(
            "  metadata="
            f"filename={result.chunk.metadata['filename']} "
            f"source={result.chunk.metadata['source']} "
            f"chunk={result.chunk.metadata['chunk_index']}"
        )
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
