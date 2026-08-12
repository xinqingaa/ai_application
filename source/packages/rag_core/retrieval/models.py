"""Contracts for PostgreSQL lexical indexing and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.lexical.models import QueryOperator


@dataclass(frozen=True)
class ChunkIndexReport:
    indexed_chunks: int
    lexical_config_ref: str
    latency_ms: float


# Backward-compatible name for the step 11 public API. Chunk persistence is now
# shared by lexical and dense routes, so new code should use ChunkIndexReport.
LexicalIndexReport = ChunkIndexReport


@dataclass(frozen=True)
class DeleteReport:
    deleted_chunks: int
    latency_ms: float


@dataclass(frozen=True)
class LexicalHit:
    chunk_id: str
    document_id: str
    document_version: str
    content: str
    source_role: SourceRole
    evidence_eligibility: EvidenceEligibility
    business_metadata: Mapping[str, str]
    matched_terms: tuple[str, ...]
    fts_rank: float
    route_rank: int


@dataclass(frozen=True)
class LexicalDiagnostics:
    query: str
    normalized_query: str
    query_terms: tuple[str, ...]
    postgres_query_terms: tuple[str, ...]
    tsquery: str
    query_operator: QueryOperator
    lexical_config_ref: str
    retriever_config_ref: str
    postgres_config: str
    knowledge_scope: str | None
    source_roles: tuple[SourceRole, ...]
    evidence_eligibilities: tuple[EvidenceEligibility, ...]
    indexed_chunk_count: int
    visible_chunk_count: int
    matched_chunk_count: int
    returned_chunk_count: int
    candidate_k: int
    rank_name: str
    higher_is_better: bool
    latency_ms: float


@dataclass(frozen=True)
class LexicalSearchResult:
    hits: tuple[LexicalHit, ...]
    diagnostics: LexicalDiagnostics


class DenseSearchMode(str, Enum):
    EXACT = "exact"
    HNSW = "hnsw"


@dataclass(frozen=True)
class DenseHit:
    chunk_id: str
    document_id: str
    document_version: str
    content: str
    source_role: SourceRole
    evidence_eligibility: EvidenceEligibility
    business_metadata: Mapping[str, str]
    cosine_distance: float
    cosine_similarity: float
    route_rank: int


@dataclass(frozen=True)
class DenseDiagnostics:
    query: str
    embedding_space_ref: str
    provider: str
    config_ref: str
    model: str
    dimensions: int
    preprocessing_version: str
    knowledge_scope: str | None
    source_roles: tuple[SourceRole, ...]
    evidence_eligibilities: tuple[EvidenceEligibility, ...]
    indexed_chunk_count: int
    visible_chunk_count: int
    returned_chunk_count: int
    candidate_k: int
    distance_name: str
    lower_is_better: bool
    search_mode: DenseSearchMode
    index_name: str | None
    index_used: bool | None
    plan_node_types: tuple[str, ...]
    latency_ms: float


@dataclass(frozen=True)
class DenseSearchResult:
    hits: tuple[DenseHit, ...]
    diagnostics: DenseDiagnostics
