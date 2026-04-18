from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class GenerationProviderConfig:
    """Runtime config for the answer-generation model."""

    provider_name: str
    model_name: str
    api_key_env: str | None = None
    base_url: str | None = None
    base_url_env: str | None = None
    temperature: float = 0.0
    max_tokens: int = 280
    timeout_seconds: float = 20.0


@dataclass(slots=True)
class GenerationUsage:
    """Normalized usage payload returned by the generation client."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(slots=True)
class GenerationResult:
    """Normalized response returned by the generation client."""

    provider_name: str
    model_name: str
    content: str
    mocked: bool = False
    finish_reason: str | None = None
    usage: GenerationUsage | None = None
    request_preview: list[dict[str, str]] | None = None
    raw_response_preview: dict[str, Any] | None = None
    error: str | None = None


class LLMClient(Protocol):
    """Stable generation interface consumed by the RAG service."""

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        ...


@dataclass(slots=True)
class OpenAICompatibleLLMClient:
    """Real answer-generation path for OpenAI-compatible providers."""

    config: GenerationProviderConfig
    api_key: str

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai SDK is not installed") from exc

        base_url = self.config.base_url
        if base_url is None and self.config.base_url_env:
            base_url = os.getenv(self.config.base_url_env)

        client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=self.config.timeout_seconds,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        message = response.choices[0].message.content or ""
        usage = None
        if response.usage is not None:
            usage = GenerationUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        raw_preview = {
            "finish_reason": response.choices[0].finish_reason,
            "content_preview": message[:200],
        }
        return GenerationResult(
            provider_name=self.config.provider_name,
            model_name=self.config.model_name,
            content=message.strip(),
            mocked=False,
            finish_reason=response.choices[0].finish_reason,
            usage=usage,
            request_preview=messages,
            raw_response_preview=raw_preview,
        )


@dataclass(slots=True)
class MockLLMClient:
    """Deterministic fallback that keeps Phase 6 runnable without API access."""

    config: GenerationProviderConfig
    fallback_reason: str | None = None

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        user_content = messages[-1]["content"] if messages else ""
        question = _extract_section(
            user_content,
            "问题：",
            "回答要求：",
        ) or _extract_section(
            user_content,
            "Question:",
            "Answer Requirements:",
        )
        context = _extract_section(
            user_content,
            "上下文：",
            "问题：",
        ) or _extract_section(
            user_content,
            "Context:",
            "Question:",
        )

        answer = _build_mock_answer(question=question or "", context=context or "")
        return GenerationResult(
            provider_name="mock",
            model_name="mock-rag-answer-v1",
            content=answer,
            mocked=True,
            finish_reason="mock_stop",
            request_preview=messages,
            raw_response_preview={"answer_preview": answer[:200]},
            error=self.fallback_reason,
        )


def create_generation_client(config: GenerationProviderConfig) -> LLMClient:
    """Create a real or mock generation client depending on local readiness."""

    if config.provider_name != "openai_compatible":
        return MockLLMClient(config=config)

    api_key = os.getenv(config.api_key_env or "") if config.api_key_env else None
    if not api_key:
        return MockLLMClient(
            config=config,
            fallback_reason=f"missing_api_key_env:{config.api_key_env}",
        )

    try:
        import openai  # noqa: F401
    except ImportError:
        return MockLLMClient(
            config=config,
            fallback_reason="openai_sdk_not_installed",
        )

    return OpenAICompatibleLLMClient(config=config, api_key=api_key)


@dataclass(slots=True)
class _ContextBlock:
    label: str
    content: str


def _extract_section(text: str, start_marker: str, end_marker: str) -> str | None:
    start_index = text.find(start_marker)
    if start_index == -1:
        return None
    start_index += len(start_marker)
    end_index = text.find(end_marker, start_index)
    if end_index == -1:
        end_index = len(text)
    return text[start_index:end_index].strip()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _keyword_tokens(question: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z]{4,}|[\u4e00-\u9fff]{2,}", question.lower())
    seen: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return seen


def _parse_context_blocks(context: str) -> list[_ContextBlock]:
    pattern = re.compile(r"(?ms)^\[(S\d+)\][^\n]*\n(.*?)(?=^\[S\d+\]|\Z)")
    blocks: list[_ContextBlock] = []
    for label, content in pattern.findall(context):
        blocks.append(_ContextBlock(label=label, content=content.strip()))
    return blocks


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    cleaned = [item.strip() for item in sentences if item.strip()]
    return cleaned


def _build_mock_answer(question: str, context: str) -> str:
    blocks = _parse_context_blocks(context)
    if not blocks:
        return "我不知道。当前检索到的内容不足以支持这个问题。"

    keywords = _keyword_tokens(question)
    candidates: list[tuple[int, str, str]] = []
    for block in blocks:
        for sentence in _split_sentences(block.content):
            sentence_lower = sentence.lower()
            overlap = sum(1 for token in keywords if token in sentence_lower or token in sentence)
            candidates.append((overlap, block.label, sentence))

    candidates.sort(key=lambda item: (item[0], len(item[2])), reverse=True)
    selected: list[str] = []
    for _, label, sentence in candidates:
        cited_sentence = f"{sentence} [{label}]"
        if cited_sentence not in selected:
            selected.append(cited_sentence)
        if len(selected) == 2:
            break

    if not selected:
        for block in blocks[:2]:
            first_sentence = _split_sentences(block.content)
            if first_sentence:
                selected.append(f"{first_sentence[0]} [{block.label}]")

    if _contains_cjk(question):
        return "根据检索到的资料，" + "；".join(selected)
    return "Based on the retrieved context, " + " ".join(selected)
