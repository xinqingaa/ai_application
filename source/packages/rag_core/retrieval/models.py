"""Contracts for PostgreSQL lexical indexing and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from rag_core.ingestion.models import EvidenceEligibility, SourceRole
from rag_core.lexical.models import QueryOperator


@dataclass(frozen=True)
class LexicalIndexReport:
    indexed_chunks: int
    lexical_config_ref: str
    latency_ms: float


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
