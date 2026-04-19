import argparse

from generation_basics import (
    Chapter5DemoRetriever,
    MockLLMClient,
    RagService,
    context_relevance_score,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal RAG answer generation demo.")
    parser.add_argument("question", nargs="?", default="退款规则是什么？")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-context-score", "--min-score", dest="min_context_score", type=float, default=0.35)
    parser.add_argument("--max-chunks", type=int, default=3)
    args = parser.parse_args()

    service = RagService(
        retriever=Chapter5DemoRetriever(),
        llm=MockLLMClient(),
        min_context_score=args.min_context_score,
        max_chunks=args.max_chunks,
    )
    result = service.ask(args.question, top_k=args.top_k)

    print(f"Question: {args.question}")
    print(f"Retrieved: {len(service.last_retrieved_results)}")
    for item in service.last_retrieved_results:
        context_score = context_relevance_score(args.question, item.chunk.content)
        print(
            f"- retrieval_score={item.score:.3f} "
            f"context_score={context_score:.3f} "
            f"filename={item.chunk.metadata['filename']} "
            f"chunk={item.chunk.metadata['chunk_index']}"
        )

    print()
    print(f"Accepted: {len(service.last_accepted_results)}")
    for item in service.last_accepted_results:
        context_score = context_relevance_score(args.question, item.chunk.content)
        print(
            f"- retrieval_score={item.score:.3f} "
            f"context_score={context_score:.3f} "
            f"filename={item.chunk.metadata['filename']} "
            f"source={item.chunk.metadata['source']}"
        )

    print()
    print(f"Prompt chunks: {len(service.last_prompt_results)}")
    for item in service.last_prompt_results:
        print(
            f"- filename={item.chunk.metadata['filename']} "
            f"source={item.chunk.metadata['source']} "
            f"chunk={item.chunk.metadata['chunk_index']}"
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
