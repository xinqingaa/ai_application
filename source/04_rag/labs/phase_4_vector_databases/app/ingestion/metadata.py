from pathlib import Path


def _display_source(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_base_metadata(path: Path, text: str) -> dict[str, str | int]:
    """Build the minimum metadata every chunk should carry."""

    line_count = 0 if not text else text.count("\n") + 1
    return {
        "source": _display_source(path),
        "filename": path.name,
        "suffix": path.suffix.lower(),
        "char_count": len(text),
        "line_count": line_count,
    }


def build_chunk_metadata(
    base_metadata: dict[str, str | int], chunk_index: int, start_index: int, end_index: int
) -> dict[str, str | int]:
    """Attach chunk-level metadata required by later indexing and retrieval stages."""

    return {
        **base_metadata,
        "chunk_index": chunk_index,
        "char_start": start_index,
        "char_end": end_index,
        "chunk_chars": end_index - start_index,
    }
