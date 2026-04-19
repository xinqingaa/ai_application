from rag_basics import answer_with_rag, answer_without_rag


def print_case(question: str) -> None:
    rag_result = answer_with_rag(question)

    print("=" * 72)
    print(f"问题: {question}")
    print(f"不接 RAG: {answer_without_rag(question)}")
    print(f"接入 RAG: {rag_result.answer}")
    print(f"来源: {list(rag_result.sources) if rag_result.sources else '无'}")


def main() -> None:
    print("示例 1：课程私有知识")
    print_case("Python 系统课可以退费吗？")

    print()
    print("示例 2：通用常识")
    print_case("法国首都是什么？")


if __name__ == "__main__":
    main()
