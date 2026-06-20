from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chroma_retriever import ChromaRetriever
from retrieval_basics import (
    LocalKeywordEmbeddingProvider,
    RetrievalResult,
    RetrievalStrategyConfig,
    SimpleBM25Scorer,
    SimpleCrossReranker,
    average_redundancy,
    build_demo_chroma_store,
    chromadb_is_available,
    demo_source_chunks,
    hybrid_search,
)


@unittest.skipUnless(chromadb_is_available(), "chromadb package is not installed.")
class ChromaRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.persist_directory = Path(self.tmp_dir.name) / "chroma"
        self.provider = LocalKeywordEmbeddingProvider()
        self.store = build_demo_chroma_store(
            provider=self.provider,
            persist_directory=self.persist_directory,
            collection_name="test_retrievals",
            reset_store=True,
        )
        self.retriever = ChromaRetriever(store=self.store, provider=self.provider)

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
                candidate_k=5,
                mmr_lambda=0.35,
            ),
        )

        self.assertLessEqual(
            average_redundancy(mmr, self.provider),
            average_redundancy(similarity, self.provider),
        )

    def test_candidate_k_changes_mmr_candidate_pool(self) -> None:
        narrow_pool = self.retriever.retrieve(
            "购买后多久还能退款？",
            RetrievalStrategyConfig(
                strategy_name="mmr",
                top_k=3,
                candidate_k=3,
                mmr_lambda=0.35,
            ),
        )
        wide_pool = self.retriever.retrieve(
            "购买后多久还能退款？",
            RetrievalStrategyConfig(
                strategy_name="mmr",
                top_k=3,
                candidate_k=4,
                mmr_lambda=0.35,
            ),
        )

        narrow_ids = {item.chunk.chunk_id for item in narrow_pool}
        wide_ids = {item.chunk.chunk_id for item in wide_pool}
        self.assertNotIn("refund_process:0", narrow_ids)
        self.assertIn("refund_process:0", wide_ids)

    def test_retriever_rejects_different_embedding_space(self) -> None:
        other_provider = LocalKeywordEmbeddingProvider(model_name="concept-space-v2")
        mismatched_retriever = ChromaRetriever(store=self.store, provider=other_provider)

        with self.assertRaisesRegex(ValueError, "embedding space"):
            mismatched_retriever.retrieve(
                "购买后多久还能退款？",
                RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
            )

    # --- Hybrid search with Chroma backend ---

    def test_hybrid_search_with_chroma_retriever(self) -> None:
        vector_results = self.retriever.retrieve(
            "退费申请流程",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
        )
        corpus = demo_source_chunks()
        bm25_scorer = SimpleBM25Scorer(corpus)
        hybrid_results = hybrid_search(
            query="退费申请流程",
            vector_results=vector_results,
            bm25_scorer=bm25_scorer,
            alpha=0.5,
            top_k=3,
        )

        self.assertTrue(hybrid_results)
        hybrid_ids = {r.chunk.chunk_id for r in hybrid_results}
        self.assertIn("refund_process:0", hybrid_ids)

    # --- Reranker with Chroma backend ---

    def test_reranker_with_chroma_results(self) -> None:
        results = self.retriever.retrieve(
            "购买后多久还能退款？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=6, candidate_k=8),
        )
        reranker = SimpleCrossReranker()
        reranked = reranker.rerank("购买后多久还能退款？", results, top_n=3)

        self.assertEqual(len(reranked), 3)
        for i in range(len(reranked) - 1):
            self.assertGreaterEqual(reranked[i].score, reranked[i + 1].score)


if __name__ == "__main__":
    unittest.main()
