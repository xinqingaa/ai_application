import argparse

from retrieval_basics import (
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    build_demo_store,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one retrieval strategy against the demo store.")
    parser.add_argument(
        "question",
        nargs="?",
        default="购买后多久还能退款？",
        help="Question to retrieve against the demo store.",
    )
    parser.add_argument(
        "--strategy",
        choices=("similarity", "threshold", "mmr"),
        default="similarity",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-k", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--mmr-lambda", type=float, default=0.35)
    parser.add_argument("--filename", help="Optional filename filter.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = build_demo_store(provider=provider, reset_store=True)
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
    print(f"Store path: {store.config.store_path}")
    current_space = store.embedding_space()
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    print(
        f"Strategy: {args.strategy} top_k={args.top_k} candidate_k={args.candidate_k} "
        f"threshold={args.threshold:.2f} mmr_lambda={args.mmr_lambda:.2f}"
    )
    if args.filename:
        print(
            f"Filename filter: {args.filename} "
            "(Chapter 5 currently supports filename-only filtering)"
        )
    if args.strategy == "mmr":
        print("Displayed score is similarity_score; selection order comes from MMR diversification.")

    if not results:
        print("No retrieval results.")
        return

    for result in results:
        preview = result.chunk.content[:80]
        print(
            f"- similarity_score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id}"
        )
        print(
            "  metadata="
            f"filename={result.chunk.metadata['filename']} "
            f"suffix={result.chunk.metadata.get('suffix')} "
            f"source={result.chunk.metadata['source']} "
            f"chunk={result.chunk.metadata['chunk_index']} "
            f"chars={result.chunk.metadata.get('char_start')}-{result.chunk.metadata.get('char_end')}"
        )
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
