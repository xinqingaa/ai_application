"""Adapt traceable retrieval candidates to the shared Context Builder."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from llm_core.context import (
    BuiltContext,
    ContextBuildPolicy,
    ContextSource,
    ContextSourceType,
    build_review_context,
)
from rag_core.ingestion.models import EvidenceEligibility
from rag_core.retrieval.hybrid import RetrievalResult


class ContextMappingStatus(str, Enum):
    MAPPED = "mapped"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class RetrievalContextDecision:
    chunk_id: str
    source_id: str
    fusion_rank: int
    source_type: ContextSourceType
    status: ContextMappingStatus
    reason: str
    source_locators: tuple[str, ...]
    route_ranks: tuple[tuple[str, int], ...]
    native_scores: tuple[tuple[str, str, float, bool], ...]


@dataclass(frozen=True)
class RetrievalContextMapping:
    sources: tuple[ContextSource, ...]
    decisions: tuple[RetrievalContextDecision, ...]

    @property
    def mapped_source_ids(self) -> tuple[str, ...]:
        return tuple(source.source_id for source in self.sources)


@dataclass(frozen=True)
class RAGContextBuildResult:
    mapping: RetrievalContextMapping
    context: BuiltContext


def retrieval_result_to_context_sources(
    result: RetrievalResult,
) -> RetrievalContextMapping:
    """Preserve retrieval identity and provenance without inventing authority scores."""

    sources: list[ContextSource] = []
    decisions: list[RetrievalContextDecision] = []
    for candidate in result.candidates:
        locators = tuple(
            dict.fromkeys(span.locator.describe() for span in candidate.source_spans)
        )
        if not locators:
            raise ValueError(
                f"检索候选缺少 source_spans，不能进入可追踪上下文：{candidate.chunk_id}"
            )
        source_type, status, reason = _mapping_outcome(candidate.evidence_eligibility)
        route_ranks = tuple(
            (item.route_name, item.route_rank) for item in candidate.contributions
        )
        native_scores = tuple(
            (
                item.route_name,
                item.native_score_name,
                item.native_score,
                item.higher_is_better,
            )
            for item in candidate.contributions
        )
        decisions.append(
            RetrievalContextDecision(
                chunk_id=candidate.chunk_id,
                source_id=candidate.chunk_id,
                fusion_rank=candidate.fusion_rank,
                source_type=source_type,
                status=status,
                reason=reason,
                source_locators=locators,
                route_ranks=route_ranks,
                native_scores=native_scores,
            )
        )
        if status is ContextMappingStatus.EXCLUDED:
            continue

        sources.append(
            ContextSource(
                source_id=candidate.chunk_id,
                content=candidate.content,
                source_type=source_type,
                title=(
                    f"{candidate.document_id}@{candidate.document_version}"
                    f" · {locators[0]}"
                ),
                # Preserve the fused order for budget selection. This is not a
                # source-authority or factual-confidence score.
                priority=max(1, 1000 - candidate.fusion_rank),
                score=None,
                metadata={
                    "chunk_id": candidate.chunk_id,
                    "document_id": candidate.document_id,
                    "document_version": candidate.document_version,
                    "source_role": candidate.source_role.value,
                    "evidence_eligibility": candidate.evidence_eligibility.value,
                    "source_locators": " | ".join(locators),
                    "fusion_rank": str(candidate.fusion_rank),
                    "rrf_score": f"{candidate.rrf_score:.8f}",
                    "route_ranks": _route_rank_text(route_ranks),
                    "native_scores": _native_score_text(native_scores),
                    "retriever_config_ref": result.report.retriever_config_ref,
                },
            )
        )
    return RetrievalContextMapping(
        sources=tuple(sources),
        decisions=tuple(decisions),
    )


def build_rag_review_context(
    *,
    requirement_text: str,
    retrieval_result: RetrievalResult,
    policy: ContextBuildPolicy,
    additional_sources: Sequence[ContextSource] = (),
) -> RAGContextBuildResult:
    """Map retrieval output, then delegate all selection to llm_core.context."""

    mapping = retrieval_result_to_context_sources(retrieval_result)
    retrieval_ids = set(mapping.mapped_source_ids)
    collisions = sorted(
        source.source_id
        for source in additional_sources
        if source.source_id in retrieval_ids
    )
    if collisions:
        raise ValueError(
            "additional_sources 与检索 Chunk 的 source_id 冲突："
            + ", ".join(collisions)
        )
    context = build_review_context(
        requirement_text=requirement_text,
        sources=(*mapping.sources, *additional_sources),
        policy=policy,
    )
    return RAGContextBuildResult(mapping=mapping, context=context)


def _mapping_outcome(
    eligibility: EvidenceEligibility,
) -> tuple[ContextSourceType, ContextMappingStatus, str]:
    if eligibility is EvidenceEligibility.CURRENT_EVIDENCE:
        return "evidence", ContextMappingStatus.MAPPED, "mapped_as_current_evidence"
    if eligibility is EvidenceEligibility.HISTORICAL_CONTEXT:
        return "history_review", ContextMappingStatus.MAPPED, "mapped_as_history"
    return "other", ContextMappingStatus.EXCLUDED, "excluded_ineligible_source"


def _route_rank_text(values: tuple[tuple[str, int], ...]) -> str:
    return ",".join(f"{route}:{rank}" for route, rank in values)


def _native_score_text(
    values: tuple[tuple[str, str, float, bool], ...],
) -> str:
    return ";".join(
        f"{route}.{name}={value:.8f}({('higher' if higher else 'lower')})"
        for route, name, value, higher in values
    )
