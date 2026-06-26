from rag_basics import answer_question, answer_without_rag


def print_case(question: str) -> None:
    # 把同一个问题分别走两条路径打印出来：
    # 1. 不走 RAG 的基线回答
    # 2. 本章带路由判断的回答链路
    result = answer_question(question)

    print("=" * 72)
    print(f"问题: {question}")
    print(f"只做单次模型调用: {answer_without_rag(question)}")
    print(f"系统路由: {result.route}")
    print(f"路由理由: {result.reason}")
    print(f"最终回答: {result.answer}")
    print(f"来源: {list(result.sources) if result.sources else '无'}")


def main() -> None:
    # 这三个问题故意覆盖第一章最核心的三条路线。
    print("示例 1：课程私有知识")
    print_case("Python 系统课可以退费吗？")

    print()
    print("示例 2：通用常识")
    print_case("法国首都是什么？")

    print()
    print("示例 3：结构化系统查询")
    print_case("订单 1024 的状态是什么？")

    print()
    print("示例 4：缺乏上下文")
    print_case("本项目里用了什么python库？")


if __name__ == "__main__":
    main()
