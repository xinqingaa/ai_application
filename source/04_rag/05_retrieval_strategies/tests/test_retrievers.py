from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import (
    InMemoryVectorStore,
    LocalKeywordEmbeddingProvider,
    RetrievalStrategyConfig,
    SimpleRetriever,
    average_redundancy,
    demo_embedded_chunks,
)


class RetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = LocalKeywordEmbeddingProvider()
        self.store = InMemoryVectorStore(demo_embedded_chunks(self.provider))
        self.retriever = SimpleRetriever(store=self.store, provider=self.provider)

    def test_similarity_retriever_returns_relevant_chunk(self) -> None:
        results = self.retriever.retrieve(
            "退款规则是什么？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
        )

        self.assertTrue(results)
        self.assertTrue(results[0].chunk.chunk_id.startswith("refund_"))

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
                score_threshold=0.60,
            ),
        )

        self.assertGreaterEqual(len(similarity), len(threshold))
        self.assertTrue(all(item.score >= 0.60 for item in threshold))

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


if __name__ == "__main__":
    unittest.main()
