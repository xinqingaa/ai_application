from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.evaluation.evaluator import summarize_samples
from app.schemas import EvalSample


class ScaffoldTests(unittest.TestCase):
    def test_settings_defaults(self) -> None:
        self.assertEqual(settings.project_name, "rag_lab")
        self.assertGreater(settings.default_chunk_size, settings.default_chunk_overlap)

    def test_evaluation_summary_counts_samples(self) -> None:
        summary = summarize_samples(
            [
                EvalSample(
                    question="What is RAG?",
                    expected_answer="Retrieval-Augmented Generation",
                    expected_sources=["outline.md"],
                )
            ]
        )
        self.assertEqual(summary["total_samples"], 1)
        self.assertEqual(summary["samples_with_expected_sources"], 1)


if __name__ == "__main__":
    unittest.main()
