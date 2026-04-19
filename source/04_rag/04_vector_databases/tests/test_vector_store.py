from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
)


class VectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.store_path = Path(self.tmp_dir.name) / "store.json"
        self.store = PersistentVectorStore(VectorStoreConfig(store_path=self.store_path))
        self.provider = LocalKeywordEmbeddingProvider()
        self.chunks = demo_embedded_chunks(self.provider)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_upsert_persists_and_reloads_chunks(self) -> None:
        self.store.upsert(self.chunks)
        reloaded_store = PersistentVectorStore(VectorStoreConfig(store_path=self.store_path))
        reloaded = reloaded_store.load_chunks()

        self.assertEqual(len(reloaded), len(self.chunks))
        self.assertEqual(
            {chunk.chunk.chunk_id for chunk in reloaded},
            {chunk.chunk.chunk_id for chunk in self.chunks},
        )
        self.assertEqual(
            {chunk.chunk.metadata["filename"] for chunk in reloaded},
            {chunk.chunk.metadata["filename"] for chunk in self.chunks},
        )

    def test_similarity_search_prefers_relevant_chunk(self) -> None:
        self.store.upsert(self.chunks)
        query_vector = self.provider.embed_query("如何申请退费？")
        results = self.store.similarity_search(query_vector, top_k=1)

        self.assertEqual(results[0].chunk.chunk_id, "refund:0")
        self.assertGreater(results[0].score, 0.5)

    def test_filename_filter_limits_results(self) -> None:
        self.store.upsert(self.chunks)
        query_vector = self.provider.embed_query("为什么 metadata 很重要？")
        results = self.store.similarity_search(
            query_vector,
            top_k=3,
            filename="metadata_rules.md",
        )

        self.assertTrue(results)
        self.assertTrue(all(item.chunk.metadata["filename"] == "metadata_rules.md" for item in results))

    def test_delete_by_document_id_removes_every_chunk_for_that_document(self) -> None:
        self.store.upsert(self.chunks)
        deleted = self.store.delete_by_document_id("trial")

        self.assertEqual(deleted, 1)
        self.assertNotIn("trial", self.store.list_document_ids())
        self.assertEqual(self.store.count(), len(self.chunks) - 1)


if __name__ == "__main__":
    unittest.main()
