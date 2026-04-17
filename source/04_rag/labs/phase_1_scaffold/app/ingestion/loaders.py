from pathlib import Path


def detect_file_type(path: Path) -> str:
    """Return a normalized suffix for routing to the right loader."""

    return path.suffix.lower()


def load_document(path: Path) -> str:
    """Phase 2 entry point for turning a file into raw text."""

    raise NotImplementedError("Phase 2 should implement document loading here.")
