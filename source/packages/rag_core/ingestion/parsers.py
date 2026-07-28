"""Format-specific parsers that preserve native source locations."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from docx import Document as open_docx
from docx.table import Table
from docx.text.paragraph import Paragraph
from markdown_it import MarkdownIt
from pypdf import PdfReader

from rag_core.ingestion.errors import IngestionError, IngestionErrorCode, IngestionStage
from rag_core.ingestion.models import (
    ElementKind,
    FileArtifact,
    FileFormat,
    LoadWarning,
    LoaderConfig,
    SourceLocator,
)


@dataclass(frozen=True)
class ParsedElement:
    kind: ElementKind
    text: str
    locator: SourceLocator


@dataclass(frozen=True)
class ParseOutput:
    elements: tuple[ParsedElement, ...]
    warnings: tuple[LoadWarning, ...] = ()


def parse_artifact(
    artifact: FileArtifact,
    file_format: FileFormat,
    config: LoaderConfig,
) -> ParseOutput:
    try:
        if file_format is FileFormat.TXT:
            return _parse_txt(artifact, config)
        if file_format is FileFormat.MARKDOWN:
            return _parse_markdown(artifact, config)
        if file_format is FileFormat.DOCX:
            return _parse_docx(artifact)
        if file_format is FileFormat.PDF:
            return _parse_pdf(artifact)
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(
            code=IngestionErrorCode.DOCUMENT_PARSE_FAILED,
            stage=IngestionStage.PARSE,
            message=f"{file_format.value} 解析失败：{exc}",
            filename=artifact.filename,
            raw=exc,
        ) from exc
    raise AssertionError(f"未处理的文件格式：{file_format}")


def _decode_text(artifact: FileArtifact, config: LoaderConfig) -> str:
    try:
        return artifact.content.decode(config.text_encoding)
    except UnicodeDecodeError as exc:
        raise IngestionError(
            code=IngestionErrorCode.TEXT_DECODE_FAILED,
            stage=IngestionStage.PARSE,
            message=f"无法按 {config.text_encoding} 解码；请显式转换编码或设置 LoaderConfig",
            filename=artifact.filename,
            raw=exc,
        ) from exc


def _parse_txt(artifact: FileArtifact, config: LoaderConfig) -> ParseOutput:
    text = _decode_text(artifact, config)
    lines = text.splitlines()
    elements: list[ParsedElement] = []
    block: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        if not block:
            return
        elements.append(
            ParsedElement(
                kind=ElementKind.PARAGRAPH,
                text="\n".join(block),
                locator=SourceLocator(
                    kind="text_lines",
                    line_start=start_line,
                    line_end=end_line,
                ),
            )
        )
        block.clear()

    for index, line in enumerate(lines, start=1):
        if line.strip():
            if not block:
                start_line = index
            block.append(line)
        else:
            flush(index - 1)
    flush(len(lines))
    return ParseOutput(elements=tuple(elements))


def _parse_markdown(artifact: FileArtifact, config: LoaderConfig) -> ParseOutput:
    text = _decode_text(artifact, config)
    tokens = MarkdownIt("commonmark").parse(text)
    elements: list[ParsedElement] = []
    headings: list[str] = []
    list_depth = 0
    index = 0

    while index < len(tokens):
        token = tokens[index]
        if token.type == "list_item_open":
            list_depth += 1
        elif token.type == "list_item_close":
            list_depth = max(0, list_depth - 1)
        elif token.type == "heading_open" and index + 1 < len(tokens):
            inline = tokens[index + 1]
            level = int(token.tag[1:])
            title = inline.content.strip()
            headings = headings[: level - 1]
            headings.append(title)
            elements.append(
                ParsedElement(
                    kind=ElementKind.TITLE,
                    text=title,
                    locator=_markdown_locator(token.map, tuple(headings)),
                )
            )
        elif token.type == "paragraph_open" and index + 1 < len(tokens):
            inline = tokens[index + 1]
            elements.append(
                ParsedElement(
                    kind=ElementKind.LIST_ITEM if list_depth else ElementKind.PARAGRAPH,
                    text=inline.content,
                    locator=_markdown_locator(token.map, tuple(headings)),
                )
            )
        elif token.type in {"fence", "code_block"}:
            elements.append(
                ParsedElement(
                    kind=ElementKind.CODE,
                    text=token.content,
                    locator=_markdown_locator(token.map, tuple(headings)),
                )
            )
        index += 1

    return ParseOutput(elements=tuple(elements))


def _markdown_locator(
    line_map: list[int] | None,
    heading_path: tuple[str, ...],
) -> SourceLocator:
    if line_map is None:
        return SourceLocator(kind="markdown_block", heading_path=heading_path)
    start, end_exclusive = line_map
    return SourceLocator(
        kind="markdown_block",
        line_start=start + 1,
        line_end=max(start + 1, end_exclusive),
        heading_path=heading_path,
    )


def _parse_docx(artifact: FileArtifact) -> ParseOutput:
    document = open_docx(BytesIO(artifact.content))
    elements: list[ParsedElement] = []
    headings: list[str] = []
    paragraph_index = 0
    table_index = 0

    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            paragraph_index += 1
            text = block.text
            if not text.strip():
                continue
            heading_level = _docx_heading_level(block)
            kind = ElementKind.PARAGRAPH
            if heading_level is not None:
                headings = headings[: heading_level - 1]
                headings.append(text.strip())
                kind = ElementKind.TITLE
            elements.append(
                ParsedElement(
                    kind=kind,
                    text=text,
                    locator=SourceLocator(
                        kind="docx_paragraph",
                        paragraph_index=paragraph_index,
                        heading_path=tuple(headings),
                    ),
                )
            )
        elif isinstance(block, Table):
            table_index += 1
            rows = [" | ".join(cell.text for cell in row.cells) for row in block.rows]
            elements.append(
                ParsedElement(
                    kind=ElementKind.TABLE,
                    text="\n".join(rows),
                    locator=SourceLocator(
                        kind="docx_table",
                        table_index=table_index,
                        heading_path=tuple(headings),
                    ),
                )
            )

    return ParseOutput(elements=tuple(elements))


def _docx_heading_level(paragraph: Paragraph) -> int | None:
    style_name = paragraph.style.name if paragraph.style is not None else ""
    if not style_name.startswith("Heading "):
        return None
    try:
        return max(1, min(9, int(style_name.removeprefix("Heading "))))
    except ValueError:
        return None


def _parse_pdf(artifact: FileArtifact) -> ParseOutput:
    reader = PdfReader(BytesIO(artifact.content))
    if reader.is_encrypted:
        try:
            unlocked = reader.decrypt("")
        except Exception as exc:
            raise IngestionError(
                code=IngestionErrorCode.ENCRYPTED_PDF,
                stage=IngestionStage.PARSE,
                message="PDF 已加密，当前 Loader 无法读取",
                filename=artifact.filename,
                raw=exc,
            ) from exc
        if not unlocked:
            raise IngestionError(
                code=IngestionErrorCode.ENCRYPTED_PDF,
                stage=IngestionStage.PARSE,
                message="PDF 已加密，当前 Loader 无法读取",
                filename=artifact.filename,
            )

    elements: list[ParsedElement] = []
    warnings: list[LoadWarning] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        locator = SourceLocator(kind="pdf_page", page_number=page_number)
        if not page_text.strip():
            warnings.append(
                LoadWarning(
                    code="pdf_page_without_text",
                    message="该页没有可提取文本；可能为空页、图片页或扫描页",
                    locator=locator,
                )
            )
            continue
        elements.append(ParsedElement(kind=ElementKind.PAGE, text=page_text, locator=locator))

    if not elements:
        raise IngestionError(
            code=IngestionErrorCode.PDF_TEXT_LAYER_MISSING,
            stage=IngestionStage.EMPTY_CONTENT,
            message="PDF 没有可提取文本层；V0 不会静默调用 OCR/VLM",
            filename=artifact.filename,
        )

    warnings.append(
        LoadWarning(
            code="pdf_reading_order_not_guaranteed",
            message="文本按 PDF 内容流提取；复杂分栏、表格和浮动元素的阅读顺序需要人工核对",
        )
    )
    return ParseOutput(elements=tuple(elements), warnings=tuple(warnings))
