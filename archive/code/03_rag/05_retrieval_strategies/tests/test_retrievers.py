from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_basics import (
    LocalKeywordEmbeddingProvider,
    RetrievalResult,
    RetrievalStrategyConfig,
    SimpleBM25Scorer,
    SimpleCrossReranker,
    SimpleRetriever,
    average_redundancy,
    build_demo_store,
    demo_source_chunks,
    hybrid_search,
    strategy_from_case,
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

    def test_strategy_from_case_applies_strategy_specific_overrides(self) -> None:
        strategy = strategy_from_case(
            {
                "filename_filter": "metadata_rules.md",
                "strategy_configs": {
                    "mmr": {
                        "candidate_k": 5,
                        "mmr_lambda": 0.20,
                    }
                },
            },
            "mmr",
        )

        self.assertEqual(strategy.candidate_k, 5)
        self.assertAlmostEqual(strategy.mmr_lambda, 0.20, places=6)
        self.assertEqual(strategy.filename_filter, "metadata_rules.md")

    def test_retriever_rejects_different_embedding_space(self) -> None:
        other_provider = LocalKeywordEmbeddingProvider(model_name="concept-space-v2")
        mismatched_retriever = SimpleRetriever(store=self.store, provider=other_provider)

        with self.assertRaisesRegex(ValueError, "embedding space"):
            mismatched_retriever.retrieve(
                "购买后多久还能退款？",
                RetrievalStrategyConfig(strategy_name="similarity", top_k=3, candidate_k=4),
            )

    # --- BM25 tests ---

    def test_bm25_scorer_returns_keyword_match_higher(self) -> None:
        corpus = demo_source_chunks()
        scorer = SimpleBM25Scorer(corpus)
        results = scorer.score("退费申请流程")

        self.assertTrue(results)
        top_chunk, top_score = results[0]
        self.assertEqual(top_chunk.chunk_id, "refund_process:0")
        self.assertGreater(top_score, 0.0)

    def test_bm25_scorer_empty_query(self) -> None:
        corpus = demo_source_chunks()
        scorer = SimpleBM25Scorer(corpus)
        results = scorer.score("")

        self.assertEqual(len(results), len(corpus))
        for _chunk, score in results:
            self.assertEqual(score, 0.0)

    # --- Hybrid search tests ---

    def test_hybrid_search_combines_both_sources(self) -> None:
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

    def test_hybrid_alpha_zero_equals_bm25_only(self) -> None:
        vector_results = self.retriever.retrieve(
            "退费申请流程",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=5, candidate_k=8),
        )
        corpus = demo_source_chunks()
        bm25_scorer = SimpleBM25Scorer(corpus)

        hybrid_results = hybrid_search(
            query="退费申请流程",
            vector_results=vector_results,
            bm25_scorer=bm25_scorer,
            alpha=0.0,
            top_k=3,
        )
        bm25_top = [chunk.chunk_id for chunk, _ in bm25_scorer.score("退费申请流程")[:3]]
        hybrid_top = [r.chunk.chunk_id for r in hybrid_results]

        self.assertEqual(hybrid_top, bm25_top)

    # --- Reranker tests ---

    def test_reranker_returns_correct_count(self) -> None:
        results = self.retriever.retrieve(
            "购买后多久还能退款？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=6, candidate_k=8),
        )
        reranker = SimpleCrossReranker()
        reranked = reranker.rerank("购买后多久还能退款？", results, top_n=3)

        self.assertEqual(len(reranked), 3)

    def test_reranker_scores_are_descending(self) -> None:
        results = self.retriever.retrieve(
            "购买后多久还能退款？",
            RetrievalStrategyConfig(strategy_name="similarity", top_k=6, candidate_k=8),
        )
        reranker = SimpleCrossReranker()
        reranked = reranker.rerank("购买后多久还能退款？", results)

        for i in range(len(reranked) - 1):
            self.assertGreaterEqual(reranked[i].score, reranked[i + 1].score)

    def test_reranker_prefers_exact_keyword_match(self) -> None:
        candidates = [
            RetrievalResult(chunk=demo_source_chunks()[7], score=0.9),  # embedding_notes
            RetrievalResult(chunk=demo_source_chunks()[3], score=0.5),  # refund_process
        ]
        reranker = SimpleCrossReranker()
        reranked = reranker.rerank("退费申请流程", candidates, top_n=2)

        self.assertEqual(reranked[0].chunk.chunk_id, "refund_process:0")


if __name__ == "__main__":
    unittest.main()
