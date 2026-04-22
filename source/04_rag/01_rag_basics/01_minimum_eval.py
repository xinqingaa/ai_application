from rag_basics import (
    CHAPTER_KEY,
    answer_question,
    get_chapter_expectation,
    load_minimum_golden_set,
)


def _as_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def main() -> None:
    cases = load_minimum_golden_set()
    passed = 0

    print("课程共享最小评估集")
    print("说明：这份样本会在 01-04 复用；第一章只验证路由、toy RAG 行为和最小来源边界。")

    for case in cases:
        question = str(case["question"])
        expectation = get_chapter_expectation(case, CHAPTER_KEY)
        expected_route = str(expectation["expected_route"])
        expected_used_rag = bool(expectation["expected_used_rag"])
        expected_sources = _as_strings(expectation.get("expected_sources"))
        expected_answer_points = _as_strings(expectation.get("expected_answer_points"))
        known_gap = expectation.get("known_gap")

        result = answer_question(question)
        missing_sources = [source for source in expected_sources if source not in result.sources]
        missing_answer_points = [
            point for point in expected_answer_points if point not in result.answer
        ]
        case_passed = (
            result.route == expected_route
            and result.used_rag == expected_used_rag
            and not missing_sources
            and not missing_answer_points
        )
        passed += int(case_passed)

        print("=" * 72)
        print(f"case_id: {case['case_id']}")
        print(f"question: {question}")
        print(f"route: {result.route} | expected: {expected_route}")
        print(f"used_rag: {result.used_rag} | expected: {expected_used_rag}")
        print(f"sources: {list(result.sources)} | expected subset: {list(expected_sources)}")
        if expected_answer_points:
            print(f"answer must contain: {list(expected_answer_points)}")
        if known_gap:
            print(f"known_gap: {known_gap}")
        if missing_sources:
            print(f"missing_sources: {missing_sources}")
        if missing_answer_points:
            print(f"missing_answer_points: {missing_answer_points}")
        print(f"result: {'PASS' if case_passed else 'FAIL'}")

    print("=" * 72)
    print(f"summary: {passed}/{len(cases)} cases passed for {CHAPTER_KEY}")


if __name__ == "__main__":
    main()
