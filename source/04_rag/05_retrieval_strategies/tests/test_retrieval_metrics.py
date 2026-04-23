from pathlib import Path
import json
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import RetrievalResult, demo_source_chunks
from retrieval_metrics import (
    evaluate_retrieval_cases,
    hit_rate,
    load_eval_cases,
    recall_at_k,
    reciprocal_rank,
    RetrievalEvalCase,
)


class RetrievalMetricsTests(unittest.TestCase):
    def test_recall_mrr_and_hit_rate(self) -> None:
        chunks = demo_source_chunks()
        results = [
            RetrievalResult(chunk=chunks[7], score=0.9),  # embedding
            RetrievalResult(chunk=chunks[3], score=0.8),  # refund_process
            RetrievalResult(chunk=chunks[1], score=0.7),  # refund_summary
        ]

        self.assertAlmostEqual(recall_at_k(results, ["refund_process:0", "refund_summary:0"]), 1.0)
        self.assertAlmostEqual(reciprocal_rank(results, ["refund_process:0"]), 0.5)
        self.assertEqual(hit_rate(results, ["refund_process:0"]), 1.0)

    def test_load_eval_cases(self) -> None:
        payload = [
            {
                "case_id": "metadata_case",
                "question": "为什么 metadata 很重要？",
                "expected_chunk_ids": ["metadata:0"],
                "filename_filter": "metadata_rules.md",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "cases.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            cases = load_eval_cases(path)

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].case_id, "metadata_case")
        self.assertEqual(cases[0].filename_filter, "metadata_rules.md")

    def test_evaluate_retrieval_cases_aggregates_metrics(self) -> None:
        chunks = demo_source_chunks()
        cases = [
            RetrievalEvalCase(
                case_id="refund_process",
                question="退费申请流程",
                expected_chunk_ids=("refund_process:0",),
            ),
            RetrievalEvalCase(
                case_id="metadata",
                question="为什么 metadata 很重要？",
                expected_chunk_ids=("metadata:0",),
            ),
        ]
        canned_results = {
            "refund_process": [
                RetrievalResult(chunk=chunks[3], score=0.9),
                RetrievalResult(chunk=chunks[1], score=0.6),
            ],
            "metadata": [
                RetrievalResult(chunk=chunks[5], score=0.95),
            ],
        }

        report = evaluate_retrieval_cases(
            cases,
            lambda case: canned_results[case.case_id],
        )

        self.assertEqual(report.case_count, 2)
        self.assertAlmostEqual(report.recall, 1.0)
        self.assertAlmostEqual(report.mrr, 1.0)
        self.assertAlmostEqual(report.hit_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
