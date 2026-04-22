from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.ingestion.loaders import discover_documents, load_document
from app.ingestion.splitters import SplitterConfig, split_text
from app.indexing.index_manager import load_and_prepare_chunks


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = PROJECT_ROOT / "data"
        self.sample_markdown = self.data_dir / "product_overview.md"
        self.sample_text = self.data_dir / "faq.txt"

    def test_settings_defaults(self) -> None:
        self.assertEqual(settings.project_name, "rag_lab")
        self.assertGreater(settings.default_chunk_size, settings.default_chunk_overlap)
        self.assertEqual(settings.default_embedding_provider, "local_hash")
        self.assertEqual(settings.default_embedding_model, "token-hash-v1")
        self.assertGreater(settings.default_embedding_dimensions, 0)
        self.assertEqual(settings.supported_suffixes, (".md", ".txt"))

    def test_discover_documents_filters_supported_files(self) -> None:
        documents = discover_documents(self.data_dir, settings.supported_suffixes)
        self.assertEqual([path.name for path in documents], ["faq.txt", "product_overview.md"])

    def test_load_document_normalizes_text(self) -> None:
        text = load_document(self.sample_markdown)
        self.assertIn("# Product Overview", text)
        self.assertNotIn("\r\n", text)

    def test_split_text_returns_chunk_offsets(self) -> None:
        text = load_document(self.sample_markdown)
        chunks = split_text(text, SplitterConfig(chunk_size=160, chunk_overlap=30))
        self.assertGreater(len(chunks), 1)
        self.assertLess(chunks[0].start_index, chunks[0].end_index)
        self.assertTrue(chunks[0].content)

    def test_load_and_prepare_chunks_is_stable(self) -> None:
        first_run = load_and_prepare_chunks(
            self.sample_text,
            SplitterConfig(
                chunk_size=settings.default_chunk_size,
                chunk_overlap=settings.default_chunk_overlap,
            ),
        )
        second_run = load_and_prepare_chunks(
            self.sample_text,
            SplitterConfig(
                chunk_size=settings.default_chunk_size,
                chunk_overlap=settings.default_chunk_overlap,
            ),
        )

        self.assertGreaterEqual(len(first_run), 1)
        self.assertEqual(
            [chunk.chunk_id for chunk in first_run],
            [chunk.chunk_id for chunk in second_run],
        )
        self.assertIn("char_start", first_run[0].metadata)
        self.assertIn("char_end", first_run[0].metadata)
        self.assertEqual(first_run[0].metadata["filename"], "faq.txt")


if __name__ == "__main__":
    unittest.main()
