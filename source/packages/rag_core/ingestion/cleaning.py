"""Deterministic, location-preserving text cleanup."""

from __future__ import annotations

import re
import unicodedata

from rag_core.ingestion.models import LoaderConfig


def clean_text(text: str, config: LoaderConfig) -> tuple[str, tuple[str, ...]]:
    actions: list[str] = []
    cleaned = text

    normalized_newlines = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    if normalized_newlines != cleaned:
        actions.append("normalize_newlines")
        cleaned = normalized_newlines

    if "\u00a0" in cleaned:
        cleaned = cleaned.replace("\u00a0", " ")
        actions.append("replace_non_breaking_space")

    if config.normalize_unicode:
        normalized_unicode = unicodedata.normalize("NFC", cleaned)
        if normalized_unicode != cleaned:
            actions.append("normalize_unicode_nfc")
            cleaned = normalized_unicode

    trimmed_lines = "\n".join(line.rstrip() for line in cleaned.split("\n"))
    if trimmed_lines != cleaned:
        actions.append("trim_line_endings")
        cleaned = trimmed_lines

    if config.collapse_blank_lines:
        collapsed = re.sub(r"\n{3,}", "\n\n", cleaned)
        if collapsed != cleaned:
            actions.append("collapse_blank_lines")
            cleaned = collapsed

    stripped = cleaned.strip()
    if stripped != cleaned:
        actions.append("trim_outer_whitespace")
        cleaned = stripped

    return cleaned, tuple(actions)
