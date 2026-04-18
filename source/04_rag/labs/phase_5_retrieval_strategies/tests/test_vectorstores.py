from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.vectorstores.chroma_store import (
    ChromaVectorStore,
    ChromaVectorStoreConfig,
    chromadb_is_available,
)


@unittest.skipUnless(chromadb_is_available(), "chromadb package is not installed.")
class ChromaVectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store_dir = Path(self.temp_dir.name) / "chroma"
        self.split_config = SplitterConfig(
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
        )
        self.provider = create_embedding_provider(
            EmbeddingProviderConfig(
                provider_name=settings.default_embedding_provider,
                model_name=settings.default_embedding_model,
                dimensions=settings.default_embedding_dimensions,
            )
        )
        self.embedded_chunks = build_embedded_chunk_corpus(
            data_dir=PROJECT_ROOT / "data",
            split_config=self.split_config,
            supported_suffixes=settings.supported_suffixes,
            provider=self.provider,
            batch_size=settings.default_embedding_batch_size,
        )
        self.store = ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.store_dir,
                collection_name="test_chunks",
                distance_metric="cosine",
            )
        )
        self.store.reset()
        self.store.upsert(self.embedded_chunks, batch_size=4)

    def test_upsert_persists_and_reloads_chunks(self) -> None:
        reloaded = ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.store_dir,
                collection_name="test_chunks",
                distance_metric="cosine",
            )
        )

        self.assertEqual(reloaded.count(), len(self.embedded_chunks))
        restored = reloaded.get_chunks(limit=2)
        self.assertEqual(len(restored), 2)
        self.assertTrue(restored[0].chunk_id)
        self.assertTrue(restored[0].document_id)
        self.assertIn("filename", restored[0].metadata)
        self.assertIn("chunk_index", restored[0].metadata)

    def test_similarity_search_prefers_relevant_chunk(self) -> None:
        results = self.store.similarity_search(
            question="Why do stable document IDs matter?",
            provider=self.provider,
            top_k=2,
        )

        self.assertGreaterEqual(len(results), 1)
        self.assertIsNotNone(results[0].score)
        self.assertIn("stable", results[0].chunk.content.lower())
        self.assertEqual(results[0].chunk.metadata["filename"], "faq.txt")

    def test_metadata_filter_limits_results(self) -> None:
        results = self.store.similarity_search(
            question="Where do we keep source path and chunk index metadata?",
            provider=self.provider,
            top_k=3,
            where={"filename": "product_overview.md"},
        )

        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(
            all(item.chunk.metadata["filename"] == "product_overview.md" for item in results)
        )

    def test_delete_by_document_id_removes_every_chunk_for_that_document(self) -> None:
        target = next(
            item for item in self.embedded_chunks if item.chunk.metadata["filename"] == "faq.txt"
        )

        before = self.store.count()
        self.store.delete_by_document_id(target.chunk.document_id)
        after = self.store.count()
        remaining = self.store.get_chunks(where={"filename": "faq.txt"})

        self.assertLess(after, before)
        self.assertEqual(remaining, [])


if __name__ == "__main__":
    unittest.main()
