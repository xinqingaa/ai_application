import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_processing import (
    CHAPTER_ROOT,
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
    load_document_record,
    normalize_text,
    run_document_pipeline,
    split_markdown_by_headers,
    split_text,
)

GOLDEN_SET_PATH = CHAPTER_ROOT / "document_processing_golden_set.json"
with GOLDEN_SET_PATH.open("r", encoding="utf-8") as handle:
    GOLDEN_SET = json.load(handle)


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_markdown = DATA_DIR / "product_overview.md"
        self.sample_text = DATA_DIR / "faq.txt"
        self.sample_pdf = DATA_DIR / "course_policy.pdf"

    def test_discover_documents_filters_supported_files(self) -> None:
        documents = discover_documents(DATA_DIR)
        self.assertEqual(
            [path.name for path in documents],
            ["course_policy.pdf", "faq.txt", "product_overview.md"],
        )

    def test_inspect_document_candidates_explains_accept_and_ignore(self) -> None:
        decisions = {
            candidate.path.name: candidate
            for candidate in inspect_document_candidates(DATA_DIR)
        }
        self.assertTrue(decisions["course_policy.pdf"].accepted)
        self.assertIn("pypdf.PdfReader", decisions["course_policy.pdf"].reason)
        self.assertTrue(decisions["faq.txt"].accepted)
        self.assertIn("supported suffix: .txt", decisions["faq.txt"].reason)
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

    def test_load_document_record_reads_pdf_and_records_page_count(self) -> None:
        document = load_document_record(self.sample_pdf)
        self.assertEqual(document.metadata["loader"], "pypdf.PdfReader")
        self.assertEqual(document.metadata["page_count"], 2)
        self.assertIn("Course PDF Policy", document.content)
        self.assertIn("Pipeline Notes", document.content)

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

    def test_split_markdown_by_headers_returns_header_paths(self) -> None:
        text = load_document(self.sample_markdown)
        sections = split_markdown_by_headers(text)
        self.assertEqual(sections[0].header_path, "Product Overview")
        self.assertEqual(sections[1].header_path, "Product Overview > Ingestion Policy")
        self.assertEqual(sections[-1].section_title, "Metadata Rules")

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

    def test_run_document_pipeline_reports_summary(self) -> None:
        result = run_document_pipeline(DATA_DIR, SplitterConfig())
        self.assertEqual(result.accepted_documents, 3)
        self.assertEqual(result.ignored_candidates, 2)
        self.assertGreater(result.total_chunks, 0)

    def test_build_chunk_corpus_matches_golden_set(self) -> None:
        chunks = build_chunk_corpus(DATA_DIR, SplitterConfig(chunk_size=180, chunk_overlap=30))
        actual_counts: dict[str, int] = {}
        actual_sources: dict[str, str] = {}
        actual_loaders: dict[str, str] = {}
        actual_page_counts: dict[str, int] = {}
        actual_header_paths: dict[str, set[str]] = {}

        for chunk in chunks:
            filename = str(chunk.metadata["filename"])
            actual_counts[filename] = actual_counts.get(filename, 0) + 1
            actual_sources.setdefault(filename, str(chunk.metadata["source"]))
            actual_loaders.setdefault(filename, str(chunk.metadata["loader"]))
            if "page_count" in chunk.metadata:
                actual_page_counts.setdefault(filename, int(chunk.metadata["page_count"]))
            if "header_path" in chunk.metadata and chunk.metadata["header_path"]:
                actual_header_paths.setdefault(filename, set()).add(str(chunk.metadata["header_path"]))

        for case in GOLDEN_SET:
            with self.subTest(filename=case["filename"]):
                self.assertEqual(actual_counts[case["filename"]], case["expected_chunk_count"])
                self.assertEqual(actual_sources[case["filename"]], case["expected_source"])
                self.assertEqual(actual_loaders[case["filename"]], case["expected_loader"])
                if "expected_page_count" in case:
                    self.assertEqual(
                        actual_page_counts[case["filename"]],
                        case["expected_page_count"],
                    )
                if "expected_header_paths" in case:
                    self.assertTrue(
                        set(case["expected_header_paths"]).issubset(
                            actual_header_paths[case["filename"]]
                        )
                    )


if __name__ == "__main__":
    unittest.main()
