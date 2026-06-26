from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chroma_store import (
    DOCUMENT_ID_KEY,
    ChromaVectorStore,
    ChromaVectorStoreConfig,
    chromadb_is_available,
)
from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    SourceChunk,
    demo_embedded_chunks,
    embed_chunks,
)


@unittest.skipUnless(chromadb_is_available(), "chromadb package is not installed.")
class ChromaVectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store_dir = Path(self.temp_dir.name) / "chroma"
        self.store = ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.store_dir,
                collection_name="test_chunks",
            )
        )
        self.provider = LocalKeywordEmbeddingProvider()
        self.chunks = demo_embedded_chunks(self.provider)
        self.store.reset()
        self.store.upsert(self.chunks)

    def test_upsert_persists_and_reloads_chunks(self) -> None:
        reloaded = ChromaVectorStore(
            ChromaVectorStoreConfig(
                persist_directory=self.store_dir,
                collection_name="test_chunks",
            )
        )

        loaded = reloaded.load_chunks()
        self.assertEqual(len(loaded), len(self.chunks))
        self.assertEqual(
            {chunk.chunk.chunk_id for chunk in loaded},
            {chunk.chunk.chunk_id for chunk in self.chunks},
        )
        self.assertEqual(
            {chunk.chunk.metadata["filename"] for chunk in loaded},
            {chunk.chunk.metadata["filename"] for chunk in self.chunks},
        )

    def test_similarity_search_prefers_relevant_chunk(self) -> None:
        query_vector = self.provider.embed_query("如何申请退费？")
        results = self.store.similarity_search(query_vector, provider=self.provider, top_k=1)

        self.assertEqual(results[0].chunk.chunk_id, "refund:0")
        self.assertGreater(results[0].score, 0.5)

    def test_metadata_filter_limits_results(self) -> None:
        query_vector = self.provider.embed_query("为什么 metadata 很重要？")
        results = self.store.similarity_search(
            query_vector,
            provider=self.provider,
            top_k=3,
            where={"filename": "metadata_rules.md"},
        )

        self.assertTrue(results)
        self.assertTrue(all(item.chunk.metadata["filename"] == "metadata_rules.md" for item in results))

    def test_composite_metadata_filter_limits_results(self) -> None:
        query_vector = self.provider.embed_query("为什么 metadata 很重要？")
        results = self.store.similarity_search(
            query_vector,
            provider=self.provider,
            top_k=3,
            where={
                "$and": [
                    {"filename": "metadata_rules.md"},
                    {"suffix": ".md"},
                    {DOCUMENT_ID_KEY: "metadata"},
                ]
            },
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.document_id, "metadata")

    def test_delete_by_document_id_removes_every_chunk_for_that_document(self) -> None:
        deleted = self.store.delete_by_document_id("trial")

        self.assertEqual(deleted, 1)
        self.assertNotIn("trial", self.store.list_document_ids())
        self.assertEqual(self.store.count(), len(self.chunks) - 1)

    def test_replace_document_removes_stale_chunks_for_same_document(self) -> None:
        replacement_chunks = embed_chunks(
            [
                SourceChunk(
                    chunk_id="trial:1",
                    document_id="trial",
                    content="试学需要先完成登记，再预约 30 分钟时段。",
                    metadata={
                        "source": "data/trial_policy.md",
                        "filename": "trial_policy.md",
                        "suffix": ".md",
                        "char_count": 22,
                        "line_count": 1,
                        "chunk_index": 1,
                        "char_start": 0,
                        "char_end": 22,
                        "chunk_chars": 22,
                    },
                )
            ],
            self.provider,
        )

        replaced = self.store.replace_document(replacement_chunks)
        loaded_chunk_ids = {chunk.chunk.chunk_id for chunk in self.store.load_chunks()}

        self.assertEqual(replaced, 1)
        self.assertIn("trial:1", loaded_chunk_ids)
        self.assertNotIn("trial:0", loaded_chunk_ids)

    def test_similarity_search_rejects_query_from_different_embedding_space(self) -> None:
        other_provider = LocalKeywordEmbeddingProvider(model_name="concept-space-v2")
        query_vector = other_provider.embed_query("如何申请退费？")

        with self.assertRaisesRegex(ValueError, "embedding space"):
            self.store.similarity_search(query_vector, provider=other_provider, top_k=1)


if __name__ == "__main__":
    unittest.main()
