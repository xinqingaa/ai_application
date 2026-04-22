from pathlib import Path


def build_base_metadata(path: Path) -> dict[str, str]:
    """Build the minimum metadata every chunk should carry."""

    return {
        "source": str(path),
        "filename": path.name,
        "suffix": path.suffix.lower(),
    }
