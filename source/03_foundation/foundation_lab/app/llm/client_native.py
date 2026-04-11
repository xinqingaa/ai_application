"""
Minimal native client placeholder.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.config import Settings, get_settings


class NativeLLMClient:
    """
    A native client skeleton.

    This class is intentionally simple for the current phase. When real provider
    integration starts, replace the mock branch with the actual SDK call.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def mocked(self) -> bool:
        return self.settings.use_mock_when_unconfigured or not self.settings.api_key

    def invoke(self, prompt: str) -> str:
        if self.mocked:
            return self._mock_response(prompt)
        return "Native provider integration has not been implemented yet."

    def stream(self, prompt: str) -> Iterator[str]:
        text = self.invoke(prompt)
        for token in text.split():
            yield f"{token} "

    def structured_invoke(self, question: str) -> dict[str, str | bool]:
        return {
            "question": question,
            "engine": "native",
            "mocked": self.mocked,
            "summary": self.invoke(f"Summarize the question: {question}"),
        }

    def _mock_response(self, prompt: str) -> str:
        preview = " ".join(prompt.split())[:220]
        return (
            "Native mock response. "
            "This output proves the service layer and prompt pipeline are wired. "
            f"Prompt preview: {preview}"
        )
