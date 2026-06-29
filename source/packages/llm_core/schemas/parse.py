"""Parse model text into Pydantic models."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from pydantic import TypeAdapter, ValidationError

from llm_core.schemas.review import ReviewRisk, ReviewRiskList

_JSON_FENCE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class StructuredParseResult:
    ok: bool
    risks: Optional[list[ReviewRisk]]
    error_stage: Optional[str] = None  # json | schema | empty
    message: Optional[str] = None

    @property
    def risk_count(self) -> int:
        return len(self.risks) if self.risks else 0


def extract_json_text(content: str) -> str:
    text = content.strip()
    if not text:
        return text
    fence = _JSON_FENCE.match(text)
    if fence:
        return fence.group(1).strip()
    return text


def parse_risk_list(content: str) -> StructuredParseResult:
    """Parse assistant content into ReviewRisk list (array or {risks: [...]})."""
    text = extract_json_text(content)
    if not text:
        return StructuredParseResult(
            ok=False,
            risks=None,
            error_stage="empty",
            message="模型输出为空",
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return StructuredParseResult(
            ok=False,
            risks=None,
            error_stage="json",
            message=str(exc),
        )

    try:
        if isinstance(data, list):
            risks = TypeAdapter(list[ReviewRisk]).validate_python(data)
        elif isinstance(data, dict):
            if "risks" in data:
                risks = ReviewRiskList.model_validate(data).risks
            else:
                risks = [ReviewRisk.model_validate(data)]
        else:
            return StructuredParseResult(
                ok=False,
                risks=None,
                error_stage="json",
                message=f"不支持的 JSON 根类型: {type(data).__name__}",
            )
        return StructuredParseResult(ok=True, risks=risks)
    except ValidationError as exc:
        return StructuredParseResult(
            ok=False,
            risks=None,
            error_stage="schema",
            message=str(exc),
        )
