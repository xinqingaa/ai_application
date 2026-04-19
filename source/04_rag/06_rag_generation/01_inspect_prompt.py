import argparse

from generation_basics import DemoRetriever, inspect_prompt


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect how retrieval results become a RAG prompt.")
    parser.add_argument("question", nargs="?", default="退款规则是什么？")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.35)
    parser.add_argument("--max-chunks", type=int, default=3)
    parser.add_argument("--max-chars", type=int, default=90)
    args = parser.parse_args()

    retriever = DemoRetriever()
    inspection = inspect_prompt(
        question=args.question,
        retriever=retriever,
        top_k=args.top_k,
        min_score=args.min_score,
        max_chunks=args.max_chunks,
        max_chars_per_chunk=args.max_chars,
    )

    print(f"Question: {args.question}")
    print(f"Retrieved: {len(inspection.retrieved_results)}")
    for result in inspection.retrieved_results:
        print(
            f"- score={result.score:.3f} "
            f"filename={result.chunk.metadata['filename']} "
            f"chunk={result.chunk.metadata['chunk_index']}"
        )
        print(f"  preview={result.chunk.content}")

    print()
    print(f"Accepted for generation: {len(inspection.accepted_results)}")
    if not inspection.accepted_results:
        print("No chunks passed the min_score filter, so the model should refuse to answer.")
        return

    print()
    print("Context:")
    print(inspection.context)
    print()
    print("Prompt Preview:")
    print(inspection.prompt_preview)


if __name__ == "__main__":
    main()
