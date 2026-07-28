"""Document loading, cleaning, and source-location contracts."""

from rag_core.ingestion.errors import IngestionError, IngestionErrorCode, IngestionStage
from rag_core.ingestion.loader import load_document
from rag_core.ingestion.models import (
    DocumentElement,
    ElementKind,
    EvidenceEligibility,
    FileArtifact,
    FileFormat,
    KnowledgeDocument,
    LoadReport,
    LoadResult,
    LoadWarning,
    LoaderConfig,
    SourceLocator,
    SourceRole,
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
