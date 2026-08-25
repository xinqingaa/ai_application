"""Fixed lexical + dense + RRF retrieval control and diagnostics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from collections.abc import Callable
from typing import Mapping

from rag_core.embedding.models import EmbeddingRecord
from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.retrieval.errors import RetrievalError
from rag_core.retrieval.fusion import (
    RRFCandidate,
    RRFDiagnostics,
    RankedRoute,
    RouteStatus,
    dense_ranked_route,
    failed_ranked_route,
    lexical_ranked_route,
    reciprocal_rank_fusion,
)
from rag_core.retrieval.postgres_dense import PostgresDenseRetriever
from rag_core.retrieval.postgres_fts import PostgresFTSRetriever


@dataclass(frozen=True)
class HybridRetrieverConfig:
    lexical_candidate_k: int = 5
    dense_candidate_k: int = 5
    lexical_min_rank: float | None = None
    dense_max_distance: float | None = None
    rrf_k: int = 60
    final_top_k: int = 5
    knowledge_scope: str | None = None
    source_roles: tuple[SourceRole, ...] = ()
    evidence_eligibilities: tuple[EvidenceEligibility, ...] = ()

    def __post_init__(self) -> None:
        if self.lexical_candidate_k <= 0 or self.dense_candidate_k <= 0:
            raise ValueError("每路 candidate_k 必须大于 0")
        if self.rrf_k <= 0:
            raise ValueError("rrf_k 必须大于 0")
        if self.final_top_k <= 0:
            raise ValueError("final_top_k 必须大于 0")
        if self.lexical_min_rank is not None and self.lexical_min_rank < 0:
            raise ValueError("lexical_min_rank 不能小于 0")
        if self.dense_max_distance is not None and not (
            0 <= self.dense_max_distance <= 2
        ):
            raise ValueError("dense_max_distance 必须位于 [0, 2]")
        if self.knowledge_scope is not None and not self.knowledge_scope.strip():
            raise ValueError("knowledge_scope 不能是空字符串")

    @property
    def config_ref(self) -> str:
        payload = {
            "version": "1.0.0",
            "lexical_candidate_k": self.lexical_candidate_k,
            "dense_candidate_k": self.dense_candidate_k,
            "lexical_min_rank": self.lexical_min_rank,
            "dense_max_distance": self.dense_max_distance,
            "rrf_k": self.rrf_k,
            "final_top_k": self.final_top_k,
            "knowledge_scope": self.knowledge_scope,
            "source_roles": sorted(item.value for item in self.source_roles),
            "evidence_eligibilities": sorted(
                item.value for item in self.evidence_eligibilities
            ),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        fingerprint = hashlib.sha256(encoded).hexdigest()[:16]
        return f"fixed-hybrid-retriever@1.0.0:{fingerprint}"


class ThresholdStatus(str, Enum):
    PASSED = "passed"
    DROPPED = "dropped"


@dataclass(frozen=True)
class ThresholdDecision:
    route_name: str
    chunk_id: str
    route_rank: int
    native_score_name: str
    native_score: float
    higher_is_better: bool
    threshold_name: str | None
    threshold_value: float | None
    status: ThresholdStatus
    reason: str


@dataclass(frozen=True)
class FinalSelectionDecision:
    chunk_id: str
    fusion_rank: int
    rrf_score: float
    selected: bool
    reason: str


@dataclass(frozen=True)
class RouteControlReport:
    route_name: str
    execution_status: RouteStatus
    post_threshold_status: RouteStatus
    indexed_chunk_count: int | None
    visible_chunk_count: int | None
    matched_chunk_count: int | None
    candidate_count: int
    passed_threshold_count: int
    dropped_threshold_count: int
    native_score_name: str
    higher_is_better: bool
    threshold_name: str | None
    threshold_value: float | None
    latency_ms: float | None
    error_code: str | None = None
    error_message: str | None = None


class NoResultReason(str, Enum):
    VISIBLE_SCOPE_EMPTY = "visible_scope_empty"
    NO_ROUTE_MATCH = "no_route_match"
    ALL_BELOW_THRESHOLD = "all_below_threshold"
    ROUTE_FAILURE = "route_failure"
    ALL_ROUTES_FAILED = "all_routes_failed"


@dataclass(frozen=True)
class RetrievalReport:
    query: str
    retriever_config_ref: str
    control_order: tuple[str, ...]
    route_reports: Mapping[str, RouteControlReport]
    threshold_decisions: tuple[ThresholdDecision, ...]
    fusion_diagnostics: RRFDiagnostics
    final_selection: tuple[FinalSelectionDecision, ...]
    no_result_reason: NoResultReason | None
    partial_failure: bool
    latency_ms: float


@dataclass(frozen=True)
class RetrievalResult:
    candidates: tuple[RRFCandidate, ...]
    report: RetrievalReport


class FixedHybridRetriever:
    """Execute the first-stage pre-filter → routes → thresholds → RRF → final top-k contract."""

    def __init__(
        self,
        lexical: PostgresFTSRetriever,
        dense: PostgresDenseRetriever,
    ) -> None:
        self.lexical = lexical
        self.dense = dense

    def retrieve(
        self,
        query: str,
        query_embedding: EmbeddingRecord,
        *,
        config: HybridRetrieverConfig,
    ) -> RetrievalResult:
        if not query.strip():
            raise ValueError("query 不能为空")
        if query_embedding.text != query:
            raise ValueError("query_embedding.text 必须与 query 一致")
        started = perf_counter()

        lexical_result, lexical_route = self._run_lexical(query, config)
        dense_result, dense_route = self._run_dense(query_embedding, config)
        filtered_lexical, lexical_decisions = _apply_threshold(
            lexical_route,
            threshold_name="lexical_min_fts_rank",
            threshold_value=config.lexical_min_rank,
            keep_when=lambda value, threshold: value >= threshold,
        )
        filtered_dense, dense_decisions = _apply_threshold(
            dense_route,
            threshold_name="dense_max_cosine_distance",
            threshold_value=config.dense_max_distance,
            keep_when=lambda value, threshold: value <= threshold,
        )
        fused = reciprocal_rank_fusion(
            (filtered_lexical, filtered_dense),
            rrf_k=config.rrf_k,
        )
        selected = fused.candidates[: config.final_top_k]
        final_decisions = tuple(
            FinalSelectionDecision(
                chunk_id=candidate.chunk_id,
                fusion_rank=candidate.fusion_rank,
                rrf_score=candidate.rrf_score,
                selected=candidate.fusion_rank <= config.final_top_k,
                reason=(
                    "selected_by_final_top_k"
                    if candidate.fusion_rank <= config.final_top_k
                    else "dropped_by_final_top_k"
                ),
            )
            for candidate in fused.candidates
        )
        threshold_decisions = lexical_decisions + dense_decisions
        route_reports = {
            "lexical": _lexical_report(
                lexical_result,
                lexical_route,
                filtered_lexical,
                lexical_decisions,
                config,
            ),
            "dense": _dense_report(
                dense_result,
                dense_route,
                filtered_dense,
                dense_decisions,
                config,
            ),
        }
        no_result_reason = _no_result_reason(
            selected,
            route_reports,
            fused.diagnostics.failed_routes,
        )
        return RetrievalResult(
            candidates=selected,
            report=RetrievalReport(
                query=query,
                retriever_config_ref=config.config_ref,
                control_order=(
                    "pre_filter",
                    "route_candidate_k",
                    "route_threshold",
                    "rrf",
                    "final_top_k",
                ),
                route_reports=route_reports,
                threshold_decisions=threshold_decisions,
                fusion_diagnostics=fused.diagnostics,
                final_selection=final_decisions,
                no_result_reason=no_result_reason,
                partial_failure=bool(fused.diagnostics.failed_routes),
                latency_ms=(perf_counter() - started) * 1000,
            ),
        )

    def _run_lexical(self, query, config):
        try:
            result = self.lexical.search(
                query,
                candidate_k=config.lexical_candidate_k,
                knowledge_scope=config.knowledge_scope,
                source_roles=config.source_roles,
                evidence_eligibilities=config.evidence_eligibilities,
            )
            return result, lexical_ranked_route(result)
        except RetrievalError as exc:
            return None, failed_ranked_route(
                "lexical",
                error_code=exc.code.value,
                error_message=exc.message,
            )

    def _run_dense(self, query_embedding, config):
        try:
            result = self.dense.search(
                query_embedding,
                candidate_k=config.dense_candidate_k,
                knowledge_scope=config.knowledge_scope,
                source_roles=config.source_roles,
                evidence_eligibilities=config.evidence_eligibilities,
            )
            return result, dense_ranked_route(result)
        except RetrievalError as exc:
            return None, failed_ranked_route(
                "dense",
                error_code=exc.code.value,
                error_message=exc.message,
            )


def _apply_threshold(
    route: RankedRoute,
    *,
    threshold_name: str,
    threshold_value: float | None,
    keep_when: Callable[[float, float], bool],
) -> tuple[RankedRoute, tuple[ThresholdDecision, ...]]:
    if route.status is RouteStatus.FAILED:
        return route, ()
    kept = []
    decisions = []
    for candidate in route.candidates:
        passed = threshold_value is None or keep_when(
            candidate.native_score, threshold_value
        )
        decisions.append(
            ThresholdDecision(
                route_name=route.name,
                chunk_id=candidate.chunk_id,
                route_rank=candidate.route_rank,
                native_score_name=candidate.native_score_name,
                native_score=candidate.native_score,
                higher_is_better=candidate.higher_is_better,
                threshold_name=None if threshold_value is None else threshold_name,
                threshold_value=threshold_value,
                status=ThresholdStatus.PASSED if passed else ThresholdStatus.DROPPED,
                reason=(
                    "no_route_threshold"
                    if threshold_value is None
                    else (
                        "passed_route_threshold"
                        if passed
                        else "dropped_by_route_threshold"
                    )
                ),
            )
        )
        if passed:
            kept.append(candidate)
    return (
        RankedRoute(
            name=route.name,
            status=RouteStatus.SUCCESS if kept else RouteStatus.EMPTY,
            candidates=tuple(kept),
        ),
        tuple(decisions),
    )


def _lexical_report(result, before, after, decisions, config):
    diagnostics = None if result is None else result.diagnostics
    return _route_report(
        before,
        after,
        decisions,
        indexed=None if diagnostics is None else diagnostics.indexed_chunk_count,
        visible=None if diagnostics is None else diagnostics.visible_chunk_count,
        matched=None if diagnostics is None else diagnostics.matched_chunk_count,
        native_score_name="postgresql_ts_rank",
        higher_is_better=True,
        threshold_name=(
            None if config.lexical_min_rank is None else "lexical_min_fts_rank"
        ),
        threshold_value=config.lexical_min_rank,
        latency=None if diagnostics is None else diagnostics.latency_ms,
    )


def _dense_report(result, before, after, decisions, config):
    diagnostics = None if result is None else result.diagnostics
    return _route_report(
        before,
        after,
        decisions,
        indexed=None if diagnostics is None else diagnostics.indexed_chunk_count,
        visible=None if diagnostics is None else diagnostics.visible_chunk_count,
        matched=None,
        native_score_name="pgvector_cosine_distance",
        higher_is_better=False,
        threshold_name=(
            None if config.dense_max_distance is None else "dense_max_cosine_distance"
        ),
        threshold_value=config.dense_max_distance,
        latency=None if diagnostics is None else diagnostics.latency_ms,
    )


def _route_report(
    before,
    after,
    decisions,
    *,
    indexed,
    visible,
    matched,
    native_score_name,
    higher_is_better,
    threshold_name,
    threshold_value,
    latency,
):
    passed = sum(item.status is ThresholdStatus.PASSED for item in decisions)
    dropped = sum(item.status is ThresholdStatus.DROPPED for item in decisions)
    return RouteControlReport(
        route_name=before.name,
        execution_status=before.status,
        post_threshold_status=after.status,
        indexed_chunk_count=indexed,
        visible_chunk_count=visible,
        matched_chunk_count=matched,
        candidate_count=len(before.candidates),
        passed_threshold_count=passed,
        dropped_threshold_count=dropped,
        native_score_name=native_score_name,
        higher_is_better=higher_is_better,
        threshold_name=threshold_name,
        threshold_value=threshold_value,
        latency_ms=latency,
        error_code=before.error_code,
        error_message=before.error_message,
    )


def _no_result_reason(candidates, route_reports, failed_routes):
    if candidates:
        return None
    if len(failed_routes) == len(route_reports):
        return NoResultReason.ALL_ROUTES_FAILED
    if failed_routes:
        return NoResultReason.ROUTE_FAILURE
    visible_counts = [
        report.visible_chunk_count
        for report in route_reports.values()
        if report.visible_chunk_count is not None
    ]
    if visible_counts and all(value == 0 for value in visible_counts):
        return NoResultReason.VISIBLE_SCOPE_EMPTY
    if sum(report.candidate_count for report in route_reports.values()) == 0:
        return NoResultReason.NO_ROUTE_MATCH
    if sum(report.passed_threshold_count for report in route_reports.values()) == 0:
        return NoResultReason.ALL_BELOW_THRESHOLD
    return NoResultReason.NO_ROUTE_MATCH
