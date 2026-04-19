from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_basics import Scenario, answer_with_rag, answer_without_rag, recommend_solution, retrieve


class RagBasicsTests(unittest.TestCase):
    def test_private_question_retrieves_refund_policy(self) -> None:
        results = retrieve("Python 系统课可以退费吗？")
        self.assertTrue(results)
        self.assertEqual(results[0].chunk.source, "refund_policy.md")

    def test_answer_with_rag_returns_sources(self) -> None:
        result = answer_with_rag("如何申请退款？")
        self.assertTrue(result.used_rag)
        self.assertIn("refund_policy.md", result.sources)
        self.assertIn("[S1]", result.answer)

    def test_answer_without_rag_refuses_private_knowledge(self) -> None:
        answer = answer_without_rag("课程可以退费吗？")
        self.assertIn("私有资料", answer)

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


if __name__ == "__main__":
    unittest.main()
