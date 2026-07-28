"""Structured ingestion errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class IngestionStage(str, Enum):
    FORMAT_DETECTION = "format_detection"
    PARSE = "parse"
    CLEANING = "cleaning"
    EMPTY_CONTENT = "empty_content"


class IngestionErrorCode(str, Enum):
    FILE_NOT_FOUND = "file_not_found"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    FORMAT_MISMATCH = "format_mismatch"
    TEXT_DECODE_FAILED = "text_decode_failed"
    DOCUMENT_PARSE_FAILED = "document_parse_failed"
    ENCRYPTED_PDF = "encrypted_pdf"
    PDF_TEXT_LAYER_MISSING = "pdf_text_layer_missing"
    EMPTY_DOCUMENT = "empty_document"
    CLEANING_FAILED = "cleaning_failed"


@dataclass
class IngestionError(Exception):
    code: IngestionErrorCode
    stage: IngestionStage
    message: str
    filename: str | None = None
    raw: Any = None

    def __str__(self) -> str:
        source = f" [{self.filename}]" if self.filename else ""
        return f"{self.stage.value}/{self.code.value}{source}: {self.message}"
