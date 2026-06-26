import argparse

from rag_basics import answer_question, build_context, retrieve, route_question


def main() -> None:
    # 这个脚本只负责演示“单次在线问题”怎么流过最小 RAG 链路。
    # 它不会读取 minimum_golden_set.json，也不会去 JSON 里找“最像的一条样本”。
    # 当前这次运行到底处理什么问题，只取决于命令行传入的 question。
    # argparse 不是“Python 内置对象”，而是 Python 标准库里的命令行参数解析模块。
    # ArgumentParser 的作用是：
    # 1. 定义这个脚本允许接收哪些命令行参数
    # 2. 自动处理默认值、帮助信息和参数解析
    # 3. 把解析结果整理成 args 对象，后面就可以用 args.question 直接取值
    parser = argparse.ArgumentParser(description="观察第一章最小 RAG 链路的各个阶段。")
    parser.add_argument(
        "question",
        nargs="?",
        default="如何申请退款？",
        # 这里定义了一个位置参数 question。
        # nargs="?" 表示这个参数是“可选的 0 或 1 个值”：
        # - 如果运行 python 03_rag_pipeline.py "Python 系统课可以退费吗？"
        #   那么 args.question 就是命令行里传入的问题
        # - 如果什么都不传
        #   那么 args.question 会使用下面的 default 默认值
        help="要送进最小 RAG 流程里的问题；不传时使用默认问题。",
    )
    # parse_args() 会真正去读取命令行输入，并返回一个 Namespace 对象。
    # 在这个脚本里，最关心的字段就是 args.question。
    args = parser.parse_args()

    # 把同一个问题拆成几个阶段分别观察，
    # 这样既能看到中间数据，也能看到最终结果。
    # 这里的 args.question 就是在线链路的唯一输入。
    route = route_question(args.question)
    final_result = answer_question(args.question)
    results = retrieve(args.question)

    print("0. 路由判断")
    print(f"   route: {route.route}")
    print(f"   reason: {route.reason}")

    print("1. 输入问题")
    print(f"   {args.question}")

    if route.route != "固定 2-step RAG":
        # 这个分支和 RAG 分支一样重要：
        # 第一章要强调很多问题一开始就不该进入检索链路。
        print("2. 本题不进入第一章的 RAG 在线链路")
        print(f"   answer: {final_result.answer}")
        print(f"   sources: {list(final_result.sources)}")
        return

    print("2. 检索结果")
    if not results:
        print("   没有命中任何知识块。")
        # 这里是一个很有教学价值的对比：
        # 路由判断认为应该尝试 RAG，但检索阶段依然可能什么都召回不到，
        # 所以 used_rag 仍然会是 false。
        print("   这说明路由判断认为它该走 RAG，但当前关键词检索没有召回相关 chunk。")
    else:
        for index, result in enumerate(results, start=1):
            matched = ", ".join(result.matched_keywords)
            print(
                f"   [来源{index}] score={result.score:.2f} "
                f"source={result.chunk.source} matched={matched}"
            )

    print("3. 送入回答阶段的上下文")
    print(build_context(results))

    print("4. 输出")
    print(f"   answer: {final_result.answer}")
    print(f"   sources: {list(final_result.sources)}")


if __name__ == "__main__":
    main()
