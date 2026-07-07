"""Cache key construction for exact-match LLM result caching."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class CacheKeyParts:
    config_ref: str
    messages: list[dict[str, str]]
    model: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_version: Optional[str] = None
    structured_mode: Optional[str] = None
    schema_version: Optional[str] = None
    temperature: Optional[float] = None
    context_fingerprint: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


def build_cache_key(parts: CacheKeyParts) -> str:
    payload = {
        "config_ref": parts.config_ref,
        "model": parts.model,
        "prompt_id": parts.prompt_id,
        "prompt_version": parts.prompt_version,
        "structured_mode": parts.structured_mode,
        "schema_version": parts.schema_version,
        "temperature": parts.temperature,
        "context_fingerprint": parts.context_fingerprint,
        "messages_hash": fingerprint_messages(parts.messages),
        "extra": parts.extra,
    }
    return stable_fingerprint(payload)


def fingerprint_messages(messages: list[dict[str, str]]) -> str:
    return stable_fingerprint(messages)


def stable_fingerprint(value: Any) -> str:
    normalized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
