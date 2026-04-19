import argparse

from generation_basics import DemoRetriever, MockLLMClient, RagService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal RAG answer generation demo.")
    parser.add_argument("question", nargs="?", default="退款规则是什么？")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.35)
    args = parser.parse_args()

    service = RagService(
        retriever=DemoRetriever(),
        llm=MockLLMClient(),
        min_source_score=args.min_score,
    )
    result = service.ask(args.question, top_k=args.top_k)

    print(f"Question: {args.question}")
    print(f"Retrieved: {len(service.last_retrieved_results)}")
    for item in service.last_retrieved_results:
        print(
            f"- score={item.score:.3f} "
            f"filename={item.chunk.metadata['filename']} "
            f"chunk={item.chunk.metadata['chunk_index']}"
        )

    print()
    print(f"Accepted: {len(service.last_accepted_results)}")
    for item in service.last_accepted_results:
        print(
            f"- score={item.score:.3f} "
            f"filename={item.chunk.metadata['filename']} "
            f"source={item.chunk.metadata['source']}"
        )

    print()
    print("Answer:")
    print(result.answer)

    print()
    print("Sources:")
    if not result.sources:
        print("- none")
    for source in result.sources:
        print(
            f"- filename={source.metadata['filename']} "
            f"source={source.metadata['source']} "
            f"chunk={source.metadata['chunk_index']}"
        )


if __name__ == "__main__":
    main()
