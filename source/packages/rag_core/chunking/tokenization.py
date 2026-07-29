"""Deterministic token-aware character range splitting."""

from __future__ import annotations

import tiktoken


class TokenCounter:
    def __init__(self, encoding_name: str) -> None:
        try:
            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception as exc:
            raise ValueError(f"不支持的 tokenizer encoding：{encoding_name}") from exc
        self.encoding_name = encoding_name

    def count(self, text: str) -> int:
        return len(self._encoding.encode(text))

    def split_ranges(
        self,
        text: str,
        *,
        max_tokens: int,
        overlap_tokens: int = 0,
    ) -> tuple[tuple[int, int], ...]:
        if not text:
            return ()
        ranges: list[tuple[int, int]] = []
        start = 0
        while start < len(text):
            end = self._largest_end(text, start, max_tokens)
            if end < len(text):
                end = _prefer_end_boundary(text, start, end)
            trimmed_start, trimmed_end = _trim_range(text, start, end)
            if trimmed_end > trimmed_start:
                ranges.append((trimmed_start, trimmed_end))
            if end >= len(text):
                break
            if overlap_tokens:
                next_start = self._suffix_start(text, start, end, overlap_tokens)
                next_start = _prefer_start_boundary(text, next_start, end)
                start = next_start if next_start > start else end
            else:
                start = end
        return tuple(ranges)

    def _largest_end(self, text: str, start: int, max_tokens: int) -> int:
        low = start + 1
        high = len(text)
        best = start
        while low <= high:
            middle = (low + high) // 2
            if self.count(text[start:middle]) <= max_tokens:
                best = middle
                low = middle + 1
            else:
                high = middle - 1
        return best if best > start else start + 1

    def _suffix_start(
        self,
        text: str,
        window_start: int,
        window_end: int,
        overlap_tokens: int,
    ) -> int:
        low = window_start
        high = window_end
        best = window_end
        while low <= high:
            middle = (low + high) // 2
            if self.count(text[middle:window_end]) <= overlap_tokens:
                best = middle
                high = middle - 1
            else:
                low = middle + 1
        return best


def _trim_range(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _prefer_end_boundary(text: str, start: int, end: int) -> int:
    floor = start + max(1, (end - start) // 2)
    for index in range(end, floor, -1):
        if text[index - 1] in ".!?。！？;；\n":
            return index
    for index in range(end, floor, -1):
        if index < len(text) and text[index].isspace():
            return index
    return end


def _prefer_start_boundary(text: str, start: int, end: int) -> int:
    for index in range(start, end):
        if text[index].isspace():
            while index < end and text[index].isspace():
                index += 1
            return index
    return start
