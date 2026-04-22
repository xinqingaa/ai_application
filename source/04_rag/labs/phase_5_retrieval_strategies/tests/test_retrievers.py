from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.similarity import cosine_similarity
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.retrievers.chroma import ChromaRetriever, RetrievalStrategyConfig
from app.vectorstores.chroma_store import (
    ChromaVectorStore,
    ChromaVectorStoreConfig,
    chromadb_is_available,
)


def _average_pairwise_similarity(texts: list[str], provider_name: str, model_name: str, dimensions: int) -> float:
    provider = create_embedding_provider(
        EmbeddingProviderConfig(
            provider_name=provider_name,
            model_name=model_name,
            dimensions=dimensions,
        )
    )
    vectors = provider.embed_documents(texts)
    if len(vectors) < 2:
        return 0.0

    total = 0.0
    pairs = 0
    for left_index in range(len(vectors)):
        for right_index in range(left_index + 1, len(vectors)):
            total += cosine_similarity(vectors[left_index], vectors[right_index])
            pairs += 1
    return total / pairs


@unittest.skipUnless(chromadb_is_available(), "chromadb package is not installed.")
class RetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store_dir = Path(self.temp_dir.name) / "chroma"
        self.provider = create_embedding_provider(
            EmbeddingProviderConfig(
                provider_name=settings.default_embedding_provider,
                model_name=settings.default_embedding_model,
                dimensions=settings.default_embedding_dimensions,
            )
        )
        split_config = SplitterConfig(
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
        )
        embedded_chunks = build_embedded_chunk_corpus(
            data_dir=PROJECT_ROOT / "data",
            split_config=split_config,
            supported_suffixes=settings.supported_suffixes,
            provider=self.provider,
            batch_size=settings.default_embedding_batch_size,
        )
        self.store = ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.store_dir,
                collection_name="retriever_chunks",
                distance_metric="cosine",
            )
        )
        self.store.reset()
        self.store.upsert(embedded_chunks, batch_size=4)

    def test_similarity_retriever_returns_relevant_chunk(self) -> None:
        retriever = ChromaRetriever(
            store=self.store,
            provider=self.provider,
            config=RetrievalStrategyConfig(strategy_name="similarity"),
        )

        results = retriever.retrieve("Why do stable document IDs matter?", top_k=2)

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].chunk.metadata["filename"], "faq.txt")
        self.assertIn("stable", results[0].chunk.content.lower())

    def test_threshold_retriever_filters_out_low_score_tail(self) -> None:
        similarity = ChromaRetriever(
            store=self.store,
            provider=self.provider,
            config=RetrievalStrategyConfig(strategy_name="similarity"),
        )
        threshold = ChromaRetriever(
            store=self.store,
            provider=self.provider,
            config=RetrievalStrategyConfig(
                strategy_name="threshold",
                candidate_k=6,
                score_threshold=0.70,
            ),
        )

        similarity_results = similarity.retrieve(
            "Why do stable document IDs matter?",
            top_k=5,
        )
        threshold_results = threshold.retrieve(
            "Why do stable document IDs matter?",
            top_k=5,
        )

        self.assertGreater(len(similarity_results), len(threshold_results))
        self.assertTrue(all(item.score is not None and item.score >= 0.70 for item in threshold_results))

    def test_metadata_filter_applies_inside_retriever(self) -> None:
        retriever = ChromaRetriever(
            store=self.store,
            provider=self.provider,
            config=RetrievalStrategyConfig(
                strategy_name="similarity",
                metadata_filter={"filename": "product_overview.md"},
            ),
        )

        results = retriever.retrieve(
            "Where do we keep source path and chunk index metadata?",
            top_k=3,
        )

        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(
            all(item.chunk.metadata["filename"] == "product_overview.md" for item in results)
        )

    def test_mmr_reduces_redundancy_relative_to_similarity(self) -> None:
        question = "Where do we keep source path and chunk index metadata?"
        similarity = ChromaRetriever(
            store=self.store,
            provider=self.provider,
            config=RetrievalStrategyConfig(
                strategy_name="similarity",
                candidate_k=5,
            ),
        )
        mmr = ChromaRetriever(
            store=self.store,
            provider=self.provider,
            config=RetrievalStrategyConfig(
                strategy_name="mmr",
                candidate_k=5,
                mmr_lambda=0.15,
            ),
        )

        similarity_results = similarity.retrieve(question, top_k=3)
        mmr_results = mmr.retrieve(question, top_k=3)

        self.assertEqual(len(similarity_results), 3)
        self.assertEqual(len(mmr_results), 3)

        similarity_redundancy = _average_pairwise_similarity(
            [item.chunk.content for item in similarity_results],
            settings.default_embedding_provider,
            settings.default_embedding_model,
            settings.default_embedding_dimensions,
        )
        mmr_redundancy = _average_pairwise_similarity(
            [item.chunk.content for item in mmr_results],
            settings.default_embedding_provider,
            settings.default_embedding_model,
            settings.default_embedding_dimensions,
        )

        self.assertLess(mmr_redundancy, similarity_redundancy)


if __name__ == "__main__":
    unittest.main()
