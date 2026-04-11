"""
Minimal LangChain-style client placeholder.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.config import Settings, get_settings


class LangChainLLMClient:
    """
    A LangChain-facing placeholder.

    Real LangChain objects are intentionally not imported yet. This file fixes the
    boundary and leaves a stable replacement point for the next implementation step.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def mocked(self) -> bool:
        return True

    def invoke(self, prompt: str) -> str:
        preview = " ".join(prompt.split())[:220]
        return (
            "LangChain mock response. "
            "This output stands in for prompt -> llm -> parser composition. "
            f"Prompt preview: {preview}"
        )

    def stream(self, prompt: str) -> Iterator[str]:
        text = self.invoke(prompt)
        for token in text.split():
            yield f"{token} "
