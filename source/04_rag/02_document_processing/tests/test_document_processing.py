from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_processing import (
    DATA_DIR,
    SplitterConfig,
    build_base_metadata,
    build_chunk_corpus,
    build_chunk_metadata,
    discover_documents,
    inspect_document_candidate,
    inspect_document_candidates,
    load_and_prepare_chunks,
    load_document,
    normalize_text,
    split_text,
)

MINI_GOLDEN_SET = [
    {
        "filename": "faq.txt",
        "expected_chunk_count": 3,
        "expected_source": "data/faq.txt",
    },
    {
        "filename": "product_overview.md",
        "expected_chunk_count": 9,
        "expected_source": "data/product_overview.md",
    },
]


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_markdown = DATA_DIR / "product_overview.md"
        self.sample_text = DATA_DIR / "faq.txt"

    def test_discover_documents_filters_supported_files(self) -> None:
        documents = discover_documents(DATA_DIR)
        self.assertEqual([path.name for path in documents], ["faq.txt", "product_overview.md"])

    def test_inspect_document_candidates_explains_accept_and_ignore(self) -> None:
        decisions = {
            candidate.path.name: candidate
            for candidate in inspect_document_candidates(DATA_DIR)
        }
        self.assertTrue(decisions["faq.txt"].accepted)
        self.assertEqual(decisions["faq.txt"].reason, "supported suffix: .txt")
        self.assertFalse(decisions["README.md"].accepted)
        self.assertIn("not a knowledge source", decisions["README.md"].reason)
        self.assertFalse(decisions["ignore.csv"].accepted)
        self.assertIn("unsupported suffix", decisions["ignore.csv"].reason)

    def test_normalize_text_removes_crlf_and_trailing_spaces(self) -> None:
        normalized = normalize_text("line 1  \r\nline 2\r\n")
        self.assertEqual(normalized, "line 1\nline 2")

    def test_inspect_document_candidate_rejects_non_file(self) -> None:
        candidate = inspect_document_candidate(DATA_DIR)
        self.assertFalse(candidate.accepted)
        self.assertEqual(candidate.reason, "not a file")

    def test_load_document_rejects_unsupported_file_type(self) -> None:
        with self.assertRaises(ValueError):
            load_document(DATA_DIR / "ignore.csv")

    def test_splitter_config_rejects_invalid_overlap(self) -> None:
        with self.assertRaises(ValueError):
            SplitterConfig(chunk_size=100, chunk_overlap=100)

    def test_split_text_returns_chunk_offsets(self) -> None:
        text = load_document(self.sample_markdown)
        chunks = split_text(text, SplitterConfig(chunk_size=160, chunk_overlap=30))
        self.assertGreater(len(chunks), 1)
        self.assertLess(chunks[0].start_index, chunks[0].end_index)
        self.assertTrue(chunks[0].content)

    def test_metadata_builders_keep_document_and_chunk_fields(self) -> None:
        text = load_document(self.sample_text)
        base_metadata = build_base_metadata(self.sample_text, text)
        chunk_metadata = build_chunk_metadata(
            base_metadata=base_metadata,
            chunk_index=0,
            start_index=10,
            end_index=42,
        )
        self.assertEqual(base_metadata["filename"], "faq.txt")
        self.assertEqual(base_metadata["source"], "data/faq.txt")
        self.assertEqual(chunk_metadata["chunk_index"], 0)
        self.assertEqual(chunk_metadata["char_start"], 10)
        self.assertEqual(chunk_metadata["char_end"], 42)
        self.assertEqual(chunk_metadata["chunk_chars"], 32)

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

    def test_build_chunk_corpus_matches_mini_golden_set(self) -> None:
        chunks = build_chunk_corpus(DATA_DIR, SplitterConfig(chunk_size=180, chunk_overlap=30))
        actual_counts: dict[str, int] = {}
        actual_sources: dict[str, str] = {}

        for chunk in chunks:
            filename = str(chunk.metadata["filename"])
            actual_counts[filename] = actual_counts.get(filename, 0) + 1
            actual_sources.setdefault(filename, str(chunk.metadata["source"]))

        for case in MINI_GOLDEN_SET:
            with self.subTest(filename=case["filename"]):
                self.assertEqual(actual_counts[case["filename"]], case["expected_chunk_count"])
                self.assertEqual(actual_sources[case["filename"]], case["expected_source"])


if __name__ == "__main__":
    unittest.main()
