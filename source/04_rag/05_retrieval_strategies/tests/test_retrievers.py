from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import (
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    average_redundancy,
    build_demo_store,
)


class RetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.store_path = Path(self.tmp_dir.name) / "retrieval_store.json"
        self.provider = LocalKeywordEmbeddingProvider()
        self.store = build_demo_store(
            provider=self.provider,
            store_path=self.store_path,
            reset_store=True,
        )
        self.retriever = SimpleRetriever(store=self.store, provider=self.provider)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_similarity_retriever_returns_relevant_chunk(self) -> None:
        results = self.retriever.retrieve(
            "购买后多久还能退款？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
        )

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.chunk_id, "refund_summary:0")

    def test_threshold_retriever_filters_out_low_score_tail(self) -> None:
        similarity = self.retriever.retrieve(
            "火星首都是什么？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
        )
        threshold = self.retriever.retrieve(
            "火星首都是什么？",
            RetrievalStrategyConfig(
                strategy_name="threshold",
                top_k=3,
                candidate_k=4,
                score_threshold=0.80,
            ),
        )

        self.assertGreaterEqual(len(similarity), len(threshold))
        self.assertFalse(threshold)

    def test_metadata_filter_applies_inside_retriever(self) -> None:
        results = self.retriever.retrieve(
            "为什么 metadata 很重要？",
            RetrievalStrategyConfig(
                strategy_name="similarity",
                top_k=3,
                candidate_k=4,
                filename_filter="metadata_rules.md",
            ),
        )

        self.assertTrue(results)
        self.assertTrue(all(item.chunk.metadata["filename"] == "metadata_rules.md" for item in results))

    def test_mmr_reduces_redundancy_relative_to_similarity(self) -> None:
        similarity = self.retriever.retrieve(
            "退款规则是什么？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
        )
        mmr = self.retriever.retrieve(
            "退款规则是什么？",
            RetrievalStrategyConfig(
                strategy_name="mmr",
                top_k=3,
                candidate_k=4,
                mmr_lambda=0.35,
            ),
        )

        self.assertLessEqual(
            average_redundancy(mmr, self.provider),
            average_redundancy(similarity, self.provider),
        )

    def test_retriever_rejects_different_embedding_space(self) -> None:
        other_provider = LocalKeywordEmbeddingProvider(model_name="concept-space-v2")
        mismatched_retriever = SimpleRetriever(store=self.store, provider=other_provider)

        with self.assertRaisesRegex(ValueError, "embedding space"):
            mismatched_retriever.retrieve(
                "购买后多久还能退款？",
                RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
            )


if __name__ == "__main__":
    unittest.main()
