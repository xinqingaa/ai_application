from pathlib import Path

from app.config import settings


def detect_file_type(path: Path) -> str:
    """Return a normalized suffix for routing to the right loader."""

    return path.suffix.lower()


def normalize_text(text: str) -> str:
    """Normalize line endings and trailing spaces without destroying structure."""

    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def load_text_file(path: Path) -> str:
    """Load plain text files with basic normalization."""

    return normalize_text(path.read_text(encoding="utf-8"))


def load_markdown_file(path: Path) -> str:
    """Load markdown as raw text while preserving headings and list markers."""

    return normalize_text(path.read_text(encoding="utf-8"))


def discover_documents(
    data_dir: Path, supported_suffixes: tuple[str, ...] | None = None
) -> list[Path]:
    """Return supported documents under the data directory in deterministic order."""

    suffixes = supported_suffixes or settings.supported_suffixes
    return sorted(
        path
        for path in data_dir.rglob("*")
        if path.is_file()
        and path.name.lower() != "readme.md"
        and detect_file_type(path) in suffixes
    )


def load_document(path: Path) -> str:
    """Shared ingestion entry point for turning a file into normalized raw text."""

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    file_type = detect_file_type(path)
    if file_type not in settings.supported_suffixes:
        supported = ", ".join(settings.supported_suffixes)
        raise ValueError(f"Unsupported file type {file_type!r}. Supported: {supported}")

    if file_type == ".txt":
        return load_text_file(path)
    if file_type == ".md":
        return load_markdown_file(path)

    raise ValueError(f"No loader registered for file type {file_type!r}")
