"""Token estimation utilities for local context budgeting."""

from __future__ import annotations

from typing import Optional


def estimate_tokens(text: str, *, model: Optional[str] = None) -> int:
    """Estimate tokens for budget decisions without requiring a live API call."""

    cleaned = text.strip()
    if not cleaned:
        return 0
    try:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(model or "gpt-4o-mini")
        except Exception:
            encoding = tiktoken.get_encoding("o200k_base")
        return len(encoding.encode(cleaned))
    except Exception:
        return max(1, len(cleaned) // 2)
