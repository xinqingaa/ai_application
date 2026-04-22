from retrieval_basics import (
    EmbeddingProvider,
    RetrievalResult,
    average_redundancy,
    build_demo_retriever,
    evaluate_bad_case,
    load_bad_cases,
    strategy_from_case,
)


def summarize_results(results: list[RetrievalResult], provider: EmbeddingProvider) -> str:
    top_chunk_id = results[0].chunk.chunk_id if results else "none"
    chunk_ids = [result.chunk.chunk_id for result in results]
    redundancy = average_redundancy(results, provider)
    return (
        f"top={top_chunk_id} count={len(results)} "
        f"redundancy={redundancy:.3f} chunk_ids={chunk_ids}"
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run Chapter 5 bad-case regression.")
    parser.add_argument(
        "--backend",
        choices=("json", "chroma"),
        default="chroma",
        help="Retriever backend to evaluate. Chapter 5 defaults to the real Chroma path.",
    )
    parser.add_argument("--reset", action="store_true", help="Reset the selected backend first.")
    args = parser.parse_args()

    retriever, store = build_demo_retriever(
        args.backend,
        reset_store=args.reset,
    )
    provider = retriever.provider
    failures = 0

    for case in load_bad_cases():
        question = str(case["question"])
        filename = case.get("filename_filter")
        expected = str(case["expected_focus"])

        print(f"Case: {case['case_id']}")
        print(f"Question: {question}")
        print(f"Expected focus: {expected}")
        print(f"Backend: {args.backend}")
        if args.backend == "json":
            print(f"Store path: {store.config.store_path}")
        else:
            print(f"Persist dir: {store.persist_directory}")
            print(f"Collection: {store.collection_name}")
        if filename:
            print(f"Filename filter: {filename} (filename-only)")

        for strategy_name in ("similarity", "threshold", "mmr"):
            strategy = strategy_from_case(case, strategy_name)
            print(
                "  config: "
                f"top_k={strategy.top_k} candidate_k={strategy.candidate_k} "
                f"threshold={strategy.score_threshold:.2f} mmr_lambda={strategy.mmr_lambda:.2f}"
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
