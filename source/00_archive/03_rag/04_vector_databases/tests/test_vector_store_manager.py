from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chroma_store import chromadb_is_available
from langchain_adapter import langchain_vectorstore_is_available
from vector_store_basics import LocalKeywordEmbeddingProvider
from vector_store_manager import VectorStoreManager


class VectorStoreManagerJsonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.manager = VectorStoreManager(
            backend="json",
            provider=LocalKeywordEmbeddingProvider(),
            json_store_path=Path(self.temp_dir.name) / "store.json",
        )

    def test_json_manager_add_replace_search_delete(self) -> None:
        added = self.manager.add_documents(
            ["购买后可以联系助教办理退费。"],
            ids=["custom"],
            metadatas=[{"source": "data/custom.md"}],
        )
        self.assertEqual(added, 1)
        self.assertEqual(self.manager.count(), 1)

        results = self.manager.search("如何办理退费？", top_k=1)
        self.assertEqual(results[0].chunk.document_id, "custom")

        replaced = self.manager.replace_document(
            "custom",
            "试学需要提前预约并完成登记。",
            metadata={"source": "data/custom.md"},
        )
        self.assertEqual(replaced, 1)

        results = self.manager.search("如何预约试学？", top_k=1)
        self.assertEqual(results[0].chunk.document_id, "custom")

        deleted = self.manager.delete_document("custom")
        self.assertEqual(deleted, 1)
        self.assertEqual(self.manager.count(), 0)


@unittest.skipUnless(chromadb_is_available(), "chromadb package is not installed.")
class VectorStoreManagerChromaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.manager = VectorStoreManager(
            backend="chroma",
            provider=LocalKeywordEmbeddingProvider(),
            chroma_persist_directory=Path(self.temp_dir.name) / "chroma",
            chroma_collection_name="test_manager_chunks",
        )

    def test_chroma_manager_add_replace_search_delete(self) -> None:
        added = self.manager.add_documents(
            ["购买后可以联系助教办理退费。"],
            ids=["custom"],
            metadatas=[{"source": "data/custom.md"}],
        )
        self.assertEqual(added, 1)
        self.assertEqual(self.manager.count(), 1)

        results = self.manager.search("如何办理退费？", top_k=1)
        self.assertEqual(results[0].chunk.document_id, "custom")

        replaced = self.manager.replace_document(
            "custom",
            "试学需要提前预约并完成登记。",
            metadata={"source": "data/custom.md"},
        )
        self.assertEqual(replaced, 1)

        results = self.manager.search("如何预约试学？", top_k=1)
        self.assertEqual(results[0].chunk.document_id, "custom")

        deleted = self.manager.delete_document("custom")
        self.assertEqual(deleted, 1)
        self.assertEqual(self.manager.count(), 0)


@unittest.skipUnless(
    langchain_vectorstore_is_available(),
    "langchain-core and langchain-chroma packages are not installed.",
)
class VectorStoreManagerLangChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.manager = VectorStoreManager(
            backend="langchain",
            provider=LocalKeywordEmbeddingProvider(),
            langchain_persist_directory=Path(self.temp_dir.name) / "langchain_chroma",
            langchain_collection_name="test_manager_langchain_chunks",
        )

    def test_langchain_manager_add_replace_search_delete(self) -> None:
        added = self.manager.add_documents(
            ["购买后可以联系助教办理退费。"],
            ids=["custom"],
            metadatas=[{"source": "data/custom.md"}],
        )
        self.assertEqual(added, 1)
        self.assertEqual(self.manager.count(), 1)

        results = self.manager.search("如何办理退费？", top_k=1)
        self.assertEqual(results[0].chunk.document_id, "custom")

        replaced = self.manager.replace_document(
            "custom",
            "试学需要提前预约并完成登记。",
            metadata={"source": "data/custom.md"},
        )
        self.assertEqual(replaced, 1)

        results = self.manager.search("如何预约试学？", top_k=1)
        self.assertEqual(results[0].chunk.document_id, "custom")

        deleted = self.manager.delete_document("custom")
        self.assertEqual(deleted, 1)
        self.assertEqual(self.manager.count(), 0)


if __name__ == "__main__":
    unittest.main()
