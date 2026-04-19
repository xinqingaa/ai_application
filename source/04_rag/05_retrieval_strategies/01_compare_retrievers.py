import argparse

from retrieval_basics import (
    InMemoryVectorStore,
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    average_redundancy,
    demo_embedded_chunks,
)


def print_results(strategy_name: str, results, provider) -> None:
    print(f"[{strategy_name}]")
    if not results:
        print("  no results")
        return

    print(f"  average_redundancy={average_redundancy(results, provider):.3f}")
    for result in results:
        preview = result.chunk.content[:60]
        print(
            f"  - score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"filename={result.chunk.metadata['filename']}"
        )
        print(f"    preview={preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare retrieval strategies on one question.")
    parser.add_argument(
        "question",
        nargs="?",
        default="退款规则是什么？",
        help="Question to retrieve against the demo store.",
    )
    parser.add_argument("--filename", help="Optional filename filter.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = InMemoryVectorStore(demo_embedded_chunks(provider))
    retriever = SimpleRetriever(store=store, provider=provider)

    print(f"Question: {args.question}")
    if args.filename:
        print(f"Filename filter: {args.filename}")

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
            score_threshold=0.60,
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
