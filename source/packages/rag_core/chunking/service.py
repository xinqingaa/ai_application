"""Public chunking service and built-in strategies."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, Sequence

from rag_core.chunking.identity import build_chunk_id
from rag_core.chunking.models import (
    Chunk,
    ChunkKind,
    ChunkPolicy,
    ChunkReport,
    ChunkResult,
    ChunkSourceSpan,
    ChunkStrategy,
)
from rag_core.chunking.tokenization import TokenCounter
from rag_core.ingestion.models import DocumentElement, ElementKind, KnowledgeDocument

_RESERVED_METADATA_KEYS = {
    "chunk_id",
    "document_id",
    "document_version",
    "original_filename",
    "file_format",
    "source_role",
    "evidence_eligibility",
    "policy_name",
    "policy_version",
    "policy_fingerprint",
    "parent_chunk_id",
}


@dataclass(frozen=True)
class _Piece:
    text: str
    source_spans: tuple[ChunkSourceSpan, ...]


def chunk_document(
    document: KnowledgeDocument,
    policy: ChunkPolicy,
) -> ChunkResult:
    """Turn one loaded document into traceable retrieval/context units."""
    _validate_document(document)
    counter = TokenCounter(policy.tokenizer)

    if policy.strategy is ChunkStrategy.ELEMENT:
        drafts = [
            (ChunkKind.STANDALONE, piece, None)
            for piece in _element_pieces(document.elements, counter, policy.max_tokens)
        ]
    elif policy.strategy is ChunkStrategy.FIXED_WINDOW:
        drafts = [
            (ChunkKind.STANDALONE, piece, None)
            for piece in _fixed_window_pieces(
                document.elements,
                counter,
                max_tokens=policy.max_tokens,
                overlap_tokens=policy.overlap_tokens,
            )
        ]
    elif policy.strategy is ChunkStrategy.STRUCTURE_AWARE:
        drafts = [
            (ChunkKind.STANDALONE, piece, None)
            for piece in _structure_pieces(
                document.elements,
                counter,
                max_tokens=policy.max_tokens,
            )
        ]
    elif policy.strategy is ChunkStrategy.PARENT_CHILD:
        drafts = _parent_child_drafts(document.elements, counter, policy)
    else:
        raise AssertionError(f"未处理的 Chunk strategy：{policy.strategy}")

    chunks = _materialize_chunks(document, policy, counter, drafts)
    if not chunks:
        raise ValueError("KnowledgeDocument 没有产生有效 Chunk")
    return ChunkResult(
        chunks=chunks,
        report=_build_report(document, policy, counter, chunks),
    )


def _validate_document(document: KnowledgeDocument) -> None:
    if not document.elements:
        raise ValueError("KnowledgeDocument.elements 不能为空")
    conflicts = sorted(_RESERVED_METADATA_KEYS.intersection(document.metadata))
    if conflicts:
        raise ValueError(f"业务 metadata 不能覆盖保留字段：{', '.join(conflicts)}")


def _element_pieces(
    elements: Sequence[DocumentElement],
    counter: TokenCounter,
    max_tokens: int,
) -> list[_Piece]:
    pieces: list[_Piece] = []
    for element in elements:
        pieces.extend(_split_element(element, counter, max_tokens))
    return pieces


def _fixed_window_pieces(
    elements: Sequence[DocumentElement],
    counter: TokenCounter,
    *,
    max_tokens: int,
    overlap_tokens: int,
) -> list[_Piece]:
    text, element_ranges = _document_buffer(elements)
    return [
        _piece_from_global_range(text, element_ranges, start, end)
        for start, end in counter.split_ranges(
            text,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )
    ]


def _structure_pieces(
    elements: Sequence[DocumentElement],
    counter: TokenCounter,
    *,
    max_tokens: int,
) -> list[_Piece]:
    sections = _section_groups(elements)
    pieces: list[_Piece] = []
    for section in sections:
        pieces.extend(_pack_elements(section, counter, max_tokens))
    return pieces


def _parent_child_drafts(
    elements: Sequence[DocumentElement],
    counter: TokenCounter,
    policy: ChunkPolicy,
) -> list[tuple[ChunkKind, _Piece, str | None]]:
    drafts: list[tuple[ChunkKind, _Piece, str | None]] = []
    parent_pieces: list[_Piece] = []
    for section in _section_groups(elements):
        parent_pieces.extend(_pack_elements(section, counter, policy.parent_max_tokens))

    for parent_piece in parent_pieces:
        parent_key = _draft_parent_key(parent_piece)
        drafts.append((ChunkKind.PARENT, parent_piece, parent_key))
        child_pieces = _split_piece(
            parent_piece,
            counter,
            max_tokens=policy.max_tokens,
            overlap_tokens=policy.overlap_tokens,
        )
        for child_piece in child_pieces:
            drafts.append((ChunkKind.CHILD, child_piece, parent_key))
    return drafts


def _section_groups(
    elements: Sequence[DocumentElement],
) -> list[list[DocumentElement]]:
    groups: list[list[DocumentElement]] = []
    current: list[DocumentElement] = []
    has_body = False
    for element in elements:
        if element.kind is ElementKind.TITLE and current and has_body:
            groups.append(current)
            current = []
            has_body = False
        current.append(element)
        if element.kind is not ElementKind.TITLE:
            has_body = True
    if current:
        if not has_body and groups:
            groups[-1].extend(current)
        else:
            groups.append(current)
    return groups


def _pack_elements(
    elements: Sequence[DocumentElement],
    counter: TokenCounter,
    max_tokens: int,
) -> list[_Piece]:
    title_prefix: list[DocumentElement] = []
    body: list[DocumentElement] = []
    for element in elements:
        if not body and element.kind is ElementKind.TITLE:
            title_prefix.append(element)
        else:
            body.append(element)
    if not body:
        return _piece_for_group(title_prefix, counter, max_tokens)

    pieces: list[_Piece] = []
    current_body: list[DocumentElement] = []
    for element in body:
        candidate = [*title_prefix, *current_body, element]
        if current_body and counter.count(_join_element_text(candidate)) > max_tokens:
            pieces.extend(
                _piece_for_group(
                    [*title_prefix, *current_body],
                    counter,
                    max_tokens,
                )
            )
            current_body = [element]
        else:
            current_body.append(element)
    if current_body:
        pieces.extend(
            _piece_for_group(
                [*title_prefix, *current_body],
                counter,
                max_tokens,
            )
        )
    return pieces


def _piece_for_group(
    elements: Sequence[DocumentElement],
    counter: TokenCounter,
    max_tokens: int,
) -> list[_Piece]:
    if len(elements) == 1:
        return _split_element(elements[0], counter, max_tokens)
    text, element_ranges = _document_buffer(elements)
    if counter.count(text) <= max_tokens:
        return [_piece_from_global_range(text, element_ranges, 0, len(text))]

    title_prefix = [item for item in elements if item.kind is ElementKind.TITLE]
    body = [item for item in elements if item.kind is not ElementKind.TITLE]
    if not body:
        return _fixed_window_pieces(
            elements,
            counter,
            max_tokens=max_tokens,
            overlap_tokens=0,
        )
    pieces: list[_Piece] = []
    for element in body:
        group = [*title_prefix, element]
        group_text, group_ranges = _document_buffer(group)
        if counter.count(group_text) <= max_tokens:
            pieces.append(
                _piece_from_global_range(group_text, group_ranges, 0, len(group_text))
            )
        else:
            pieces.extend(
                _fixed_window_pieces(
                    group,
                    counter,
                    max_tokens=max_tokens,
                    overlap_tokens=0,
                )
            )
    return pieces


def _split_element(
    element: DocumentElement,
    counter: TokenCounter,
    max_tokens: int,
) -> list[_Piece]:
    if counter.count(element.text) <= max_tokens:
        return [
            _Piece(
                text=element.text,
                source_spans=(
                    ChunkSourceSpan(
                        element_id=element.element_id,
                        locator=element.locator,
                        start_char=0,
                        end_char=len(element.text),
                        text=element.text,
                    ),
                ),
            )
        ]
    pieces: list[_Piece] = []
    for start, end in counter.split_ranges(element.text, max_tokens=max_tokens):
        pieces.append(
            _Piece(
                text=element.text[start:end],
                source_spans=(
                    ChunkSourceSpan(
                        element_id=element.element_id,
                        locator=element.locator,
                        start_char=start,
                        end_char=end,
                        text=element.text[start:end],
                    ),
                ),
            )
        )
    return pieces


def _split_piece(
    piece: _Piece,
    counter: TokenCounter,
    *,
    max_tokens: int,
    overlap_tokens: int,
) -> list[_Piece]:
    if counter.count(piece.text) <= max_tokens:
        return [piece]
    mapped_ranges = _piece_buffer_ranges(piece)
    return [
        _piece_from_global_range(piece.text, mapped_ranges, start, end)
        for start, end in counter.split_ranges(
            piece.text,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )
    ]


def _document_buffer(
    elements: Sequence[DocumentElement],
) -> tuple[str, list[tuple[int, int, DocumentElement, int]]]:
    parts: list[str] = []
    ranges: list[tuple[int, int, DocumentElement, int]] = []
    cursor = 0
    for index, element in enumerate(elements):
        if index:
            parts.append("\n\n")
            cursor += 2
        start = cursor
        parts.append(element.text)
        cursor += len(element.text)
        ranges.append((start, cursor, element, 0))
    return "".join(parts), ranges


def _piece_buffer_ranges(
    piece: _Piece,
) -> list[tuple[int, int, DocumentElement, int]]:
    ranges: list[tuple[int, int, DocumentElement, int]] = []
    cursor = 0
    for index, span in enumerate(piece.source_spans):
        if index:
            cursor += 2
        start = piece.text.find(span.text, cursor)
        if start < 0:
            continue
        end = start + len(span.text)
        element = DocumentElement(
            element_id=span.element_id,
            kind=ElementKind.PARAGRAPH,
            text=span.text,
            locator=span.locator,
            ordinal=index + 1,
        )
        ranges.append((start, end, element, span.start_char))
        cursor = end
    return ranges


def _piece_from_global_range(
    text: str,
    element_ranges: Sequence[tuple[int, int, DocumentElement, int]],
    start: int,
    end: int,
) -> _Piece:
    spans: list[ChunkSourceSpan] = []
    for element_start, element_end, element, base_offset in element_ranges:
        overlap_start = max(start, element_start)
        overlap_end = min(end, element_end)
        if overlap_end <= overlap_start:
            continue
        relative_start = base_offset + overlap_start - element_start
        relative_end = base_offset + overlap_end - element_start
        span_text = text[overlap_start:overlap_end]
        spans.append(
            ChunkSourceSpan(
                element_id=element.element_id,
                locator=element.locator,
                start_char=relative_start,
                end_char=relative_end,
                text=span_text,
            )
        )
    return _Piece(text=text[start:end], source_spans=tuple(spans))


def _join_element_text(elements: Iterable[DocumentElement]) -> str:
    return "\n\n".join(element.text for element in elements)


def _draft_parent_key(piece: _Piece) -> str:
    first = piece.source_spans[0]
    last = piece.source_spans[-1]
    return f"{first.element_id}:{first.start_char}-{last.element_id}:{last.end_char}"


def _materialize_chunks(
    document: KnowledgeDocument,
    policy: ChunkPolicy,
    counter: TokenCounter,
    drafts: Sequence[tuple[ChunkKind, _Piece, str | None]],
) -> tuple[Chunk, ...]:
    parent_ids: dict[str, str] = {}
    for kind, piece, parent_key in drafts:
        if kind is not ChunkKind.PARENT or parent_key is None:
            continue
        parent_ids[parent_key] = build_chunk_id(
            document_id=document.document_id,
            document_version=document.document_version,
            policy_fingerprint=policy.fingerprint,
            kind=kind,
            text=piece.text,
            source_spans=piece.source_spans,
        )

    chunks: list[Chunk] = []
    for ordinal, (kind, piece, parent_key) in enumerate(drafts, start=1):
        parent_chunk_id = (
            parent_ids[parent_key]
            if kind is ChunkKind.CHILD and parent_key is not None
            else None
        )
        chunk_id = build_chunk_id(
            document_id=document.document_id,
            document_version=document.document_version,
            policy_fingerprint=policy.fingerprint,
            kind=kind,
            text=piece.text,
            source_spans=piece.source_spans,
        )
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                kind=kind,
                document_id=document.document_id,
                document_version=document.document_version,
                original_filename=document.original_filename,
                file_format=document.file_format,
                source_role=document.source_role,
                evidence_eligibility=document.evidence_eligibility,
                text=piece.text,
                ordinal=ordinal,
                token_count=counter.count(piece.text),
                source_spans=piece.source_spans,
                policy_name=policy.name,
                policy_version=policy.version,
                policy_fingerprint=policy.fingerprint,
                parent_chunk_id=parent_chunk_id,
                business_metadata=dict(document.metadata),
            )
        )
    return tuple(chunks)


def _build_report(
    document: KnowledgeDocument,
    policy: ChunkPolicy,
    counter: TokenCounter,
    chunks: Sequence[Chunk],
) -> ChunkReport:
    token_counts = sorted(chunk.token_count for chunk in chunks)
    total_chunk_tokens = sum(token_counts)
    source_tokens = counter.count(document.text)
    repeated_tokens = max(0, total_chunk_tokens - source_tokens)
    return ChunkReport(
        document_id=document.document_id,
        document_version=document.document_version,
        policy_name=policy.name,
        policy_version=policy.version,
        policy_fingerprint=policy.fingerprint,
        strategy=policy.strategy,
        chunk_count=len(chunks),
        standalone_count=sum(chunk.kind is ChunkKind.STANDALONE for chunk in chunks),
        parent_count=sum(chunk.kind is ChunkKind.PARENT for chunk in chunks),
        child_count=sum(chunk.kind is ChunkKind.CHILD for chunk in chunks),
        source_span_count=sum(len(chunk.source_spans) for chunk in chunks),
        min_tokens=token_counts[0],
        median_tokens=token_counts[len(token_counts) // 2],
        p95_tokens=token_counts[max(0, ceil(len(token_counts) * 0.95) - 1)],
        max_tokens=token_counts[-1],
        total_chunk_tokens=total_chunk_tokens,
        source_tokens=source_tokens,
        repeated_tokens=repeated_tokens,
        repetition_ratio=(
            round(repeated_tokens / source_tokens, 4) if source_tokens else 0.0
        ),
    )
