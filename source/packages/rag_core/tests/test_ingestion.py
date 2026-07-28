from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document
from reportlab.pdfgen import canvas

from rag_core import (
    ElementKind,
    EvidenceEligibility,
    IngestionError,
    IngestionErrorCode,
    IngestionStage,
    SourceRole,
    load_document,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_DIR = REPO_ROOT / "review_assistant" / "fixtures" / "v0" / "ingestion"


def _load(path: Path, **overrides):
    arguments = {
        "document_id": "KR-ORDER-STATE",
        "document_version": "1.0.0",
        "source_role": SourceRole.REFERENCE_KNOWLEDGE,
        "evidence_eligibility": EvidenceEligibility.CURRENT_EVIDENCE,
        "metadata": {"domain": "after_sale"},
    }
    arguments.update(overrides)
    return load_document(path, **arguments)


def test_txt_preserves_line_ranges_and_stable_identity(tmp_path: Path) -> None:
    path = tmp_path / "rules.txt"
    path.write_text("Current rules\npaid and completed\n\nAPI\nsource_channel required\n", encoding="utf-8")

    first = _load(path)
    second = _load(path)

    assert first.document.content_hash == second.document.content_hash
    assert [element.element_id for element in first.document.elements] == [
        element.element_id for element in second.document.elements
    ]
    assert first.document.metadata["domain"] == "after_sale"
    assert first.document.elements[0].locator.line_start == 1
    assert first.document.elements[0].locator.line_end == 2
    assert first.document.elements[1].locator.line_start == 4
    assert first.report.source_locator_kinds == ("text_lines",)


def test_markdown_preserves_heading_paths_and_list_items(tmp_path: Path) -> None:
    path = tmp_path / "rules.md"
    path.write_text(
        "# After-sale rules\n\n## States\n\n- paid\n- completed\n",
        encoding="utf-8",
    )

    result = _load(path)

    assert [element.kind for element in result.document.elements] == [
        ElementKind.TITLE,
        ElementKind.TITLE,
        ElementKind.LIST_ITEM,
        ElementKind.LIST_ITEM,
    ]
    assert result.document.elements[-1].locator.heading_path == (
        "After-sale rules",
        "States",
    )
    assert result.document.elements[-1].locator.line_start == 6


def test_docx_preserves_paragraph_and_table_locations(tmp_path: Path) -> None:
    path = tmp_path / "rules.docx"
    document = Document()
    document.add_heading("After-sale rules", level=1)
    document.add_paragraph("Only paid and completed orders are eligible.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "field"
    table.cell(0, 1).text = "requirement"
    table.cell(1, 0).text = "source_channel"
    table.cell(1, 1).text = "required"
    document.save(path)

    result = _load(path)

    assert [element.kind for element in result.document.elements] == [
        ElementKind.TITLE,
        ElementKind.PARAGRAPH,
        ElementKind.TABLE,
    ]
    assert result.document.elements[1].locator.paragraph_index == 2
    assert result.document.elements[2].locator.table_index == 1
    assert result.document.elements[2].locator.heading_path == ("After-sale rules",)


def test_text_pdf_succeeds_with_page_location_and_warning(tmp_path: Path) -> None:
    path = tmp_path / "rules.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 760, "Only paid and completed orders are eligible.")
    pdf.showPage()
    pdf.drawString(72, 760, "source_channel is required by after-sale API v2.")
    pdf.save()

    result = _load(path)

    assert [element.locator.page_number for element in result.document.elements] == [1, 2]
    assert "paid and completed" in result.document.elements[0].text
    assert "source_channel" in result.document.elements[1].text
    assert {warning.code for warning in result.report.warnings} == {
        "pdf_reading_order_not_guaranteed"
    }


def test_pdf_without_text_layer_fails_explicitly(tmp_path: Path) -> None:
    path = tmp_path / "scan.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.rect(72, 700, 300, 80, fill=1)
    pdf.showPage()
    pdf.save()

    with pytest.raises(IngestionError) as captured:
        _load(path)

    assert captured.value.stage is IngestionStage.EMPTY_CONTENT
    assert captured.value.code is IngestionErrorCode.PDF_TEXT_LAYER_MISSING


def test_invalid_utf8_and_format_mismatch_have_different_stages(tmp_path: Path) -> None:
    invalid_text = tmp_path / "invalid.txt"
    invalid_text.write_bytes("售后".encode("gbk"))
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(IngestionError) as text_error:
        _load(invalid_text)
    with pytest.raises(IngestionError) as format_error:
        _load(fake_pdf)

    assert text_error.value.stage is IngestionStage.PARSE
    assert text_error.value.code is IngestionErrorCode.TEXT_DECODE_FAILED
    assert format_error.value.stage is IngestionStage.FORMAT_DETECTION
    assert format_error.value.code is IngestionErrorCode.FORMAT_MISMATCH


def test_empty_markdown_and_historical_evidence_boundary(tmp_path: Path) -> None:
    empty = tmp_path / "empty.md"
    empty.write_text("<!-- no knowledge content -->\n", encoding="utf-8")

    with pytest.raises(IngestionError) as empty_error:
        _load(empty)
    assert empty_error.value.code is IngestionErrorCode.EMPTY_DOCUMENT

    valid = tmp_path / "history.txt"
    valid.write_text("old review", encoding="utf-8")
    with pytest.raises(ValueError, match="Historical Material"):
        _load(
            valid,
            source_role=SourceRole.HISTORICAL_MATERIAL,
            evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        )

    history = _load(
        valid,
        source_role=SourceRole.HISTORICAL_MATERIAL,
        evidence_eligibility=EvidenceEligibility.HISTORICAL_CONTEXT,
    )
    assert history.document.source_role is SourceRole.HISTORICAL_MATERIAL
    assert history.document.evidence_eligibility is EvidenceEligibility.HISTORICAL_CONTEXT


def test_controlled_formats_preserve_all_canonical_facts() -> None:
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    canonical = json.loads((FIXTURE_DIR / manifest["canonical_source"]).read_text(encoding="utf-8"))
    facts = [fact for section in canonical["sections"] for fact in section["facts"]]

    assert manifest["fixture_kind"] == "synthetic_controlled_format_comparison"
    assert manifest["comparison_mode"] == "mutually_exclusive_representations"

    for case in manifest["documents"]:
        result = load_document(
            FIXTURE_DIR / case["path"],
            document_id=case["document_id"],
            document_version=case["document_version"],
            source_role=SourceRole(case["source_role"]),
            evidence_eligibility=EvidenceEligibility(case["evidence_eligibility"]),
        )
        for fact in facts:
            assert fact in result.document.text, f"{case['path']} 丢失 canonical fact: {fact}"
