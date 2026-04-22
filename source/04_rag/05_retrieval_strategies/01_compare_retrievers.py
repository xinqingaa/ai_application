import argparse

from retrieval_basics import (
    average_redundancy,
    build_demo_retriever,
    RetrievalStrategyConfig,
)


def print_results(strategy_name: str, results, provider) -> None:
    print(f"[{strategy_name}]")
    if not results:
        print("  no results")
        return

    if strategy_name == "mmr":
        print("  note=selection_order uses MMR diversification; displayed score is similarity_score")
    print(f"  average_redundancy={average_redundancy(results, provider):.3f}")
    for result in results:
        preview = result.chunk.content[:60]
        print(
            f"  - similarity_score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id} filename={result.chunk.metadata['filename']}"
        )
        print(f"    preview={preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare retrieval strategies on one question.")
    parser.add_argument(
        "question",
        nargs="?",
        default="购买后多久还能退款？",
        help="Question to retrieve against the demo store.",
    )
    parser.add_argument(
        "--backend",
        choices=("json", "chroma"),
        default="chroma",
        help="Retriever backend to compare. Chapter 5 defaults to the real Chroma path.",
    )
    parser.add_argument("--filename", help="Optional filename filter.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-k", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--mmr-lambda", type=float, default=0.35)
    parser.add_argument("--reset", action="store_true", help="Reset the selected backend first.")
    args = parser.parse_args()

    retriever, store = build_demo_retriever(
        args.backend,
        reset_store=args.reset,
    )
    provider = retriever.provider

    print(f"Question: {args.question}")
    print(f"Backend: {args.backend}")
    if args.backend == "json":
        print(f"Store path: {store.config.store_path}")
    else:
        print(f"Persist dir: {store.persist_directory}")
        print(f"Collection: {store.collection_name}")
    current_space = store.embedding_space()
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    if args.filename:
        print(
            f"Filename filter: {args.filename} "
            "(Chapter 5 currently supports filename-only filtering)"
        )
    print(
        "Compare config: "
        f"top_k={args.top_k} candidate_k={args.candidate_k} "
        f"threshold={args.threshold:.2f} mmr_lambda={args.mmr_lambda:.2f}"
    )

    similarity = retriever.retrieve(
        args.question,
        RetrievalStrategyConfig(
            strategy_name="similarity",
            top_k=args.top_k,
            candidate_k=args.candidate_k,
            filename_filter=args.filename,
        ),
    )
    threshold = retriever.retrieve(
        args.question,
        RetrievalStrategyConfig(
            strategy_name="threshold",
            top_k=args.top_k,
            candidate_k=args.candidate_k,
            score_threshold=args.threshold,
            filename_filter=args.filename,
        ),
    )
    mmr = retriever.retrieve(
        args.question,
        RetrievalStrategyConfig(
            strategy_name="mmr",
            top_k=args.top_k,
            candidate_k=args.candidate_k,
            mmr_lambda=args.mmr_lambda,
            filename_filter=args.filename,
        ),
    )

    print_results("similarity", similarity, provider)
    print()
    print_results("threshold", threshold, provider)
    print()
    print_results("mmr", mmr, provider)


if __name__ == "__main__":
    main()
