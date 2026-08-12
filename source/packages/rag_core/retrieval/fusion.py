"""Rank-only fusion for independently scored retrieval routes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from rag_core.chunking.models import ChunkSourceSpan
from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.retrieval.models import DenseSearchResult, LexicalSearchResult


class RouteStatus(str, Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    FAILED = "failed"


@dataclass(frozen=True)
class RankedCandidate:
    chunk_id: str
    document_id: str
    document_version: str
    content: str
    source_role: SourceRole
    evidence_eligibility: EvidenceEligibility
    business_metadata: Mapping[str, str]
    route_rank: int
    native_score_name: str
    native_score: float
    higher_is_better: bool
    source_spans: tuple[ChunkSourceSpan, ...] = ()

    def __post_init__(self) -> None:
        if not self.chunk_id.strip():
            raise ValueError("RankedCandidate.chunk_id 不能为空")
        if self.route_rank <= 0:
            raise ValueError("RankedCandidate.route_rank 必须大于 0")
        if not self.native_score_name.strip():
            raise ValueError("RankedCandidate.native_score_name 不能为空")


@dataclass(frozen=True)
class RankedRoute:
    name: str
    status: RouteStatus
    candidates: tuple[RankedCandidate, ...] = ()
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("RankedRoute.name 不能为空")
        if self.status is RouteStatus.SUCCESS:
            if not self.candidates:
                raise ValueError("SUCCESS route 必须至少包含一个 candidate")
            if self.error_code or self.error_message:
                raise ValueError("SUCCESS route 不能携带 error")
        elif self.status is RouteStatus.EMPTY:
            if self.candidates:
                raise ValueError("EMPTY route 不能包含 candidate")
            if self.error_code or self.error_message:
                raise ValueError("EMPTY route 不能携带 error")
        else:
            if self.candidates:
                raise ValueError("FAILED route 不能包含 candidate")
            if not self.error_code or not self.error_message:
                raise ValueError("FAILED route 必须携带 error_code 和 error_message")

        ranks = [candidate.route_rank for candidate in self.candidates]
        if ranks and sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise ValueError("每路 route_rank 必须从 1 开始且连续")
        chunk_ids = [candidate.chunk_id for candidate in self.candidates]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("同一路由内不能出现重复 chunk_id")


@dataclass(frozen=True)
class RRFContribution:
    route_name: str
    route_rank: int
    reciprocal_rank: float
    native_score_name: str
    native_score: float
    higher_is_better: bool


@dataclass(frozen=True)
class RRFCandidate:
    chunk_id: str
    document_id: str
    document_version: str
    content: str
    source_role: SourceRole
    evidence_eligibility: EvidenceEligibility
    business_metadata: Mapping[str, str]
    contributions: tuple[RRFContribution, ...]
    rrf_score: float
    fusion_rank: int
    source_spans: tuple[ChunkSourceSpan, ...] = ()

    @property
    def matched_routes(self) -> tuple[str, ...]:
        return tuple(item.route_name for item in self.contributions)


@dataclass(frozen=True)
class RRFDiagnostics:
    rrf_k: int
    fusion_config_ref: str
    route_statuses: Mapping[str, RouteStatus]
    route_candidate_counts: Mapping[str, int]
    distinct_candidate_count: int
    overlap_candidate_count: int
    failed_routes: tuple[str, ...]


@dataclass(frozen=True)
class RRFResult:
    candidates: tuple[RRFCandidate, ...]
    diagnostics: RRFDiagnostics


def lexical_ranked_route(result: LexicalSearchResult) -> RankedRoute:
    candidates = tuple(
        RankedCandidate(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            document_version=hit.document_version,
            content=hit.content,
            source_role=hit.source_role,
            evidence_eligibility=hit.evidence_eligibility,
            business_metadata=hit.business_metadata,
            route_rank=hit.route_rank,
            native_score_name="postgresql_ts_rank",
            native_score=hit.fts_rank,
            higher_is_better=True,
            source_spans=hit.source_spans,
        )
        for hit in result.hits
    )
    return RankedRoute(
        name="lexical",
        status=RouteStatus.SUCCESS if candidates else RouteStatus.EMPTY,
        candidates=candidates,
    )


def dense_ranked_route(result: DenseSearchResult) -> RankedRoute:
    candidates = tuple(
        RankedCandidate(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            document_version=hit.document_version,
            content=hit.content,
            source_role=hit.source_role,
            evidence_eligibility=hit.evidence_eligibility,
            business_metadata=hit.business_metadata,
            route_rank=hit.route_rank,
            native_score_name="pgvector_cosine_distance",
            native_score=hit.cosine_distance,
            higher_is_better=False,
            source_spans=hit.source_spans,
        )
        for hit in result.hits
    )
    return RankedRoute(
        name="dense",
        status=RouteStatus.SUCCESS if candidates else RouteStatus.EMPTY,
        candidates=candidates,
    )


def failed_ranked_route(
    name: str,
    *,
    error_code: str,
    error_message: str,
) -> RankedRoute:
    return RankedRoute(
        name=name,
        status=RouteStatus.FAILED,
        error_code=error_code,
        error_message=error_message,
    )


def reciprocal_rank_fusion(
    routes: Sequence[RankedRoute],
    *,
    rrf_k: int = 60,
) -> RRFResult:
    if len(routes) < 2:
        raise ValueError("RRF 至少需要两条检索路由")
    if rrf_k <= 0:
        raise ValueError("rrf_k 必须大于 0")
    route_names = [route.name for route in routes]
    if len(route_names) != len(set(route_names)):
        raise ValueError("RRF route name 不能重复")

    aggregated: dict[str, dict[str, object]] = {}
    for route in routes:
        for candidate in route.candidates:
            contribution = RRFContribution(
                route_name=route.name,
                route_rank=candidate.route_rank,
                reciprocal_rank=1.0 / (rrf_k + candidate.route_rank),
                native_score_name=candidate.native_score_name,
                native_score=candidate.native_score,
                higher_is_better=candidate.higher_is_better,
            )
            current = aggregated.get(candidate.chunk_id)
            if current is None:
                aggregated[candidate.chunk_id] = {
                    "candidate": candidate,
                    "contributions": [contribution],
                }
                continue
            _validate_same_chunk(current["candidate"], candidate)
            current["contributions"].append(contribution)

    provisional: list[tuple[RankedCandidate, tuple[RRFContribution, ...], float]] = []
    for item in aggregated.values():
        candidate = item["candidate"]
        contributions = tuple(
            sorted(item["contributions"], key=lambda value: value.route_name)
        )
        provisional.append(
            (
                candidate,
                contributions,
                sum(value.reciprocal_rank for value in contributions),
            )
        )
    provisional.sort(
        key=lambda item: (
            -item[2],
            -len(item[1]),
            min(value.route_rank for value in item[1]),
            item[0].chunk_id,
        )
    )
    fused = tuple(
        RRFCandidate(
            chunk_id=candidate.chunk_id,
            document_id=candidate.document_id,
            document_version=candidate.document_version,
            content=candidate.content,
            source_role=candidate.source_role,
            evidence_eligibility=candidate.evidence_eligibility,
            business_metadata=candidate.business_metadata,
            contributions=contributions,
            rrf_score=score,
            fusion_rank=index + 1,
            source_spans=candidate.source_spans,
        )
        for index, (candidate, contributions, score) in enumerate(provisional)
    )
    overlap = sum(1 for item in fused if len(item.contributions) > 1)
    route_statuses = {route.name: route.status for route in routes}
    route_counts = {route.name: len(route.candidates) for route in routes}
    return RRFResult(
        candidates=fused,
        diagnostics=RRFDiagnostics(
            rrf_k=rrf_k,
            fusion_config_ref=_fusion_config_ref(rrf_k, route_names),
            route_statuses=route_statuses,
            route_candidate_counts=route_counts,
            distinct_candidate_count=len(fused),
            overlap_candidate_count=overlap,
            failed_routes=tuple(
                route.name for route in routes if route.status is RouteStatus.FAILED
            ),
        ),
    )


def _validate_same_chunk(left: object, right: RankedCandidate) -> None:
    if not isinstance(left, RankedCandidate):
        raise TypeError("RRF internal candidate type error")
    identity = (
        "document_id",
        "document_version",
        "content",
        "source_role",
        "evidence_eligibility",
        "source_spans",
    )
    if any(getattr(left, field) != getattr(right, field) for field in identity):
        raise ValueError(f"同一 chunk_id 在不同路由中的来源内容不一致：{left.chunk_id}")
    if dict(left.business_metadata) != dict(right.business_metadata):
        raise ValueError(
            f"同一 chunk_id 在不同路由中的 business_metadata 不一致：{left.chunk_id}"
        )


def _fusion_config_ref(rrf_k: int, route_names: Sequence[str]) -> str:
    payload = {
        "algorithm": "reciprocal_rank_fusion",
        "version": "1.0.0",
        "rrf_k": rrf_k,
        "routes": sorted(route_names),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    fingerprint = hashlib.sha256(encoded).hexdigest()[:16]
    return f"rrf@1.0.0:{fingerprint}"
