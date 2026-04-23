from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import LocalKeywordEmbeddingProvider, chromadb_is_available
from retrieval_metrics import load_eval_cases
from smart_retrieval_engine import SmartRetrievalConfig, build_demo_smart_engine


class SmartRetrievalEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.store_path = Path(self.tmp_dir.name) / "retrieval_store.json"
        self.provider = LocalKeywordEmbeddingProvider()
        self.engine, _store = build_demo_smart_engine(
            backend="json",
            provider=self.provider,
            reset_store=True,
            json_store_path=self.store_path,
        )

    def test_hybrid_strategy_returns_keyword_sensitive_chunk(self) -> None:
        results = self.engine.retrieve(
            "退费申请流程",
            SmartRetrievalConfig(strategy="hybrid", top_k=3, candidate_k=4, hybrid_alpha=0.4),
        )

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.chunk_id, "refund_process:0")

    def test_engine_honors_filename_filter(self) -> None:
        results = self.engine.retrieve(
            "为什么 metadata 很重要？",
            SmartRetrievalConfig(
                strategy="hybrid",
                top_k=3,
                candidate_k=4,
                filename_filter="metadata_rules.md",
            ),
        )

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.chunk_id, "metadata:0")
        self.assertTrue(all(item.chunk.metadata["filename"] == "metadata_rules.md" for item in results))

    def test_engine_supports_optional_rerank(self) -> None:
        results = self.engine.retrieve(
            "退费申请流程",
            SmartRetrievalConfig(
                strategy="hybrid",
                top_k=2,
                candidate_k=4,
                rerank=True,
                fetch_k=5,
                rerank_top_n=2,
            ),
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk.chunk_id, "refund_process:0")
        self.assertGreaterEqual(results[0].score, results[1].score)

    def test_engine_evaluate_aggregates_fixed_eval_set(self) -> None:
        cases = load_eval_cases()
        report = self.engine.evaluate(
            cases,
            SmartRetrievalConfig(
                strategy="hybrid",
                top_k=3,
                candidate_k=4,
                rerank=True,
                fetch_k=6,
                rerank_top_n=3,
            ),
        )

        self.assertEqual(report.case_count, len(cases))
        self.assertGreater(report.recall, 0.66)
        self.assertGreater(report.mrr, 0.66)
        self.assertGreater(report.hit_rate, 0.66)


@unittest.skipUnless(chromadb_is_available(), "chromadb package is not installed.")
class SmartRetrievalEngineChromaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.persist_directory = Path(self.tmp_dir.name) / "chroma"
        self.provider = LocalKeywordEmbeddingProvider()
        self.engine, _store = build_demo_smart_engine(
            backend="chroma",
            provider=self.provider,
            reset_store=True,
            chroma_persist_directory=self.persist_directory,
        )

    def test_chroma_engine_runs_hybrid_retrieval(self) -> None:
        results = self.engine.retrieve(
            "退费申请流程",
            SmartRetrievalConfig(strategy="hybrid", top_k=3, candidate_k=4),
        )

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.chunk_id, "refund_process:0")


if __name__ == "__main__":
    unittest.main()
