from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_adapter import (
    LangChainChromaConfig,
    build_documents,
    create_langchain_chroma,
    create_langchain_chroma_from_documents,
    langchain_vectorstore_is_available,
    retrieval_results_from_scored_documents,
    similarity_results_from_documents,
)
from vector_store_basics import LocalKeywordEmbeddingProvider


@unittest.skipUnless(
    langchain_vectorstore_is_available(),
    "langchain-core and langchain-chroma packages are not installed.",
)
class LangChainVectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.persist_directory = Path(self.temp_dir.name) / "langchain_chroma"
        self.provider = LocalKeywordEmbeddingProvider()
        self.config = LangChainChromaConfig(
            persist_directory=self.persist_directory,
            collection_name="test_langchain_chunks",
        )
        self.vectorstore = create_langchain_chroma(self.provider, self.config)
        self.documents = build_documents()
        self.ids = [str(document.metadata["chunk_id"]) for document in self.documents]
        self.vectorstore.add_documents(documents=self.documents, ids=self.ids)

    def test_similarity_search_prefers_relevant_chunk(self) -> None:
        results = self.vectorstore.similarity_search_with_score("如何申请退费？", k=1)
        hydrated = retrieval_results_from_scored_documents(results)

        self.assertEqual(hydrated[0].chunk.chunk_id, "refund:0")
        self.assertGreater(hydrated[0].score, 0.5)

    def test_similarity_search_without_scores_prefers_relevant_chunk(self) -> None:
        results = self.vectorstore.similarity_search("如何申请退费？", k=1)
        hydrated = similarity_results_from_documents(results)

        self.assertEqual(hydrated[0].chunk.chunk_id, "refund:0")

    def test_filter_limits_results(self) -> None:
        results = self.vectorstore.similarity_search_with_score(
            "为什么 metadata 很重要？",
            k=3,
            filter={"filename": "metadata_rules.md"},
        )
        hydrated = retrieval_results_from_scored_documents(results)

        self.assertTrue(hydrated)
        self.assertTrue(all(item.chunk.metadata["filename"] == "metadata_rules.md" for item in hydrated))

    def test_as_retriever_returns_relevant_chunk(self) -> None:
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 1},
        )
        hydrated = similarity_results_from_documents(retriever.invoke("如何申请退费？"))

        self.assertEqual(hydrated[0].chunk.chunk_id, "refund:0")

    def test_from_documents_initializes_store(self) -> None:
        config = LangChainChromaConfig(
            persist_directory=Path(self.temp_dir.name) / "langchain_from_documents",
            collection_name="test_from_documents_chunks",
        )
        vectorstore = create_langchain_chroma_from_documents(self.provider, config)
        hydrated = retrieval_results_from_scored_documents(
            vectorstore.similarity_search_with_score("为什么 metadata 很重要？", k=1)
        )

        self.assertEqual(hydrated[0].chunk.chunk_id, "metadata:0")


if __name__ == "__main__":
    unittest.main()
