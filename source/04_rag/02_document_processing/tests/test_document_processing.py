from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_processing import (
    DATA_DIR,
    SplitterConfig,
    build_chunk_corpus,
    discover_documents,
    load_and_prepare_chunks,
    load_document,
    normalize_text,
    split_text,
)


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_markdown = DATA_DIR / "product_overview.md"
        self.sample_text = DATA_DIR / "faq.txt"

    def test_discover_documents_filters_supported_files(self) -> None:
        documents = discover_documents(DATA_DIR)
        self.assertEqual([path.name for path in documents], ["faq.txt", "product_overview.md"])

    def test_normalize_text_removes_crlf_and_trailing_spaces(self) -> None:
        normalized = normalize_text("line 1  \r\nline 2\r\n")
        self.assertEqual(normalized, "line 1\nline 2")

    def test_split_text_returns_chunk_offsets(self) -> None:
        text = load_document(self.sample_markdown)
        chunks = split_text(text, SplitterConfig(chunk_size=160, chunk_overlap=30))
        self.assertGreater(len(chunks), 1)
        self.assertLess(chunks[0].start_index, chunks[0].end_index)
        self.assertTrue(chunks[0].content)

    def test_load_and_prepare_chunks_is_stable(self) -> None:
        first_run = load_and_prepare_chunks(self.sample_text, SplitterConfig())
        second_run = load_and_prepare_chunks(self.sample_text, SplitterConfig())

        self.assertGreaterEqual(len(first_run), 1)
        self.assertEqual(
            [chunk.chunk_id for chunk in first_run],
            [chunk.chunk_id for chunk in second_run],
        )
        self.assertIn("char_start", first_run[0].metadata)
        self.assertIn("char_end", first_run[0].metadata)
        self.assertEqual(first_run[0].metadata["filename"], "faq.txt")

    def test_build_chunk_corpus_returns_multiple_documents(self) -> None:
        chunks = build_chunk_corpus(DATA_DIR, SplitterConfig(chunk_size=180, chunk_overlap=30))
        filenames = {chunk.metadata["filename"] for chunk in chunks}
        self.assertEqual(filenames, {"faq.txt", "product_overview.md"})


if __name__ == "__main__":
    unittest.main()
