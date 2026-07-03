"""Context engineering API for llm_core."""

from llm_core.context.builder import build_review_context
from llm_core.context.formatting import format_context_source, format_evidence_block
from llm_core.context.policies import get_context_policy, list_context_policy_names
from llm_core.context.tokenization import estimate_tokens
from llm_core.context.types import (
    BuiltContext,
    CitationCandidate,
    CompressedContextSource,
    ContextBuildPolicy,
    ContextBuildReport,
    ContextSection,
    ContextSectionName,
    ContextSource,
    ContextSourceType,
    ContextWarning,
    DroppedContextSource,
)

__all__ = [
    "BuiltContext",
    "CitationCandidate",
    "CompressedContextSource",
    "ContextBuildPolicy",
    "ContextBuildReport",
    "ContextSection",
    "ContextSectionName",
    "ContextSource",
    "ContextSourceType",
    "ContextWarning",
    "DroppedContextSource",
    "build_review_context",
    "estimate_tokens",
    "format_context_source",
    "format_evidence_block",
    "get_context_policy",
    "list_context_policy_names",
]
