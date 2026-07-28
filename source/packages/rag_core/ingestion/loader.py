"""Public document-loading orchestration."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

from rag_core.ingestion.cleaning import clean_text
from rag_core.ingestion.errors import IngestionError, IngestionErrorCode, IngestionStage
from rag_core.ingestion.models import (
    DocumentElement,
    EvidenceEligibility,
    FileArtifact,
    FileFormat,
    KnowledgeDocument,
    LoadReport,
    LoadResult,
    LoaderConfig,
    SourceRole,
)
from rag_core.ingestion.parsers import parse_artifact

_EXTENSION_FORMATS = {
    ".txt": FileFormat.TXT,
    ".md": FileFormat.MARKDOWN,
    ".markdown": FileFormat.MARKDOWN,
    ".docx": FileFormat.DOCX,
    ".pdf": FileFormat.PDF,
}


def load_document(
    path: str | Path,
    *,
    document_id: str,
    document_version: str,
    source_role: SourceRole,
    evidence_eligibility: EvidenceEligibility,
    metadata: Mapping[str, str] | None = None,
    config: LoaderConfig | None = None,
) -> LoadResult:
    """Load one supported file without chunking or indexing it."""

    document_id = document_id.strip()
    document_version = document_version.strip()
    if not document_id or not document_version:
        raise ValueError("document_id 和 document_version 不能为空")
    if (
        source_role is SourceRole.HISTORICAL_MATERIAL
        and evidence_eligibility is EvidenceEligibility.CURRENT_EVIDENCE
    ):
        raise ValueError("Historical Material 不能直接标记为 current_evidence")

    loader_config = config or LoaderConfig()
    artifact = _read_artifact(path)
    if artifact.size_bytes > loader_config.max_file_bytes:
        raise IngestionError(
            code=IngestionErrorCode.FILE_TOO_LARGE,
            stage=IngestionStage.FORMAT_DETECTION,
            message=f"文件大小 {artifact.size_bytes} 超过上限 {loader_config.max_file_bytes}",
            filename=artifact.filename,
        )

    file_format = _detect_format(artifact)
    parsed = parse_artifact(artifact, file_format, loader_config)
    elements: list[DocumentElement] = []
    all_cleaning_actions: list[str] = []

    for parsed_element in parsed.elements:
        try:
            cleaned, actions = clean_text(parsed_element.text, loader_config)
        except Exception as exc:
            raise IngestionError(
                code=IngestionErrorCode.CLEANING_FAILED,
                stage=IngestionStage.CLEANING,
                message=f"文本清洗失败：{exc}",
                filename=artifact.filename,
                raw=exc,
            ) from exc
        if not cleaned:
            continue
        ordinal = len(elements) + 1
        element_id = _element_id(
            document_id,
            document_version,
            ordinal,
            parsed_element.locator.describe(),
            cleaned,
        )
        elements.append(
            DocumentElement(
                element_id=element_id,
                kind=parsed_element.kind,
                text=cleaned,
                locator=parsed_element.locator,
                ordinal=ordinal,
                cleaning_actions=actions,
            )
        )
        for action in actions:
            if action not in all_cleaning_actions:
                all_cleaning_actions.append(action)

    if not elements:
        raise IngestionError(
            code=IngestionErrorCode.EMPTY_DOCUMENT,
            stage=IngestionStage.EMPTY_CONTENT,
            message="解析和清洗后没有有效 DocumentElement",
            filename=artifact.filename,
        )

    document = KnowledgeDocument(
        document_id=document_id,
        document_version=document_version,
        original_filename=artifact.filename,
        file_format=file_format,
        source_role=source_role,
        evidence_eligibility=evidence_eligibility,
        content_hash=artifact.content_hash,
        elements=tuple(elements),
        metadata={str(key): str(value) for key, value in (metadata or {}).items()},
    )
    report = LoadReport(
        filename=artifact.filename,
        file_format=file_format,
        status="loaded",
        element_count=len(elements),
        source_locator_kinds=tuple(dict.fromkeys(element.locator.kind for element in elements)),
        cleaning_actions=tuple(all_cleaning_actions),
        warnings=parsed.warnings,
    )
    return LoadResult(artifact=artifact, document=document, report=report)


def _read_artifact(path: str | Path) -> FileArtifact:
    try:
        return FileArtifact.from_path(path)
    except FileNotFoundError as exc:
        raise IngestionError(
            code=IngestionErrorCode.FILE_NOT_FOUND,
            stage=IngestionStage.FORMAT_DETECTION,
            message="文件不存在",
            filename=Path(path).name,
            raw=exc,
        ) from exc


def _detect_format(artifact: FileArtifact) -> FileFormat:
    suffix = artifact.path.suffix.lower()
    file_format = _EXTENSION_FORMATS.get(suffix)
    if file_format is None:
        raise IngestionError(
            code=IngestionErrorCode.UNSUPPORTED_FORMAT,
            stage=IngestionStage.FORMAT_DETECTION,
            message=f"不支持扩展名 {suffix or '(none)'}",
            filename=artifact.filename,
        )
    if file_format is FileFormat.PDF and not artifact.content.startswith(b"%PDF-"):
        raise IngestionError(
            code=IngestionErrorCode.FORMAT_MISMATCH,
            stage=IngestionStage.FORMAT_DETECTION,
            message="扩展名是 .pdf，但文件头不是 PDF",
            filename=artifact.filename,
        )
    if file_format is FileFormat.DOCX and not artifact.content.startswith(b"PK"):
        raise IngestionError(
            code=IngestionErrorCode.FORMAT_MISMATCH,
            stage=IngestionStage.FORMAT_DETECTION,
            message="扩展名是 .docx，但文件不是 OOXML ZIP 容器",
            filename=artifact.filename,
        )
    return file_format


def _element_id(
    document_id: str,
    document_version: str,
    ordinal: int,
    locator: str,
    text: str,
) -> str:
    payload = "\x1f".join((document_id, document_version, str(ordinal), locator, text))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"element_{digest}"
