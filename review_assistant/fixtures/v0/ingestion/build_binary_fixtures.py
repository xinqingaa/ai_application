"""Rebuild the DOCX/PDF and stable failure fixtures used by the ingestion lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx import Document
from reportlab.pdfgen import canvas

FIXTURE_DIR = Path(__file__).resolve().parent
CANONICAL_PATH = FIXTURE_DIR / "canonical_content.json"


def main() -> None:
    content = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    _build_docx(FIXTURE_DIR / "order_rules.docx", content)
    _build_text_pdf(FIXTURE_DIR / "order_rules.pdf", content)
    _build_image_only_pdf(FIXTURE_DIR / "image_only_scan.pdf")
    (FIXTURE_DIR / "damaged.docx").write_bytes(b"PK damaged OOXML fixture")
    (FIXTURE_DIR / "invalid_encoding.txt").write_bytes("售后入口".encode("gbk"))


def _build_docx(path: Path, content: dict[str, Any]) -> None:
    document = Document()
    document.add_heading(content["title"], level=1)
    current_rules, constraints = content["sections"]
    document.add_heading(current_rules["heading"], level=2)
    for fact in current_rules["facts"]:
        document.add_paragraph(fact)
    document.add_heading(constraints["heading"], level=2)
    table = document.add_table(rows=3, cols=2)
    table.cell(0, 0).text = "Object"
    table.cell(0, 1).text = "Current constraint"
    table.cell(1, 0).text = "After-sale API v2"
    table.cell(1, 1).text = constraints["facts"][0]
    table.cell(2, 0).text = "Flutter client"
    table.cell(2, 1).text = constraints["facts"][1]
    document.save(path)


def _build_text_pdf(path: Path, content: dict[str, Any]) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.setTitle(content["title"])
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, 760, content["title"])
    pdf.setFont("Helvetica", 11)
    current_rules, constraints = content["sections"]
    pdf.drawString(72, 730, current_rules["heading"])
    for offset, fact in enumerate(current_rules["facts"]):
        pdf.drawString(72, 705 - offset * 20, fact)
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(72, 760, constraints["heading"])
    pdf.setFont("Helvetica", 11)
    for offset, fact in enumerate(constraints["facts"]):
        pdf.drawString(72, 730 - offset * 20, fact)
    pdf.save()


def _build_image_only_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.setTitle("Image-only scan fixture")
    pdf.rect(72, 680, 440, 120, stroke=1, fill=1)
    pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    main()
