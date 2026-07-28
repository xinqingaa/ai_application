"""Data contracts for document ingestion."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping


class FileFormat(str, Enum):
    TXT = "txt"
    MARKDOWN = "markdown"
    DOCX = "docx"
    PDF = "pdf"


class SourceRole(str, Enum):
    REFERENCE_KNOWLEDGE = "reference_knowledge"
    HISTORICAL_MATERIAL = "historical_material"


class EvidenceEligibility(str, Enum):
    CURRENT_EVIDENCE = "current_evidence"
    HISTORICAL_CONTEXT = "historical_context"
    INELIGIBLE = "ineligible"


class ElementKind(str, Enum):
    TITLE = "title"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE = "code"
    PAGE = "page"


@dataclass(frozen=True)
class LoaderConfig:
    text_encoding: str = "utf-8-sig"
    max_file_bytes: int = 20 * 1024 * 1024
    normalize_unicode: bool = True
    collapse_blank_lines: bool = True

    def __post_init__(self) -> None:
        if self.max_file_bytes <= 0:
            raise ValueError("LoaderConfig.max_file_bytes 必须大于 0")


@dataclass(frozen=True)
class FileArtifact:
    path: Path
    filename: str
    size_bytes: int
    content_hash: str
    content: bytes = field(repr=False)

    @classmethod
    def from_path(cls, path: str | Path) -> "FileArtifact":
        resolved = Path(path).expanduser().resolve()
        content = resolved.read_bytes()
        return cls(
            path=resolved,
            filename=resolved.name,
            size_bytes=len(content),
            content_hash=hashlib.sha256(content).hexdigest(),
            content=content,
        )


@dataclass(frozen=True)
class SourceLocator:
    kind: str
    line_start: int | None = None
    line_end: int | None = None
    page_number: int | None = None
    paragraph_index: int | None = None
    table_index: int | None = None
    heading_path: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        numeric_values = (
            self.line_start,
            self.line_end,
            self.page_number,
            self.paragraph_index,
            self.table_index,
        )
        if any(value is not None and value <= 0 for value in numeric_values):
            raise ValueError("SourceLocator 的位置编号必须从 1 开始")

    def describe(self) -> str:
        parts = [self.kind]
        if self.line_start is not None:
            line_range = str(self.line_start)
            if self.line_end is not None and self.line_end != self.line_start:
                line_range += f"-{self.line_end}"
            parts.append(f"lines={line_range}")
        if self.page_number is not None:
            parts.append(f"page={self.page_number}")
        if self.paragraph_index is not None:
            parts.append(f"paragraph={self.paragraph_index}")
        if self.table_index is not None:
            parts.append(f"table={self.table_index}")
        if self.heading_path:
            parts.append(f"heading={' > '.join(self.heading_path)}")
        return ", ".join(parts)


@dataclass(frozen=True)
class DocumentElement:
    element_id: str
    kind: ElementKind
    text: str
    locator: SourceLocator
    ordinal: int
    cleaning_actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class LoadWarning:
    code: str
    message: str
    locator: SourceLocator | None = None


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    document_version: str
    original_filename: str
    file_format: FileFormat
    source_role: SourceRole
    evidence_eligibility: EvidenceEligibility
    content_hash: str
    elements: tuple[DocumentElement, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return "\n\n".join(element.text for element in self.elements)


@dataclass(frozen=True)
class LoadReport:
    filename: str
    file_format: FileFormat
    status: str
    element_count: int
    source_locator_kinds: tuple[str, ...]
    cleaning_actions: tuple[str, ...]
    warnings: tuple[LoadWarning, ...] = ()


@dataclass(frozen=True)
class LoadResult:
    artifact: FileArtifact
    document: KnowledgeDocument
    report: LoadReport
