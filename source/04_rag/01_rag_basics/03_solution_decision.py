from rag_basics import default_scenarios, recommend_solution


def main() -> None:
    for index, scenario in enumerate(default_scenarios(), start=1):
        choice, reason = recommend_solution(scenario)
        print(f"{index}. 场景: {scenario.name}")
        print(f"   推荐方案: {choice}")
        print(f"   理由: {reason}")


if __name__ == "__main__":
    main()
