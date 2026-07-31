"""Inspect how four file formats enter one KnowledgeDocument contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app_log import (
    add_log_arguments,
    configure_from_args,
    console,
    get_logger,
)
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
log = get_logger("rag_ingestion_lab")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-failures",
        action="store_true",
        help="同时运行阅读顺序、扫描 PDF、损坏 DOCX、错误编码和空文档案例",
    )
    add_log_arguments(parser)
    args = parser.parse_args()
    configure_from_args(args)
    json_mode = args.log_format == "json" and not args.verbose
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if not json_mode:
        console.title(
            "RAG Ingestion Lab",
            "TXT / Markdown / DOCX / text PDF\n"
            f"fixture={manifest['fixture_kind']}\n"
            f"mode={manifest['comparison_mode']} · "
            f"canonical={manifest['canonical_source']}",
        )

    loaded_results = [_load_document(case) for case in manifest["documents"]]
    _render_loaded(loaded_results, verbose=args.verbose, json_mode=json_mode)

    mismatch_count = 0
    if args.include_failures:
        mismatch_count += _inspect_warning_cases(
            manifest["warning_cases"],
            verbose=args.verbose,
            json_mode=json_mode,
        )
        mismatch_count += _inspect_failures(
            manifest["failure_cases"],
            json_mode=json_mode,
        )

    if args.verbose:
        _inspect_cleaning_cases(manifest["cleaning_cases"])

    total_elements = sum(len(result.document.elements) for result in loaded_results)
    total_warnings = sum(len(result.report.warnings) for result in loaded_results)
    if json_mode:
        log.success(
            "ingestion.completed",
            "文档摄取实验完成",
            documents=len(loaded_results),
            elements=total_elements,
            warnings=total_warnings,
            mismatches=mismatch_count,
        )
    elif mismatch_count:
        console.error(
            f"实验存在 {mismatch_count} 个契约不匹配；请检查 expected stage/code 与实际结果"
        )
    else:
        console.success(
            f"{len(loaded_results)} documents · {total_elements} elements · "
            f"{total_warnings} warning · {mismatch_count} mismatch"
        )
        if not args.verbose:
            console.hint("使用 --verbose 查看元素、ID、locator 和 cleaning actions")
    return 1 if mismatch_count else 0


def _load_document(case: dict[str, Any]):
    return load_document(
        FIXTURE_DIR / case["path"],
        document_id=case["document_id"],
        document_version=case["document_version"],
        source_role=SourceRole(case["source_role"]),
        evidence_eligibility=EvidenceEligibility(case["evidence_eligibility"]),
        metadata={"knowledge_scope": "after_sale"},
    )


def _render_loaded(results: list[Any], *, verbose: bool, json_mode: bool) -> None:
    rows: list[tuple[str, str, int, str, str]] = []
    for result in results:
        document = result.document
        report = result.report
        locator_summary = " + ".join(report.source_locator_kinds)
        status = "WARNING" if report.warnings else "SUCCESS"
        rows.append(
            (
                document.original_filename,
                document.file_format.value,
                report.element_count,
                locator_summary,
                status,
            )
        )
        if json_mode:
            log.success(
                "document.loaded",
                "文档加载完成",
                filename=document.original_filename,
                file_format=document.file_format.value,
                document_id=document.document_id,
                document_version=document.document_version,
                source_role=document.source_role.value,
                evidence_eligibility=document.evidence_eligibility.value,
                elements=report.element_count,
                content_hash=document.content_hash,
                locator_kinds=report.source_locator_kinds,
                cleaning_actions=report.cleaning_actions,
            )
            for warning in report.warnings:
                log.warning(
                    warning.code,
                    warning.message,
                    filename=document.original_filename,
                    locator=warning.locator.describe() if warning.locator else "document",
                )

    if json_mode:
        return
    console.table(
        ("File", "Format", "Elements", "Locator", "Status"),
        rows,
        styles=(None, "cyan", "magenta", None, None),
    )
    for result in results:
        for warning in result.report.warnings:
            location = warning.locator.describe() if warning.locator else "document"
            console.warning(
                f"{result.document.original_filename} · {warning.code} · "
                f"{location} · {warning.message}"
            )
    if not verbose:
        return
    console.section("Document details")
    for result in results:
        document = result.document
        console.field(
            document.original_filename,
            f"{document.document_id}@{document.document_version} · "
            f"hash={document.content_hash[:12]}",
        )
        console.table(
            ("#", "Kind", "Element ID", "Locator", "Cleaning", "Text preview"),
            (
                (
                    element.ordinal,
                    element.kind.value,
                    element.element_id,
                    element.locator.describe(),
                    ", ".join(element.cleaning_actions) or "—",
                    " ".join(element.text.split())[:100],
                )
                for element in document.elements
            ),
        )


def _inspect_warning_cases(
    cases: list[dict[str, Any]],
    *,
    verbose: bool,
    json_mode: bool,
) -> int:
    mismatches = 0
    rows: list[tuple[str, str, str, str]] = []
    for case in cases:
        result = load_document(
            FIXTURE_DIR / case["path"],
            document_id=f"WARN-{Path(case['path']).stem.upper()}",
            document_version="1.0.0",
            source_role=SourceRole.REFERENCE_KNOWLEDGE,
            evidence_eligibility=EvidenceEligibility.INELIGIBLE,
        )
        warning_codes = {warning.code for warning in result.report.warnings}
        text = result.document.text
        actual_first = (
            case["extracted_first"]
            if text.index(case["extracted_first"]) < text.index(case["visual_first"])
            else case["visual_first"]
        )
        matched = (
            case["expected_warning"] in warning_codes
            and actual_first == case["extracted_first"]
        )
        mismatches += int(not matched)
        rows.append(
            (
                case["path"],
                case["visual_first"],
                actual_first,
                "MATCH" if matched else "MISMATCH",
            )
        )
        if json_mode:
            method = log.success if matched else log.error
            method(
                "pdf.reading_order_checked",
                "PDF 阅读顺序对照完成",
                filename=case["path"],
                visual_first=case["visual_first"],
                extracted_first=actual_first,
                expected_warning=case["expected_warning"],
                warning_codes=sorted(warning_codes),
                matched=matched,
            )
        elif verbose:
            console.text("extracted_text", text, indent=1)
    if not json_mode:
        console.section("PDF reading-order case")
        console.table(
            ("File", "Visual first", "Extracted first", "Result"),
            rows,
        )
        console.info(
            "expected warning · "
            + ", ".join(case["expected_warning"] for case in cases)
        )
    return mismatches


def _inspect_failures(cases: list[dict[str, Any]], *, json_mode: bool) -> int:
    rows: list[tuple[str, str, str, str]] = []
    mismatch_details: list[str] = []
    mismatches = 0
    for case in cases:
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
            matched = (
                exc.stage.value == case["expected_stage"]
                and exc.code.value == case["expected_error"]
            )
            actual_stage = exc.stage.value
            actual_code = exc.code.value
        else:
            matched = False
            actual_stage = "success"
            actual_code = "none"
        mismatches += int(not matched)
        if not matched:
            mismatch_details.append(
                f"{path.name}: expected={case['expected_stage']}/{case['expected_error']} "
                f"actual={actual_stage}/{actual_code}"
            )
        rows.append(
            (
                path.name,
                actual_stage,
                actual_code,
                "MATCH" if matched else "MISMATCH",
            )
        )
        if json_mode:
            method = log.success if matched else log.error
            method(
                "boundary_contract.checked",
                "支持边界与错误契约检查完成",
                filename=path.name,
                expected_stage=case["expected_stage"],
                actual_stage=actual_stage,
                expected_code=case["expected_error"],
                actual_code=actual_code,
                matched=matched,
            )
    if not json_mode:
        console.section("Boundary and error contracts")
        console.table(
            ("File", "Stage", "Code", "Result"),
            rows,
        )
        for detail in mismatch_details:
            console.error(detail)
    return mismatches


def _inspect_cleaning_cases(cases: list[dict[str, Any]]) -> None:
    console.section("Cleaning probe")
    for case in cases:
        result = _load_document(case)
        console.info(
            f"{case['path']} · actions="
            f"{', '.join(result.report.cleaning_actions) or 'none'}"
        )
        console.table(
            ("Kind", "Actions", "Normalized text"),
            (
                (
                    element.kind.value,
                    ", ".join(element.cleaning_actions) or "—",
                    element.text,
                )
                for element in result.document.elements
            ),
        )


if __name__ == "__main__":
    raise SystemExit(main())
