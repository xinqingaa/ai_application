"""Review assistant structured models — field definitions are the schema source of truth."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskCategory(str, Enum):
    INTERACTION = "interaction"
    STATE_FLOW = "state_flow"
    API = "api"
    MULTI_PLATFORM = "multi_platform"
    EXCEPTION = "exception"
    OTHER = "other"


class _CitationFields(BaseModel):
    source_id: str = Field(..., description="Evidence chunk id from context / RAG")


class Citation(_CitationFields):
    """Reference to evidence; source_id validity is checked by the RAG evidence layer."""

    excerpt: Optional[str] = Field(None, description="Short quote from the source")


class QuotedCitation(_CitationFields):
    """Citation shape used once support validation requires a verbatim quote."""

    excerpt: str = Field(..., min_length=1, description="Verbatim quote from the source")


class _ReviewRiskFields(BaseModel):
    title: str
    category: RiskCategory
    level: RiskLevel
    rationale: str


class ReviewRisk(_ReviewRiskFields):
    citations: list[Citation] = Field(default_factory=list)


class ReviewRiskList(BaseModel):
    """Wrapper for Structured Outputs API (root must be an object, not a bare array)."""

    risks: list[ReviewRisk]


class QuotedReviewRisk(_ReviewRiskFields):
    """Review risk whose citations must include verbatim excerpts."""

    citations: list[QuotedCitation] = Field(default_factory=list)


class QuotedReviewRiskList(BaseModel):
    risks: list[QuotedReviewRisk]


class ClarificationQuestion(BaseModel):
    """Used in later sections for blocking clarification when evidence is insufficient."""

    question: str
    blocking: bool = True
    reason: Optional[str] = None
