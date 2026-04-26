from rag_basics import (
    CHAPTER_KEY,
    answer_question,
    get_chapter_expectation,
    load_minimum_golden_set,
)


def _as_strings(value: object) -> tuple[str, ...]:
    """把 JSON 里的可选列表字段统一转成 tuple[str, ...]，方便后续检查。"""

    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def main() -> None:
    # 评估脚本先读取课程共享 JSON，再拿第一章预期和真实运行结果做对比。
    # 这里和 03_rag_pipeline.py 不同：
    # - 03_rag_pipeline.py 的输入来自当前命令行问题
    # - 01_minimum_eval.py 的输入来自 JSON 里逐条写好的 case["question"]
    cases = load_minimum_golden_set()
    passed = 0

    print("课程共享最小评估集")
    print("说明：这份样本会在 01-04 复用；第一章只验证路由、toy RAG 行为和最小来源边界。")

    for case in cases:
        question = str(case["question"])
        # 注意：这里不是“根据当前问题去匹配最像的 JSON case”。
        # 而是评估脚本主动遍历 JSON，每次把某一条 case 的 question
        # 直接送进 answer_question()。
        # 同一条 JSON 样本可以服务多个章节，这里只取第一章自己的预期。
        expectation = get_chapter_expectation(case, CHAPTER_KEY)
        expected_route = str(expectation["expected_route"])
        expected_used_rag = bool(expectation["expected_used_rag"])
        expected_sources = _as_strings(expectation.get("expected_sources"))
        expected_answer_points = _as_strings(expectation.get("expected_answer_points"))
        known_gap = expectation.get("known_gap")

        result = answer_question(question)
        # 第一章不做模糊打分，只检查几个具体信号：
        # route 是否正确、是否真的用了 RAG、sources 是否保留、
        # answer 是否包含本章要求出现的关键信息。
        # 例如 [来源1] 这种文本，不是固定数据库 ID，
        # 而是本次回答里用于指向“第 1 条检索结果”的临时来源标签。
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
        print(f"route: {result.route} | reason: {result.reason} | expected: {expected_route}")
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
