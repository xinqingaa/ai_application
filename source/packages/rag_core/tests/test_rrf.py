from __future__ import annotations

import pytest

from rag_core import (
    EvidenceEligibility,
    RankedCandidate,
    RankedRoute,
    RouteStatus,
    SourceRole,
    failed_ranked_route,
    reciprocal_rank_fusion,
)


def _candidate(
    chunk_id: str,
    rank: int,
    *,
    score_name: str,
    score: float,
    higher_is_better: bool,
) -> RankedCandidate:
    return RankedCandidate(
        chunk_id=chunk_id,
        document_id="doc-order",
        document_version="1.0.0",
        content=f"content for {chunk_id}",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        business_metadata={"knowledge_scope": "after_sale"},
        route_rank=rank,
        native_score_name=score_name,
        native_score=score,
        higher_is_better=higher_is_better,
    )


def test_rrf_uses_ranks_and_rewards_cross_route_overlap() -> None:
    lexical = RankedRoute(
        name="lexical",
        status=RouteStatus.SUCCESS,
        candidates=(
            _candidate(
                "exact-field",
                1,
                score_name="postgresql_ts_rank",
                score=0.91,
                higher_is_better=True,
            ),
            _candidate(
                "shared-rule",
                2,
                score_name="postgresql_ts_rank",
                score=0.37,
                higher_is_better=True,
            ),
        ),
    )
    dense = RankedRoute(
        name="dense",
        status=RouteStatus.SUCCESS,
        candidates=(
            _candidate(
                "semantic-only",
                1,
                score_name="pgvector_cosine_distance",
                score=0.08,
                higher_is_better=False,
            ),
            _candidate(
                "shared-rule",
                2,
                score_name="pgvector_cosine_distance",
                score=0.14,
                higher_is_better=False,
            ),
        ),
    )

    result = reciprocal_rank_fusion((lexical, dense), rrf_k=60)

    assert result.candidates[0].chunk_id == "shared-rule"
    assert result.candidates[0].rrf_score == pytest.approx(2 / 62)
    assert result.candidates[0].matched_routes == ("dense", "lexical")
    assert result.diagnostics.overlap_candidate_count == 1
    assert result.diagnostics.distinct_candidate_count == 3


def test_rrf_preserves_empty_and_failed_route_as_different_statuses() -> None:
    lexical = RankedRoute(name="lexical", status=RouteStatus.EMPTY)
    dense = failed_ranked_route(
        "dense",
        error_code="embedding_timeout",
        error_message="Embedding service timed out",
    )

    result = reciprocal_rank_fusion((lexical, dense), rrf_k=20)

    assert result.candidates == ()
    assert result.diagnostics.route_statuses["lexical"] is RouteStatus.EMPTY
    assert result.diagnostics.route_statuses["dense"] is RouteStatus.FAILED
    assert result.diagnostics.failed_routes == ("dense",)


def test_rrf_rejects_duplicate_chunk_within_one_route() -> None:
    duplicate = _candidate(
        "same",
        1,
        score_name="postgresql_ts_rank",
        score=0.5,
        higher_is_better=True,
    )
    second = _candidate(
        "same",
        2,
        score_name="postgresql_ts_rank",
        score=0.4,
        higher_is_better=True,
    )

    with pytest.raises(ValueError, match="重复 chunk_id"):
        RankedRoute(
            name="lexical",
            status=RouteStatus.SUCCESS,
            candidates=(duplicate, second),
        )


def test_rrf_rejects_inconsistent_chunk_content_across_routes() -> None:
    left = _candidate(
        "same",
        1,
        score_name="postgresql_ts_rank",
        score=0.5,
        higher_is_better=True,
    )
    right = RankedCandidate(
        chunk_id="same",
        document_id=left.document_id,
        document_version=left.document_version,
        content="different content",
        source_role=left.source_role,
        evidence_eligibility=left.evidence_eligibility,
        business_metadata=left.business_metadata,
        route_rank=1,
        native_score_name="pgvector_cosine_distance",
        native_score=0.1,
        higher_is_better=False,
    )

    with pytest.raises(ValueError, match="来源内容不一致"):
        reciprocal_rank_fusion(
            (
                RankedRoute(
                    name="lexical",
                    status=RouteStatus.SUCCESS,
                    candidates=(left,),
                ),
                RankedRoute(
                    name="dense",
                    status=RouteStatus.SUCCESS,
                    candidates=(right,),
                ),
            )
        )
