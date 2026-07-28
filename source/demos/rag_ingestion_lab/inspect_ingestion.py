"""Inspect how four file formats enter one KnowledgeDocument contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rag_core import (
    EvidenceEligibility,
    IngestionError,
    SourceRole,
    load_document,
)

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
FIXTURE_DIR = REPO_ROOT / "review_assistant" / "fixtures" / "v0" / "ingestion"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-failures",
        action="store_true",
        help="同时运行扫描 PDF、损坏 DOCX、错误编码和空文档案例",
    )
    args = parser.parse_args()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    print("[ingestion_lab] TXT / Markdown / DOCX / text PDF")
    print(
        f"[fixture_contract] kind={manifest['fixture_kind']} "
        f"mode={manifest['comparison_mode']} canonical={manifest['canonical_source']}"
    )
    for case in manifest["documents"]:
        _inspect_document(case)

    if args.include_failures:
        print("\n[failure_cases]")
        for case in manifest["failure_cases"]:
            _inspect_failure(case)


def _inspect_document(case: dict[str, Any]) -> None:
    path = FIXTURE_DIR / case["path"]
    result = load_document(
        path,
        document_id=case["document_id"],
        document_version=case["document_version"],
        source_role=SourceRole(case["source_role"]),
        evidence_eligibility=EvidenceEligibility(case["evidence_eligibility"]),
        metadata={"knowledge_scope": "after_sale"},
    )
    document = result.document
    report = result.report
    print(
        f"\n[loaded] file={document.original_filename} format={document.file_format.value} "
        f"document={document.document_id}@{document.document_version} "
        f"role={document.source_role.value} eligibility={document.evidence_eligibility.value} "
        f"elements={report.element_count} hash={document.content_hash[:12]}"
    )
    for element in document.elements:
        preview = " ".join(element.text.split())[:100]
        print(
            f"  [{element.ordinal}] {element.kind.value} id={element.element_id} "
            f"locator=({element.locator.describe()}) text={preview}"
        )
    for warning in report.warnings:
        location = warning.locator.describe() if warning.locator else "document"
        print(f"  [warning] {warning.code} at={location}: {warning.message}")


def _inspect_failure(case: dict[str, Any]) -> None:
    path = FIXTURE_DIR / case["path"]
    try:
        load_document(
            path,
            document_id=f"FAIL-{path.stem.upper()}",
            document_version="1.0.0",
            source_role=SourceRole.REFERENCE_KNOWLEDGE,
            evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        )
    except IngestionError as exc:
        matched = exc.code.value == case["expected_error"]
        print(
            f"[expected_failure] file={path.name} stage={exc.stage.value} "
            f"code={exc.code.value} expected={case['expected_error']} matched={matched}"
        )
        return
    raise RuntimeError(f"失败案例意外成功：{path}")


if __name__ == "__main__":
    main()
