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


class Citation(BaseModel):
    """Reference to evidence; source_id validity is checked in 03_rag."""

    source_id: str = Field(..., description="Evidence chunk id from context / RAG")
    excerpt: Optional[str] = Field(None, description="Short quote from the source")


class ReviewRisk(BaseModel):
    title: str
    category: RiskCategory
    level: RiskLevel
    rationale: str
    citations: list[Citation] = Field(default_factory=list)


class ReviewRiskList(BaseModel):
    """Wrapper for Structured Outputs API (root must be an object, not a bare array)."""

    risks: list[ReviewRisk]


class ClarificationQuestion(BaseModel):
    """Used in later sections for blocking clarification when evidence is insufficient."""

    question: str
    blocking: bool = True
    reason: Optional[str] = None
