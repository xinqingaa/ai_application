import argparse

from retrieval_basics import (
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    average_redundancy,
    build_demo_store,
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
    parser.add_argument("--filename", help="Optional filename filter.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = build_demo_store(provider=provider, reset_store=True)
    retriever = SimpleRetriever(store=store, provider=provider)

    print(f"Question: {args.question}")
    print(f"Store path: {store.config.store_path}")
    current_space = store.embedding_space()
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    if args.filename:
        print(
            f"Filename filter: {args.filename} "
            "(Chapter 5 currently supports filename-only filtering)"
        )
    print("Compare config: top_k=3 candidate_k=4 threshold=0.88 mmr_lambda=0.35")

    similarity = retriever.retrieve(
        args.question,
        RetrievalStrategyConfig(
            strategy_name="similarity",
            top_k=3,
            candidate_k=4,
            filename_filter=args.filename,
        ),
    )
    threshold = retriever.retrieve(
        args.question,
        RetrievalStrategyConfig(
            strategy_name="threshold",
            top_k=3,
            candidate_k=4,
            score_threshold=0.88,
            filename_filter=args.filename,
        ),
    )
    mmr = retriever.retrieve(
        args.question,
        RetrievalStrategyConfig(
            strategy_name="mmr",
            top_k=3,
            candidate_k=4,
            mmr_lambda=0.35,
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
