import argparse

from rag_basics import answer_with_rag, build_context, retrieve


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the minimum RAG pipeline.")
    parser.add_argument(
        "question",
        nargs="?",
        default="如何申请退款？",
        help="Question to send through the minimum RAG flow.",
    )
    args = parser.parse_args()

    results = retrieve(args.question)
    answer = answer_with_rag(args.question)

    print("1. 输入问题")
    print(f"   {args.question}")

    print("2. 检索结果")
    if not results:
        print("   没有命中任何知识块。")
    else:
        for index, result in enumerate(results, start=1):
            matched = ", ".join(result.matched_keywords)
            print(
                f"   [S{index}] score={result.score:.2f} "
                f"source={result.chunk.source} matched={matched}"
            )

    print("3. 送入回答阶段的上下文")
    print(build_context(results))

    print("4. 输出")
    print(f"   answer: {answer.answer}")
    print(f"   sources: {list(answer.sources)}")


if __name__ == "__main__":
    main()
