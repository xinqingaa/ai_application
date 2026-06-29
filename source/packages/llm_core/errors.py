"""LLM error types and classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class LLMErrorCode(str, Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    AUTH = "auth"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROVIDER_ERROR = "provider_error"
    SCHEMA_PARSE = "schema_parse"
    UNKNOWN = "unknown"


@dataclass
class LLMError(Exception):
    code: LLMErrorCode
    message: str
    config_ref: Optional[str] = None
    raw: Any = None

    def __str__(self) -> str:
        ref = f" [{self.config_ref}]" if self.config_ref else ""
        return f"{self.code.value}{ref}: {self.message}"
