from retrieval_basics import (
    InMemoryVectorStore,
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    load_bad_cases,
    demo_embedded_chunks,
)


def main() -> None:
    provider = LocalKeywordEmbeddingProvider()
    store = InMemoryVectorStore(demo_embedded_chunks(provider))
    retriever = SimpleRetriever(store=store, provider=provider)

    for case in load_bad_cases():
        question = str(case["question"])
        filename = case.get("filename_filter")
        expected = str(case["expected_focus"])

        print(f"Case: {case['case_id']}")
        print(f"Question: {question}")
        print(f"Expected focus: {expected}")
        if filename:
            print(f"Filename filter: {filename}")

        for strategy_name in ("similarity", "threshold", "mmr"):
            strategy = RetrievalStrategyConfig(
                strategy_name=strategy_name,
                top_k=3,
                candidate_k=4,
                score_threshold=0.60,
                mmr_lambda=0.35,
                filename_filter=str(filename) if filename else None,
            )
            results = retriever.retrieve(question, strategy)
            top = results[0].chunk.chunk_id if results else "none"
            print(f"  - {strategy_name}: top={top} count={len(results)}")
        print()


if __name__ == "__main__":
    main()
