from retrieval_basics import (
    LocalKeywordEmbeddingProvider,
    RetrievalResult,
    RetrievalStrategyConfig,
    SimpleRetriever,
    average_redundancy,
    build_demo_store,
    evaluate_bad_case,
    load_bad_cases,
)


def summarize_results(results: list[RetrievalResult], provider: LocalKeywordEmbeddingProvider) -> str:
    top_chunk_id = results[0].chunk.chunk_id if results else "none"
    chunk_ids = [result.chunk.chunk_id for result in results]
    redundancy = average_redundancy(results, provider)
    return (
        f"top={top_chunk_id} count={len(results)} "
        f"redundancy={redundancy:.3f} chunk_ids={chunk_ids}"
    )


def main() -> None:
    provider = LocalKeywordEmbeddingProvider()
    store = build_demo_store(provider=provider, reset_store=True)
    retriever = SimpleRetriever(store=store, provider=provider)
    failures = 0

    for case in load_bad_cases():
        question = str(case["question"])
        filename = case.get("filename_filter")
        expected = str(case["expected_focus"])

        print(f"Case: {case['case_id']}")
        print(f"Question: {question}")
        print(f"Expected focus: {expected}")
        print(f"Store path: {store.config.store_path}")
        print("Regression config: top_k=3 candidate_k=4 threshold=0.80 mmr_lambda=0.35")
        if filename:
            print(f"Filename filter: {filename} (filename-only)")

        for strategy_name in ("similarity", "threshold", "mmr"):
            strategy = RetrievalStrategyConfig(
                strategy_name=strategy_name,
                top_k=3,
                candidate_k=4,
                score_threshold=0.80,
                mmr_lambda=0.35,
                filename_filter=str(filename) if filename else None,
            )
            results = retriever.retrieve(question, strategy)
            evaluation = evaluate_bad_case(case, strategy_name, results, provider)
            print(
                f"  - [{evaluation.status.upper()}] {strategy_name}: "
                f"{summarize_results(results, provider)}"
            )
            for message in evaluation.messages:
                print(f"    {message}")
            if evaluation.status == "fail":
                failures += 1
        print()

    if failures:
        raise SystemExit(f"Bad-case regression failed with {failures} failing strategy checks.")

    print("Bad-case regression passed.")


if __name__ == "__main__":
    main()
