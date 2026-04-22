from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import re

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    PdfReader = None


CHAPTER_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHAPTER_ROOT / "data"
SUPPORTED_SUFFIXES = (".md", ".txt", ".pdf")
DEFAULT_CHUNK_SIZE = 180
DEFAULT_CHUNK_OVERLAP = 30
HEADER_PATTERN = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")


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
class DocumentCandidate:
    path: Path
    accepted: bool
    reason: str


@dataclass(frozen=True)
class LoadedDocument:
    path: Path
    content: str
    metadata: dict[str, str | int]


@dataclass(frozen=True)
class MarkdownSection:
    content: str
    start_index: int
    end_index: int
    section_title: str
    header_path: str
    header_level: int


@dataclass(frozen=True)
class ChunkDraft:
    content: str
    start_index: int
    end_index: int
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


@dataclass(frozen=True)
class DocumentPipelineResult:
    candidates: tuple[DocumentCandidate, ...]
    documents: tuple[LoadedDocument, ...]
    chunks: tuple[SourceChunk, ...]
    config: SplitterConfig

    @property
    def accepted_documents(self) -> int:
        return len(self.documents)

    @property
    def ignored_candidates(self) -> int:
        return sum(1 for candidate in self.candidates if not candidate.accepted)

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)


def detect_file_type(path: Path) -> str:
    return path.suffix.lower()


def choose_loader_name(path: Path) -> str:
    file_type = detect_file_type(path)
    if file_type == ".md":
        return "markdown_loader"
    if file_type == ".txt":
        return "text_loader"
    if file_type == ".pdf":
        return "pypdf.PdfReader"
    return "unsupported"


def inspect_document_candidate(
    path: Path,
    supported_suffixes: tuple[str, ...] = SUPPORTED_SUFFIXES,
) -> DocumentCandidate:
    file_type = detect_file_type(path)

    if not path.is_file():
        return DocumentCandidate(
            path=path,
            accepted=False,
            reason="not a file",
        )

    if path.name.lower() == "readme.md":
        return DocumentCandidate(
            path=path,
            accepted=False,
            reason="chapter helper file, not a knowledge source",
        )

    if file_type not in supported_suffixes:
        return DocumentCandidate(
            path=path,
            accepted=False,
            reason=f"unsupported suffix: {file_type or '(none)'}",
        )

    return DocumentCandidate(
        path=path,
        accepted=True,
        reason=f"supported suffix: {file_type} via {choose_loader_name(path)}",
    )


def normalize_text(text: str) -> str:
    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def inspect_document_candidates(
    data_dir: Path = DATA_DIR,
    supported_suffixes: tuple[str, ...] = SUPPORTED_SUFFIXES,
) -> list[DocumentCandidate]:
    return sorted(
        (
            inspect_document_candidate(path, supported_suffixes)
            for path in data_dir.rglob("*")
            if path.is_file()
        ),
        key=lambda candidate: candidate.path.name.lower(),
    )


def discover_documents(
    data_dir: Path = DATA_DIR,
    supported_suffixes: tuple[str, ...] = SUPPORTED_SUFFIXES,
) -> list[Path]:
    return sorted(
        candidate.path
        for candidate in inspect_document_candidates(data_dir, supported_suffixes)
        if candidate.accepted
    )


def _read_pdf(path: Path) -> LoadedDocument:
    if PdfReader is None:
        raise ImportError(
            "pypdf is required for PDF loading. Run `python -m pip install -r requirements.txt`."
        )

    reader = PdfReader(str(path))
    page_texts: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        extracted = normalize_text(page.extract_text() or "")
        if extracted:
            page_texts.append(f"[Page {index}]\n{extracted}")

    combined_text = "\n\n".join(page_texts).strip()
    if not combined_text:
        raise ValueError("PDF has no extractable text. OCR is out of scope for this chapter.")

    return LoadedDocument(
        path=path,
        content=combined_text,
        metadata={
            "loader": choose_loader_name(path),
            "page_count": len(reader.pages),
        },
    )


def load_document_record(path: Path) -> LoadedDocument:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    file_type = detect_file_type(path)
    if file_type not in SUPPORTED_SUFFIXES:
        supported = ", ".join(SUPPORTED_SUFFIXES)
        raise ValueError(f"Unsupported file type {file_type!r}. Supported: {supported}")

    if file_type == ".pdf":
        return _read_pdf(path)

    return LoadedDocument(
        path=path,
        content=normalize_text(path.read_text(encoding="utf-8")),
        metadata={"loader": choose_loader_name(path)},
    )


def load_document(path: Path) -> str:
    return load_document_record(path).content


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


def split_markdown_by_headers(text: str) -> list[MarkdownSection]:
    if not text:
        return []

    matches = list(HEADER_PATTERN.finditer(text))
    if not matches:
        return [
            MarkdownSection(
                content=text,
                start_index=0,
                end_index=len(text),
                section_title="",
                header_path="",
                header_level=0,
            )
        ]

    sections: list[MarkdownSection] = []
    stack: list[str] = []
    leading_text = text[: matches[0].start()]
    if leading_text.strip():
        trimmed, start_index, end_index = _trimmed_window(leading_text, 0)
        sections.append(
            MarkdownSection(
                content=trimmed,
                start_index=start_index,
                end_index=end_index,
                section_title="",
                header_path="",
                header_level=0,
            )
        )

    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        stack = stack[: level - 1]
        stack.append(title)

        raw_start = match.start()
        raw_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw_section = text[raw_start:raw_end]
        trimmed, start_index, end_index = _trimmed_window(raw_section, raw_start)
        if not trimmed:
            continue

        sections.append(
            MarkdownSection(
                content=trimmed,
                start_index=start_index,
                end_index=end_index,
                section_title=title,
                header_path=" > ".join(stack),
                header_level=level,
            )
        )

    return sections


def split_document(path: Path, text: str, config: SplitterConfig) -> list[ChunkDraft]:
    if detect_file_type(path) != ".md":
        return [
            ChunkDraft(
                content=chunk.content,
                start_index=chunk.start_index,
                end_index=chunk.end_index,
                metadata={},
            )
            for chunk in split_text(text, config)
        ]

    drafts: list[ChunkDraft] = []
    for section in split_markdown_by_headers(text):
        section_chunks = split_text(section.content, config)
        for chunk in section_chunks:
            drafts.append(
                ChunkDraft(
                    content=chunk.content,
                    start_index=section.start_index + chunk.start_index,
                    end_index=section.start_index + chunk.end_index,
                    metadata={
                        "section_title": section.section_title,
                        "header_path": section.header_path,
                        "header_level": section.header_level,
                    },
                )
            )
    return drafts


def _display_source(path: Path) -> str:
    try:
        return path.resolve().relative_to(CHAPTER_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_base_metadata(
    path: Path,
    text: str,
    extra_metadata: dict[str, str | int] | None = None,
) -> dict[str, str | int]:
    line_count = 0 if not text else text.count("\n") + 1
    metadata: dict[str, str | int] = {
        "source": _display_source(path),
        "filename": path.name,
        "suffix": path.suffix.lower(),
        "char_count": len(text),
        "line_count": line_count,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return metadata


def build_chunk_metadata(
    base_metadata: dict[str, str | int],
    chunk_index: int,
    start_index: int,
    end_index: int,
    extra_metadata: dict[str, str | int] | None = None,
) -> dict[str, str | int]:
    metadata: dict[str, str | int] = {
        **base_metadata,
        "chunk_index": chunk_index,
        "char_start": start_index,
        "char_end": end_index,
        "chunk_chars": end_index - start_index,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return metadata


def stable_document_id(source: str) -> str:
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def stable_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    return f"{document_id}:{chunk_index}:{digest}"


def prepare_chunks(
    path: Path,
    text: str,
    config: SplitterConfig,
    document_metadata: dict[str, str | int] | None = None,
) -> list[SourceChunk]:
    resolved_path = path.resolve()
    document_id = stable_document_id(resolved_path.as_posix())
    base_metadata = build_base_metadata(path, text, extra_metadata=document_metadata)
    chunks: list[SourceChunk] = []

    for index, draft in enumerate(split_document(path, text, config)):
        chunks.append(
            SourceChunk(
                chunk_id=stable_chunk_id(document_id, index, draft.content),
                document_id=document_id,
                content=draft.content,
                metadata=build_chunk_metadata(
                    base_metadata=base_metadata,
                    chunk_index=index,
                    start_index=draft.start_index,
                    end_index=draft.end_index,
                    extra_metadata=draft.metadata,
                ),
            )
        )

    return chunks


def load_and_prepare_chunks(path: Path, config: SplitterConfig) -> list[SourceChunk]:
    document = load_document_record(path)
    return prepare_chunks(path, document.content, config, document.metadata)


def build_chunk_corpus(
    data_dir: Path = DATA_DIR,
    config: SplitterConfig | None = None,
) -> list[SourceChunk]:
    splitter_config = config or SplitterConfig()
    chunks: list[SourceChunk] = []
    for path in discover_documents(data_dir):
        chunks.extend(load_and_prepare_chunks(path, splitter_config))
    return chunks


def run_document_pipeline(
    data_dir: Path = DATA_DIR,
    config: SplitterConfig | None = None,
) -> DocumentPipelineResult:
    splitter_config = config or SplitterConfig()
    candidates = tuple(inspect_document_candidates(data_dir))
    documents: list[LoadedDocument] = []
    chunks: list[SourceChunk] = []

    for candidate in candidates:
        if not candidate.accepted:
            continue
        document = load_document_record(candidate.path)
        documents.append(document)
        chunks.extend(prepare_chunks(candidate.path, document.content, splitter_config, document.metadata))

    return DocumentPipelineResult(
        candidates=candidates,
        documents=tuple(documents),
        chunks=tuple(chunks),
        config=splitter_config,
    )
