from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


CHAPTER_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHAPTER_ROOT / "data"
SUPPORTED_SUFFIXES = (".md", ".txt")
DEFAULT_CHUNK_SIZE = 180
DEFAULT_CHUNK_OVERLAP = 30


@dataclass(frozen=True)
class TextChunk:
    content: str
    start_index: int
    end_index: int


@dataclass(frozen=True)
class SourceChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int]


@dataclass(frozen=True)
class SplitterConfig:
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")


def detect_file_type(path: Path) -> str:
    return path.suffix.lower()


def normalize_text(text: str) -> str:
    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def discover_documents(
    data_dir: Path = DATA_DIR,
    supported_suffixes: tuple[str, ...] = SUPPORTED_SUFFIXES,
) -> list[Path]:
    return sorted(
        path
        for path in data_dir.rglob("*")
        if path.is_file()
        and path.name.lower() != "readme.md"
        and detect_file_type(path) in supported_suffixes
    )


def load_document(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    file_type = detect_file_type(path)
    if file_type not in SUPPORTED_SUFFIXES:
        supported = ", ".join(SUPPORTED_SUFFIXES)
        raise ValueError(f"Unsupported file type {file_type!r}. Supported: {supported}")

    return normalize_text(path.read_text(encoding="utf-8"))


def _trimmed_window(window: str, start_index: int) -> tuple[str, int, int]:
    left_trimmed = window.lstrip()
    leading_chars = len(window) - len(left_trimmed)
    trimmed = left_trimmed.rstrip()
    chunk_start = start_index + leading_chars
    chunk_end = chunk_start + len(trimmed)
    return trimmed, chunk_start, chunk_end


def _choose_breakpoint(window: str, chunk_size: int) -> int:
    min_breakpoint = max(chunk_size // 2, 1)
    separators = ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ")

    for separator in separators:
        position = window.rfind(separator)
        if position >= min_breakpoint:
            return position + len(separator)

    return len(window)


def split_text(text: str, config: SplitterConfig) -> list[TextChunk]:
    if not text:
        return []

    chunks: list[TextChunk] = []
    start_index = 0
    text_length = len(text)

    while start_index < text_length:
        tentative_end = min(start_index + config.chunk_size, text_length)
        window = text[start_index:tentative_end]
        if tentative_end < text_length:
            breakpoint = _choose_breakpoint(window, config.chunk_size)
            tentative_end = start_index + breakpoint
            window = text[start_index:tentative_end]

        trimmed, chunk_start, chunk_end = _trimmed_window(window, start_index)
        if trimmed:
            chunks.append(
                TextChunk(
                    content=trimmed,
                    start_index=chunk_start,
                    end_index=chunk_end,
                )
            )

        if tentative_end >= text_length:
            break

        start_index = max(tentative_end - config.chunk_overlap, start_index + 1)

    return chunks


def _display_source(path: Path) -> str:
    try:
        return path.resolve().relative_to(CHAPTER_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_base_metadata(path: Path, text: str) -> dict[str, str | int]:
    line_count = 0 if not text else text.count("\n") + 1
    return {
        "source": _display_source(path),
        "filename": path.name,
        "suffix": path.suffix.lower(),
        "char_count": len(text),
        "line_count": line_count,
    }


def build_chunk_metadata(
    base_metadata: dict[str, str | int],
    chunk_index: int,
    start_index: int,
    end_index: int,
) -> dict[str, str | int]:
    return {
        **base_metadata,
        "chunk_index": chunk_index,
        "char_start": start_index,
        "char_end": end_index,
        "chunk_chars": end_index - start_index,
    }


def stable_document_id(source: str) -> str:
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def stable_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    return f"{document_id}:{chunk_index}:{digest}"


def prepare_chunks(path: Path, text: str, config: SplitterConfig) -> list[SourceChunk]:
    resolved_path = path.resolve()
    document_id = stable_document_id(resolved_path.as_posix())
    base_metadata = build_base_metadata(path, text)
    chunks: list[SourceChunk] = []

    for index, chunk in enumerate(split_text(text, config)):
        chunks.append(
            SourceChunk(
                chunk_id=stable_chunk_id(document_id, index, chunk.content),
                document_id=document_id,
                content=chunk.content,
                metadata=build_chunk_metadata(
                    base_metadata=base_metadata,
                    chunk_index=index,
                    start_index=chunk.start_index,
                    end_index=chunk.end_index,
                ),
            )
        )

    return chunks


def load_and_prepare_chunks(path: Path, config: SplitterConfig) -> list[SourceChunk]:
    return prepare_chunks(path, load_document(path), config)


def build_chunk_corpus(
    data_dir: Path = DATA_DIR,
    config: SplitterConfig | None = None,
) -> list[SourceChunk]:
    splitter_config = config or SplitterConfig()
    chunks: list[SourceChunk] = []
    for path in discover_documents(data_dir):
        chunks.extend(load_and_prepare_chunks(path, splitter_config))
    return chunks
