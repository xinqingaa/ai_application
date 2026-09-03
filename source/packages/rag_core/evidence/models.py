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
