"""Data contracts for quote location and Citation support validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from llm_core import CostEstimate, StructuredLLMResponse, TokenUsage


class QuoteLocationStatus(str, Enum):
    LOCATED = "located"
    QUOTE_NOT_FOUND = "quote_not_found"
    AMBIGUOUS_QUOTE = "ambiguous_quote"
    MISSING_EXCERPT = "missing_excerpt"
    SOURCE_NOT_ALLOWED = "source_not_allowed"


class CitationSupportVerdict(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNRELATED = "unrelated"
    INDETERMINATE = "indeterminate"


class CitationSupportValidationStatus(str, Enum):
    COMPLETED = "completed"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    JUDGMENT_SET_INVALID = "judgment_set_invalid"


@dataclass(frozen=True)
class CitationSupportInput:
    claim_id: str
    claim_text: str
    source_id: str
    excerpt: str


@dataclass(frozen=True)
class CitationSupportCheck:
    claim_id: str
    claim_text: str
    source_id: str
    excerpt: str
    location_status: QuoteLocationStatus
    source_locator: str | None
    char_start: int | None
    char_end: int | None
    match_count: int
    verdict: CitationSupportVerdict | None = None
    reason: str | None = None


@dataclass(frozen=True)
class VerifiedCitation:
    claim_id: str
    claim_text: str
    source_id: str
    excerpt: str
    source_locator: str | None
    char_start: int
    char_end: int
    verdict: CitationSupportVerdict
    reason: str


@dataclass(frozen=True)
class CitationSupportReport:
    status: CitationSupportValidationStatus
    prompt_ref: str
    config_ref: str
    structured_mode: str
    input_count: int
    located_count: int
    quote_not_found_count: int
    ambiguous_quote_count: int
    skipped_count: int
    judged_count: int
    supported_count: int
    contradicted_count: int
    unrelated_count: int
    indeterminate_count: int
    model_call_count: int
    usage: TokenUsage | None
    cost: CostEstimate | None
    latency_ms: float | None
    parse_error_stage: str | None = None
    parse_error_message: str | None = None
    boundary: str = "quote_location_then_semantic_support_not_sufficiency"


@dataclass(frozen=True)
class CitationSupportResult:
    checks: tuple[CitationSupportCheck, ...]
    verified_citations: tuple[VerifiedCitation, ...]
    report: CitationSupportReport
    messages: tuple[dict[str, str], ...]
    response: StructuredLLMResponse | None


class EvidenceDecisionKind(str, Enum):
    """How far the current evidence can support the requested conclusion."""

    ANSWERABLE = "answerable"
    PARTIAL = "partial"
    REFUSAL = "refusal"


class EvidenceCoverageVerdict(str, Enum):
    COVERED = "covered"
    GAP = "gap"


class EvidenceSufficiencyValidationStatus(str, Enum):
    COMPLETED = "completed"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    JUDGMENT_SET_INVALID = "judgment_set_invalid"


@dataclass(frozen=True)
class EvidenceClaim:
    """A conclusion whose required facts must be covered."""

    claim_id: str
    claim_text: str


@dataclass(frozen=True)
class EvidenceRequirement:
    """One fact category that must be covered before affected claims are strong."""

    requirement_id: str
    required_fact: str
    expected_source_role: str
    affected_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceScopeSource:
    """An active, bounded source record supplied to sufficiency validation."""

    source_id: str
    source_role: str
    content: str
    source_locator: str | None = None


@dataclass(frozen=True)
class EvidenceGap:
    requirement_id: str
    missing_fact: str
    expected_source_role: str
    affected_claim_ids: tuple[str, ...]
    reason: str
    question: str


@dataclass(frozen=True)
class EvidenceCoverageCheck:
    requirement_id: str
    verdict: EvidenceCoverageVerdict
    reason: str
    citation_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceDecision:
    kind: EvidenceDecisionKind
    coverage: tuple[EvidenceCoverageCheck, ...]
    gaps: tuple[EvidenceGap, ...]


@dataclass(frozen=True)
class EvidenceSufficiencyReport:
    status: EvidenceSufficiencyValidationStatus
    prompt_ref: str
    config_ref: str
    structured_mode: str
    claim_count: int
    requirement_count: int
    active_source_count: int
    verified_citation_count: int
    covered_count: int
    gap_count: int
    model_call_count: int
    usage: TokenUsage | None
    cost: CostEstimate | None
    latency_ms: float | None
    parse_error_stage: str | None = None
    parse_error_message: str | None = None
    boundary: str = "verified_citations_and_coverage_contract_not_approval"


@dataclass(frozen=True)
class EvidenceSufficiencyResult:
    decision: EvidenceDecision | None
    report: EvidenceSufficiencyReport
    messages: tuple[dict[str, str], ...]
    response: StructuredLLMResponse | None
