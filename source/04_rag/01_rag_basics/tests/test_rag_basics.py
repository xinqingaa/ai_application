from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_basics import (
    Scenario,
    answer_question,
    answer_with_rag,
    answer_without_rag,
    recommend_solution,
    retrieve,
)

MINI_GOLDEN_SET = [
    {
        "question": "法国首都是什么？",
        "expected_route": "直接回答",
        "expected_sources": (),
        "expected_used_rag": False,
    },
    {
        "question": "订单 1024 的状态是什么？",
        "expected_route": "直接查现有系统",
        "expected_sources": ("orders_table",),
        "expected_used_rag": False,
    },
    {
        "question": "Python 系统课可以退费吗？",
        "expected_route": "固定 2-step RAG",
        "expected_sources": ("refund_policy.md",),
        "expected_used_rag": True,
    },
]


class RagBasicsTests(unittest.TestCase):
    def test_private_question_retrieves_refund_policy(self) -> None:
        results = retrieve("Python 系统课可以退费吗？")
        self.assertTrue(results)
        self.assertEqual(results[0].chunk.source, "refund_policy.md")

    def test_minimum_golden_set(self) -> None:
        for case in MINI_GOLDEN_SET:
            with self.subTest(question=case["question"]):
                result = answer_question(case["question"])
                self.assertEqual(result.route, case["expected_route"])
                self.assertEqual(result.used_rag, case["expected_used_rag"])
                for source in case["expected_sources"]:
                    self.assertIn(source, result.sources)

    def test_answer_with_rag_returns_sources(self) -> None:
        result = answer_with_rag("如何申请退款？")
        self.assertTrue(result.used_rag)
        self.assertIn("refund_policy.md", result.sources)
        self.assertIn("[S1]", result.answer)

    def test_answer_without_rag_uses_generic_refusal(self) -> None:
        answer = answer_without_rag("太阳系有几颗行星？")
        self.assertNotIn("私有资料", answer)
        self.assertIn("单次调用", answer)

    def test_course_like_question_can_route_to_rag_but_still_miss_keywords(self) -> None:
        result = answer_question("Python 系统课可以退钱吗？")
        self.assertEqual(result.route, "固定 2-step RAG")
        self.assertFalse(result.used_rag)
        self.assertIn("没有命中", result.answer)

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
