from rag_basics import default_scenarios, recommend_solution


def main() -> None:
    # 这个脚本不是在回答问题，
    # 而是在演示第一章如何把“该选什么方案”写成明确的场景规则。
    print("默认顺序：长上下文 -> 直接查现有系统 -> Hosted File Search -> 固定 2-step RAG -> Hybrid RAG -> Agentic RAG")
    print()
    for index, scenario in enumerate(default_scenarios(), start=1):
        choice, reason = recommend_solution(scenario)
        print(f"{index}. 场景: {scenario.name}")
        print(f"   推荐方案: {choice}")
        print(f"   理由: {reason}")


if __name__ == "__main__":
    main()
