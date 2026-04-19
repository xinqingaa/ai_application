import argparse

from rag_basics import answer_question, build_context, retrieve, route_question


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the minimum RAG pipeline.")
    parser.add_argument(
        "question",
        nargs="?",
        default="如何申请退款？",
        help="Question to send through the minimum RAG flow.",
    )
    args = parser.parse_args()

    route = route_question(args.question)
    final_result = answer_question(args.question)
    results = retrieve(args.question)

    print("0. 路由判断")
    print(f"   route: {route.route}")
    print(f"   reason: {route.reason}")

    print("1. 输入问题")
    print(f"   {args.question}")

    if route.route != "固定 2-step RAG":
        print("2. 本题不进入第一章的 RAG 在线链路")
        print(f"   answer: {final_result.answer}")
        print(f"   sources: {list(final_result.sources)}")
        return

    print("2. 检索结果")
    if not results:
        print("   没有命中任何知识块。")
        print("   这说明路由判断认为它该走 RAG，但当前关键词检索没有召回相关 chunk。")
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
    print(f"   answer: {final_result.answer}")
    print(f"   sources: {list(final_result.sources)}")


if __name__ == "__main__":
    main()
