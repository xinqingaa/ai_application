from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from rag_core import (
    ChunkKind,
    ChunkPolicy,
    ChunkStrategy,
    EvidenceEligibility,
    SourceRole,
    chunk_document,
    load_document,
)

FIXTURE_DIR = (
    Path(__file__).resolve().parents[4]
    / "review_assistant"
    / "fixtures"
    / "v0"
    / "ingestion"
)


def _document():
    return load_document(
        FIXTURE_DIR / "order_rules.md",
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        metadata={"knowledge_scope": "after_sale"},
    ).document


def _policy(
    strategy: ChunkStrategy,
    *,
    max_tokens: int = 24,
    overlap_tokens: int = 0,
    parent_max_tokens: int = 64,
) -> ChunkPolicy:
    return ChunkPolicy(
        name=strategy.value,
        version="1.0.0",
        strategy=strategy,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        parent_max_tokens=parent_max_tokens,
    )


def test_chunk_ids_are_stable_for_same_document_and_policy() -> None:
    document = _document()
    policy = _policy(ChunkStrategy.STRUCTURE_AWARE)

    first = chunk_document(document, policy)
    second = chunk_document(document, policy)

    assert [chunk.chunk_id for chunk in first.chunks] == [
        chunk.chunk_id for chunk in second.chunks
    ]


def test_document_or_effective_policy_change_changes_chunk_ids() -> None:
    document = _document()
    policy = _policy(ChunkStrategy.FIXED_WINDOW, overlap_tokens=4)
    original = chunk_document(document, policy)

    changed_version = chunk_document(
        replace(document, document_version="1.0.1"),
        policy,
    )
    changed_policy = chunk_document(
        document,
        replace(policy, overlap_tokens=5),
    )

    assert {chunk.chunk_id for chunk in original.chunks}.isdisjoint(
        chunk.chunk_id for chunk in changed_version.chunks
    )
    assert {chunk.chunk_id for chunk in original.chunks}.isdisjoint(
        chunk.chunk_id for chunk in changed_policy.chunks
    )


@pytest.mark.parametrize("strategy", list(ChunkStrategy))
def test_every_source_span_round_trips_to_document_element(
    strategy: ChunkStrategy,
) -> None:
    document = _document()
    result = chunk_document(
        document,
        _policy(
            strategy,
            overlap_tokens=4 if strategy is ChunkStrategy.FIXED_WINDOW else 0,
        ),
    )
    elements = {element.element_id: element for element in document.elements}

    assert result.chunks
    for chunk in result.chunks:
        assert chunk.text.strip()
        assert chunk.source_spans
        for span in chunk.source_spans:
            element = elements[span.element_id]
            assert element.text[span.start_char : span.end_char] == span.text


def test_structure_aware_chunks_keep_heading_with_body() -> None:
    result = chunk_document(
        _document(),
        _policy(ChunkStrategy.STRUCTURE_AWARE),
    )

    assert all(
        not all(
            span.locator.heading_path and span.text == span.locator.heading_path[-1]
            for span in chunk.source_spans
        )
        for chunk in result.chunks
    )
    virtual_goods = next(
        chunk for chunk in result.chunks if "Virtual goods" in chunk.text
    )
    assert "Current order-state rules" in virtual_goods.text


def test_parent_child_links_are_valid_and_source_ranges_are_contained() -> None:
    result = chunk_document(
        _document(),
        _policy(
            ChunkStrategy.PARENT_CHILD,
            max_tokens=24,
            overlap_tokens=4,
            parent_max_tokens=64,
        ),
    )
    parents = {
        chunk.chunk_id: chunk
        for chunk in result.chunks
        if chunk.kind is ChunkKind.PARENT
    }
    children = [chunk for chunk in result.chunks if chunk.kind is ChunkKind.CHILD]

    assert parents
    assert children
    for child in children:
        assert child.parent_chunk_id in parents
        parent = parents[child.parent_chunk_id]
        parent_ranges = {
            (
                span.element_id,
                span.start_char,
                span.end_char,
            )
            for span in parent.source_spans
        }
        for child_span in child.source_spans:
            assert any(
                child_span.element_id == element_id
                and start <= child_span.start_char
                and child_span.end_char <= end
                for element_id, start, end in parent_ranges
            )


def test_metadata_and_report_keep_separate_responsibilities() -> None:
    document = _document()
    result = chunk_document(
        document,
        _policy(ChunkStrategy.FIXED_WINDOW, overlap_tokens=4),
    )
    chunk = result.chunks[0]
    report = result.report

    assert chunk.document_id == document.document_id
    assert chunk.source_role is SourceRole.REFERENCE_KNOWLEDGE
    assert chunk.evidence_eligibility is EvidenceEligibility.CURRENT_EVIDENCE
    assert chunk.business_metadata == {"knowledge_scope": "after_sale"}
    assert "source_span_count" not in chunk.business_metadata
    assert report.source_span_count == sum(
        len(item.source_spans) for item in result.chunks
    )
    assert report.repeated_tokens > 0
    assert report.repetition_ratio > 0


def test_reserved_source_metadata_cannot_be_overridden() -> None:
    document = replace(_document(), metadata={"document_id": "OTHER"})

    with pytest.raises(ValueError, match="不能覆盖保留字段"):
        chunk_document(document, _policy(ChunkStrategy.ELEMENT))


@pytest.mark.parametrize(
    ("max_tokens", "overlap_tokens", "parent_max_tokens", "message"),
    [
        (0, 0, 64, "max_tokens"),
        (24, 24, 64, "overlap_tokens"),
        (64, 0, 24, "parent_max_tokens"),
    ],
)
def test_policy_rejects_invalid_ranges(
    max_tokens: int,
    overlap_tokens: int,
    parent_max_tokens: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _policy(
            (
                ChunkStrategy.PARENT_CHILD
                if message == "parent_max_tokens"
                else ChunkStrategy.FIXED_WINDOW
            ),
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            parent_max_tokens=parent_max_tokens,
        )
