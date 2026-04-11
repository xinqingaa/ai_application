"""
Minimal chain assembly for foundation_lab.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol

from app.prompts.qa_prompt import format_qa_prompt


class PromptClient(Protocol):
    def invoke(self, prompt: str) -> str:
        ...

    def stream(self, prompt: str) -> Iterator[str]:
        ...


def parse_text_output(text: str) -> str:
    return text.strip()


class SimpleQAChain:
    def __init__(self, client: PromptClient) -> None:
        self.client = client

    def invoke(
        self,
        question: str,
        context_blocks: Sequence[str] | None = None,
        tool_result: str | None = None,
    ) -> str:
        prompt = format_qa_prompt(question, context_blocks=context_blocks, tool_result=tool_result)
        return parse_text_output(self.client.invoke(prompt))

    def stream(
        self,
        question: str,
        context_blocks: Sequence[str] | None = None,
        tool_result: str | None = None,
    ) -> Iterator[str]:
        prompt = format_qa_prompt(question, context_blocks=context_blocks, tool_result=tool_result)
        return self.client.stream(prompt)
