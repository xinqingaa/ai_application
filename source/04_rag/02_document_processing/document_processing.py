"""第二章文档处理核心模块。

本模块把教学代码里的主链路收束成一条明确的输入流程：

Path
-> DocumentCandidate
-> LoadedDocument
-> ChunkDraft
-> SourceChunk
-> DocumentPipelineResult
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import re

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - 仅在未安装依赖时触发
    PdfReader = None


CHAPTER_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHAPTER_ROOT / "data"
SUPPORTED_SUFFIXES = (".md", ".txt", ".pdf")
DEFAULT_CHUNK_SIZE = 180
DEFAULT_CHUNK_OVERLAP = 30
HEADER_PATTERN = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class TextChunk:
    """通用切分器输出的基础文本块。

    属性：
        content: 去掉首尾空白后的 chunk 文本。
        start_index: 在原始文本中的起始字符位置，左闭。
        end_index: 在原始文本中的结束字符位置，右开。
    """

    content: str
    start_index: int
    end_index: int


@dataclass(frozen=True)
class SourceChunk:
    """后续章节统一消费的标准 chunk 对象。

    属性：
        chunk_id: 稳定的 chunk 标识，用于 upsert、调试和追踪。
        document_id: 稳定的文档标识，用于更新、删除和归属关联。
        content: 最终要进入 embedding 和索引阶段的文本。
        metadata: 文档级和 chunk 级 metadata 的合并结果。
    """

    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int]


@dataclass(frozen=True)
class DocumentCandidate:
    """文档发现阶段的判断结果。"""

    path: Path
    accepted: bool
    reason: str


@dataclass(frozen=True)
class LoadedDocument:
    """已经完成 loader 读取和文本规范化的文档。"""

    path: Path
    content: str
    metadata: dict[str, str | int]


@dataclass(frozen=True)
class MarkdownSection:
    """Markdown 按标题切分后的中间分段。"""

    content: str
    start_index: int
    end_index: int
    section_title: str
    header_path: str
    header_level: int


@dataclass(frozen=True)
class ChunkDraft:
    """从切分阶段走向标准 chunk 之前的临时对象。"""

    content: str
    start_index: int
    end_index: int
    metadata: dict[str, str | int]


@dataclass(frozen=True)
class SplitterConfig:
    """切分配置。

    属性：
        chunk_size: 每个切分窗口期望的最大字符数。
        chunk_overlap: 相邻 chunk 之间保留的重叠字符数。
    """

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
    """目录级文档处理结果。"""

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
    """返回文件的小写后缀。"""

    return path.suffix.lower()


def choose_loader_name(path: Path) -> str:
    """根据文件类型给出本章使用的 loader 名称。"""

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
    """判断一个路径是否应该进入本章输入层。
    非文件、非readme.md、非SUPPORTED_SUFFIXES后缀类型才视为可以进行系统
    参数：
        path: 要检查的文件路径。
        supported_suffixes: 本章允许进入系统的文件后缀。

    返回：
        DocumentCandidate，包含接受或忽略的决定及原因。
    """

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
    """把不同来源的文本规整成统一格式。

    参数：
        text: 原始文本，可能来自 `.txt`、`.md` 或 PDF 页面提取。

    返回：
        统一使用 `\n`、去掉每行尾部多余空白、并去掉首尾空白的文本。
    """

    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def inspect_document_candidates(
    data_dir: Path = DATA_DIR,
    supported_suffixes: tuple[str, ...] = SUPPORTED_SUFFIXES,
) -> list[DocumentCandidate]:
    """递归扫描目录，给每个文件生成发现阶段的判断结果。"""

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
    """只返回通过发现阶段筛选的文档路径。"""

    return sorted(
        candidate.path
        for candidate in inspect_document_candidates(data_dir, supported_suffixes)
        if candidate.accepted
    )


def _read_pdf(path: Path) -> LoadedDocument:
    """读取可直接提取文本的 PDF。"""

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
    """把单个文档读取成统一文本和 loader metadata。

    参数：
        path: 支持的 `.txt`、`.md` 或 `.pdf` 文件路径。

    返回：
        LoadedDocument，包含文本内容和加载阶段 metadata。

    异常：
        FileNotFoundError: 路径不存在。
        ValueError: 文件类型不支持，或 PDF 没有可提取文本。
        ImportError: 需要读取 PDF 但当前环境未安装 `pypdf`。
    """

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
    """只返回文档文本内容的便捷封装。"""

    return load_document_record(path).content


def _trimmed_window(window: str, start_index: int) -> tuple[str, int, int]:
    """在裁掉窗口首尾空白时，同时保持字符偏移量正确。"""

    left_trimmed = window.lstrip()
    leading_chars = len(window) - len(left_trimmed)
    trimmed = left_trimmed.rstrip()
    chunk_start = start_index + leading_chars
    chunk_end = chunk_start + len(trimmed)
    return trimmed, chunk_start, chunk_end


def _choose_breakpoint(window: str, chunk_size: int) -> int:
    """优先在自然边界断开，而不是总在固定长度处硬切。"""

    min_breakpoint = max(chunk_size // 2, 1)
    separators = ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ")

    for separator in separators:
        position = window.rfind(separator)
        if position >= min_breakpoint:
            return position + len(separator)

    return len(window)


def split_text(text: str, config: SplitterConfig) -> list[TextChunk]:
    """把纯文本切成带字符范围的 `TextChunk[]`。

    参数：
        text: 已完成规范化的文本。
        config: 切分参数，控制大小和重叠。

    返回：
        按顺序排列的 TextChunk 列表。
    """

    if not text:
        return []

    chunks: list[TextChunk] = []
    start_index = 0
    text_length = len(text)

    while start_index < text_length:
        tentative_end = min(start_index + config.chunk_size, text_length)
        window = text[start_index:tentative_end]
        if tentative_end < text_length:
            # 还没到文档末尾时，优先选择更自然的断点，
            # 让后续检索和阅读看到的 chunk 更完整。
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
    """先按 Markdown 标题结构切成 section。

    参数：
        text: 已完成规范化的 Markdown 文本。

    返回：
        MarkdownSection 列表，每段都保留标题层级信息。
    """

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
    """根据文档类型选择切分策略。

    参数：
        path: 文档路径，用于决定走普通切分还是 Markdown 标题感知切分。
        text: 已完成规范化的文档文本。
        config: 切分参数。

    返回：
        ChunkDraft 列表，表示还没补齐稳定 ID 前的切分结果。
    """

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
            # Markdown section 内部切分得到的是 section 局部偏移，
            # 这里要换算回整篇文档的全局偏移，方便后续 metadata 统一引用。
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
    """优先生成相对本章目录的 source 字段，便于教学观察。"""

    try:
        return path.resolve().relative_to(CHAPTER_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_base_metadata(
    path: Path,
    text: str,
    extra_metadata: dict[str, str | int] | None = None,
) -> dict[str, str | int]:
    """构建文档级 metadata。

    参数：
        path: 文档路径。
        text: 文档全文文本。
        extra_metadata: 来自 loader 的额外 metadata，例如 `loader` 和 `page_count`。

    返回：
        所有 chunk 共用的基础 metadata。
    """

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
    """在文档级 metadata 之上补充 chunk 级字段。

    参数：
        base_metadata: 文档级 metadata。
        chunk_index: 当前 chunk 在文档内的顺序编号。
        start_index: chunk 在原始文档中的起始字符位置。
        end_index: chunk 在原始文档中的结束字符位置。
        extra_metadata: 切分阶段带来的额外字段，例如 `header_path`。

    返回：
        可直接挂到 SourceChunk 上的 metadata。
    """

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
    """根据稳定 source 生成稳定的 document_id。"""

    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def stable_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    """根据文档身份、chunk 顺序和内容生成稳定的 chunk_id。"""

    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    return f"{document_id}:{chunk_index}:{digest}"


def prepare_chunks(
    path: Path,
    text: str,
    config: SplitterConfig,
    document_metadata: dict[str, str | int] | None = None,
) -> list[SourceChunk]:
    """把单篇文档收束成最终 `SourceChunk[]`。

    参数：
        path: 文档路径。
        text: 文档全文文本。
        config: 切分参数。
        document_metadata: loader 阶段产生的 metadata。

    返回：
        已补齐稳定 ID 和 metadata 的标准 chunk 列表。
    """

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
    """执行单文档主链路中的 `load -> prepare` 两步。"""

    document = load_document_record(path)
    return prepare_chunks(path, document.content, config, document.metadata)


def build_chunk_corpus(
    data_dir: Path = DATA_DIR,
    config: SplitterConfig | None = None,
) -> list[SourceChunk]:
    """对目录下所有已接受文档批量构建 chunk 语料。"""

    splitter_config = config or SplitterConfig()
    chunks: list[SourceChunk] = []
    for path in discover_documents(data_dir):
        chunks.extend(load_and_prepare_chunks(path, splitter_config))
    return chunks


def run_document_pipeline(
    data_dir: Path = DATA_DIR,
    config: SplitterConfig | None = None,
) -> DocumentPipelineResult:
    """运行目录级主链路。

    参数：
        data_dir: 本次要处理的数据目录。
        config: 可选的切分配置；不传时使用默认值。

    返回：
        DocumentPipelineResult，包含候选文件、已加载文档、最终 chunks 和配置。
    """

    splitter_config = config or SplitterConfig()
    candidates = tuple(inspect_document_candidates(data_dir))
    documents: list[LoadedDocument] = []
    chunks: list[SourceChunk] = []

    for candidate in candidates:
        if not candidate.accepted:
            continue
        document = load_document_record(candidate.path)
        documents.append(document)
        chunks.extend(
            prepare_chunks(
                candidate.path,
                document.content,
                splitter_config,
                document.metadata,
            )
        )

    return DocumentPipelineResult(
        candidates=candidates,
        documents=tuple(documents),
        chunks=tuple(chunks),
        config=splitter_config,
    )
