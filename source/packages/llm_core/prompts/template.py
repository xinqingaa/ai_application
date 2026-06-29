"""Prompt template types for llm_core."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    prompt_id: str
    version: str
    model_config_ref: str
    system: str
    user: str

    @property
    def ref(self) -> str:
        return f"{self.prompt_id}@{self.version}"
