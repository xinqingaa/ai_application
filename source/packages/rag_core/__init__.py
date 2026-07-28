"""Shared RAG capabilities for the review assistant."""

from rag_core.ingestion import (
    DocumentElement,
    ElementKind,
    EvidenceEligibility,
    FileArtifact,
    FileFormat,
    IngestionError,
    IngestionErrorCode,
    IngestionStage,
    KnowledgeDocument,
    LoadReport,
    LoadResult,
    LoadWarning,
    LoaderConfig,
    SourceLocator,
    SourceRole,
    load_document,
)

__all__ = [
    "DocumentElement",
    "ElementKind",
    "EvidenceEligibility",
    "FileArtifact",
    "FileFormat",
    "IngestionError",
    "IngestionErrorCode",
    "IngestionStage",
    "KnowledgeDocument",
    "LoadReport",
    "LoadResult",
    "LoadWarning",
    "LoaderConfig",
    "SourceLocator",
    "SourceRole",
    "load_document",
]
