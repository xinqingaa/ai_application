"""
llm_utils.py
第一章公共工具：环境变量、provider 配置、模型调用、token 估算、导出工具
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"


def load_env_if_possible() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


@dataclass
class ProviderConfig:
    provider: str
    api_key: str | None
    base_url: str | None
    model: str
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None

    @property
    def is_ready(self) -> bool:
        return bool(self.api_key)


@dataclass
class ChatUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatResult:
    provider: str
    model: str
    content: str
    usage: ChatUsage | None = None
    mocked: bool = False
    request_preview: dict[str, Any] | None = None
    raw_response_preview: dict[str, Any] | None = None


@dataclass
class ConversationExport:
    provider: str
    model: str
    exported_at: str
    messages: list[dict[str, str]]
    metadata: dict[str, Any] = field(default_factory=dict)


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    provider_name = (provider or os.getenv("DEFAULT_PROVIDER", "openai")).strip().lower()

    mapping = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "input_price_per_million": _parse_float(os.getenv("OPENAI_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("OPENAI_OUTPUT_PRICE_PER_MILLION")),
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL"),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "input_price_per_million": _parse_float(os.getenv("DEEPSEEK_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("DEEPSEEK_OUTPUT_PRICE_PER_MILLION")),
        },
        "bailian": {
            "api_key": os.getenv("BAILIAN_API_KEY"),
            "base_url": os.getenv("BAILIAN_BASE_URL"),
            "model": os.getenv("BAILIAN_MODEL", "qwen-plus"),
            "input_price_per_million": _parse_float(os.getenv("BAILIAN_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("BAILIAN_OUTPUT_PRICE_PER_MILLION")),
        },
        "glm": {
            "api_key": os.getenv("GLM_API_KEY"),
            "base_url": os.getenv("GLM_BASE_URL"),
            "model": os.getenv("GLM_MODEL", "glm-4.5-air"),
            "input_price_per_million": _parse_float(os.getenv("GLM_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("GLM_OUTPUT_PRICE_PER_MILLION")),
        },
    }

    data = mapping.get(provider_name, mapping["openai"])
    return ProviderConfig(provider=provider_name, **data)


def preview_chat_request(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    stop: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if stop:
        payload["stop"] = stop
    return payload


def call_openai_compatible_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 300,
    stop: list[str] | None = None,
) -> ChatResult:
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, stop)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    response = client.chat.completions.create(
        model=config.model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop,
    )

    usage = None
    if response.usage:
        usage = ChatUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason
    raw_response_preview = {
        "id": response.id,
        "model": response.model,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {
                    "role": message.role,
                    "content": message.content,
                },
            }
        ],
        "usage": asdict(usage) if usage else None,
    }
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=message.content or "",
        usage=usage,
        mocked=False,
        request_preview=request_preview,
        raw_response_preview=raw_response_preview,
    )


def mock_chat_response(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 300,
) -> ChatResult:
    last_user = ""
    system_prompt = ""
    for item in messages:
        if item["role"] == "system" and not system_prompt:
            system_prompt = item["content"]
    for item in reversed(messages):
        if item["role"] == "user":
            last_user = item["content"]
            break

    content = (
        f"[MOCK:{config.provider}] 你最后一次提问是：{last_user}\n"
        f"当前 system prompt 摘要：{system_prompt[:40] or '（无）'}\n"
        f"temperature={temperature}, max_tokens={max_tokens}"
    )
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=content,
        mocked=True,
        request_preview=preview_chat_request(config, messages, temperature, max_tokens),
        raw_response_preview={
            "id": "mock-chatcmpl-001",
            "model": config.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": None,
        },
    )


def estimate_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    try:
        import tiktoken
    except ImportError:
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        non_ascii_chars = len(text) - ascii_chars
        english_est = max(1, ascii_chars // 4) if ascii_chars else 0
        chinese_est = max(1, int(non_ascii_chars / 1.5)) if non_ascii_chars else 0
        return english_est + chinese_est

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def estimate_messages_tokens(messages: list[dict[str, str]], encoding_name: str = "cl100k_base") -> int:
    total = 0
    for item in messages:
        total += estimate_tokens(item["role"], encoding_name)
        total += estimate_tokens(item["content"], encoding_name)
        total += 4
    return total + 2


def trim_messages_by_recent_messages(
    messages: list[dict[str, str]],
    keep_last_messages: int = 6,
) -> list[dict[str, str]]:
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    return system_messages + others[-keep_last_messages:]


def trim_messages_by_token_budget(
    messages: list[dict[str, str]],
    max_input_tokens: int,
    encoding_name: str = "cl100k_base",
) -> list[dict[str, str]]:
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    result = list(system_messages)

    for item in reversed(others):
        candidate = system_messages + [item] + result[len(system_messages):]
        if estimate_messages_tokens(candidate, encoding_name) <= max_input_tokens:
            result = system_messages + [item] + result[len(system_messages):]
        else:
            break
    return result


def calculate_cost_from_usage(
    usage: ChatUsage | None,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
) -> float | None:
    if not usage or input_price_per_million is None or output_price_per_million is None:
        return None
    input_cost = usage.prompt_tokens / 1_000_000 * input_price_per_million
    output_cost = usage.completion_tokens / 1_000_000 * output_price_per_million
    return input_cost + output_cost


def format_cost(cost: float | None) -> str:
    if cost is None:
        return "未配置价格"
    return f"${cost:.6f}"


def ensure_export_dir() -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR


def export_conversation(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    metadata: dict[str, Any] | None = None,
) -> Path:
    export_dir = ensure_export_dir()
    filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = export_dir / filename
    payload = ConversationExport(
        provider=provider,
        model=model,
        exported_at=datetime.now().isoformat(),
        messages=messages,
        metadata=metadata or {},
    )
    path.write_text(json.dumps(asdict(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
