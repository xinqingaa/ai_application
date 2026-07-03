"""Deterministic extractive compression for context sources."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Optional

from llm_core.context.formatting import format_context_source
from llm_core.context.tokenization import estimate_tokens
from llm_core.context.types import CompressedContextSource, ContextBuildPolicy, ContextSource

COMMON_TERMS = {
    "这个",
    "需求",
    "新增",
    "需要",
    "进行",
    "如果",
    "以及",
    "相关",
    "说明",
    "用户",
    "系统",
}


def extract_keywords(text: str) -> set[str]:
    candidates = re.findall(r"[A-Za-z0-9_./-]+|[\u4e00-\u9fff]{2,8}", text)
    return {term for term in candidates if len(term) > 1 and term not in COMMON_TERMS}


def fit_source(
    source: ContextSource,
    *,
    available_tokens: int,
    policy: ContextBuildPolicy,
    keywords: set[str],
    model: Optional[str],
) -> tuple[ContextSource, int, Optional[CompressedContextSource]]:
    full_tokens = estimate_tokens(format_context_source(source), model=model)
    source_cap = policy.max_source_tokens or available_tokens
    target_tokens = min(available_tokens, source_cap)
    if full_tokens <= target_tokens:
        return source, full_tokens, None

    if not policy.allow_compression or target_tokens < policy.min_compression_tokens:
        return source, full_tokens, None

    compressed_content = compress_text(source.content, target_tokens=target_tokens, keywords=keywords, model=model)
    compressed_source = replace(
        source,
        content=compressed_content,
        metadata={**source.metadata, "compressed": "true"},
    )
    compressed_tokens = estimate_tokens(format_context_source(compressed_source), model=model)
    if compressed_tokens < full_tokens and compressed_tokens <= available_tokens:
        return (
            compressed_source,
            compressed_tokens,
            CompressedContextSource(
                source_id=source.source_id,
                original_tokens=full_tokens,
                compressed_tokens=compressed_tokens,
            ),
        )
    if full_tokens <= available_tokens:
        return source, full_tokens, None
    return source, full_tokens, None


def compress_text(text: str, *, target_tokens: int, keywords: set[str], model: Optional[str]) -> str:
    segments = split_segments(text)
    if not segments:
        return text

    ranked = sorted(
        enumerate(segments),
        key=lambda item: (segment_score(item[1], keywords), -item[0]),
        reverse=True,
    )
    selected: list[tuple[int, str]] = []
    used_tokens = 0
    for index, segment in ranked:
        segment_tokens = estimate_tokens(segment, model=model)
        if used_tokens + segment_tokens > target_tokens:
            continue
        selected.append((index, segment))
        used_tokens += segment_tokens
        if used_tokens >= target_tokens * 0.75:
            break

    if not selected:
        approx_chars = max(40, target_tokens * 2)
        return f"{text[:approx_chars].rstrip()}..."

    ordered = [segment for _, segment in sorted(selected, key=lambda item: item[0])]
    return "\n".join(ordered)


def split_segments(text: str) -> list[str]:
    raw_segments: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if len(stripped) <= 120:
            raw_segments.append(stripped)
            continue
        raw_segments.extend(part.strip() for part in re.split(r"(?<=[。；;.!?？])", stripped) if part.strip())
    return raw_segments


def segment_score(segment: str, keywords: set[str]) -> float:
    score = 0.0
    for keyword in keywords:
        if keyword and keyword in segment:
            score += 1.0
    return score
