from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_basics import (
    CHAPTER_KEY,
    Scenario,
    answer_question,
    answer_with_rag,
    answer_without_rag,
    get_chapter_expectation,
    load_minimum_golden_set,
    recommend_solution,
    retrieve,
)

MINIMUM_GOLDEN_SET = load_minimum_golden_set()


def as_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def get_case(case_id: str) -> dict[str, object]:
    for case in MINIMUM_GOLDEN_SET:
        if case.get("case_id") == case_id:
            return case
    raise KeyError(f"missing case: {case_id}")


class RagBasicsTests(unittest.TestCase):
    def test_private_question_retrieves_refund_policy(self) -> None:
        results = retrieve("Python 系统课可以退费吗？")
        self.assertTrue(results)
        self.assertEqual(results[0].chunk.source, "refund_policy.md")

    def test_minimum_golden_set(self) -> None:
        for case in MINIMUM_GOLDEN_SET:
            with self.subTest(question=case["question"]):
                expectation = get_chapter_expectation(case, CHAPTER_KEY)
                result = answer_question(str(case["question"]))
                self.assertEqual(result.route, str(expectation["expected_route"]))
                self.assertEqual(result.used_rag, bool(expectation["expected_used_rag"]))
                for source in as_strings(expectation.get("expected_sources")):
                    self.assertIn(source, result.sources)
                for point in as_strings(expectation.get("expected_answer_points")):
                    self.assertIn(point, result.answer)

    def test_answer_with_rag_returns_sources(self) -> None:
        result = answer_with_rag("如何申请退款？")
        self.assertTrue(result.used_rag)
        self.assertIn("refund_policy.md", result.sources)
        self.assertIn("[来源1]", result.answer)

    def test_answer_without_rag_uses_generic_refusal(self) -> None:
        answer = answer_without_rag("太阳系有几颗行星？")
        self.assertNotIn("私有资料", answer)
        self.assertIn("单次调用", answer)

    def test_course_like_question_can_route_to_rag_but_still_miss_keywords(self) -> None:
        case = get_case("private_refund_synonym_gap")
        expectation = get_chapter_expectation(case, CHAPTER_KEY)
        result = answer_question(str(case["question"]))
        self.assertEqual(result.route, str(expectation["expected_route"]))
        self.assertEqual(result.used_rag, bool(expectation["expected_used_rag"]))
        for point in as_strings(expectation.get("expected_answer_points")):
            self.assertIn(point, result.answer)
        self.assertIn("known_gap", expectation)

    def test_recommend_solution_prefers_existing_system(self) -> None:
        choice, _ = recommend_solution(
            Scenario(
                name="FAQ 在 Elasticsearch 里",
                material_count="many",
                has_existing_system=True,
                structured_data=True,
                needs_citations=True,
            )
        )
        self.assertEqual(choice, "直接查现有系统")

    def test_recommend_solution_prefers_hosted_file_search_for_fast_demo(self) -> None:
        choice, _ = recommend_solution(
            Scenario(
                name="上传 10 份 PDF，快速做 Demo",
                material_count="many",
                needs_fast_validation=True,
                needs_citations=True,
            )
        )
        self.assertEqual(choice, "Hosted File Search")

    def test_recommend_solution_prefers_hybrid_rag_for_precise_terms(self) -> None:
        choice, _ = recommend_solution(
            Scenario(
                name="金融问答有大量代码和简称",
                material_count="many",
                needs_citations=True,
                knowledge_changes_often=True,
                has_precise_keywords=True,
            )
        )
        self.assertEqual(choice, "Hybrid RAG")


if __name__ == "__main__":
    unittest.main()
