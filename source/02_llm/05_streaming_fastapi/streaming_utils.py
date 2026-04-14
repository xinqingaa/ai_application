"""
streaming_utils.py
第五章公共工具：provider 配置、异步聊天、流式输出、SSE 编码、会话状态
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
DEFAULT_SYSTEM_PROMPT = "你是一个严谨、简洁、对开发者友好的 AI 助手。"
DEFAULT_DEBUG = True


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
    usage: ChatUsage | None
    mocked: bool
    request_preview: dict[str, Any]
    raw_response_preview: dict[str, Any]
    elapsed_ms: float


@dataclass
class StreamSummary:
    provider: str
    model: str
    mocked: bool
    request_preview: dict[str, Any]
    full_text: str
    first_token_ms: float | None
    elapsed_ms: float
    chunk_count: int
    input_tokens_estimate: int
    output_tokens_estimate: int


@dataclass
class SessionRecord:
    session_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    provider_name = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    mapping = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "input_price_per_million": _parse_float(os.getenv("OPENAI_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("OPENAI_OUTPUT_PRICE_PER_MILLION")),
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "input_price_per_million": _parse_float(os.getenv("DEEPSEEK_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("DEEPSEEK_OUTPUT_PRICE_PER_MILLION")),
        },
        "bailian": {
            "api_key": os.getenv("BAILIAN_API_KEY"),
            "base_url": os.getenv("BAILIAN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": os.getenv("BAILIAN_MODEL", "qwen-plus"),
            "input_price_per_million": _parse_float(os.getenv("BAILIAN_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("BAILIAN_OUTPUT_PRICE_PER_MILLION")),
        },
        "glm": {
            "api_key": os.getenv("GLM_API_KEY"),
            "base_url": os.getenv("GLM_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/",
            "model": os.getenv("GLM_MODEL", "glm-4.5-air"),
            "input_price_per_million": _parse_float(os.getenv("GLM_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("GLM_OUTPUT_PRICE_PER_MILLION")),
        },
    }
    data = mapping.get(provider_name, mapping["bailian"])
    return ProviderConfig(provider=provider_name, **data)


def preview_chat_request(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    stream: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if stream:
        payload["stream"] = True
    return payload


def _debug_print_start(
    config: ProviderConfig,
    request_preview: dict[str, Any],
    debug_label: str | None = None,
) -> None:
    if debug_label:
        print(f"\n{'=' * 72}")
        print(f"[DEBUG] {debug_label} -> 请求开始")
        print("=" * 72)
    print(
        "[DEBUG] chat.start "
        f"provider={config.provider} "
        f"model={config.model} "
        f"ready={config.is_ready}"
    )
    print("[DEBUG] request_preview:")
    print(json.dumps(request_preview, ensure_ascii=False, indent=2))


def _debug_print_result(result: ChatResult, debug_label: str | None = None) -> None:
    finish_reason = None
    choices = result.raw_response_preview.get("choices") or []
    if choices:
        finish_reason = choices[0].get("finish_reason")

    if debug_label:
        print(f"\n{'=' * 72}")
        print(f"[DEBUG] {debug_label} -> 返回结果")
        print("=" * 72)
    print(
        "[DEBUG] chat.result "
        f"provider={result.provider} "
        f"model={result.model} "
        f"mocked={result.mocked} "
        f"finish_reason={finish_reason or '（未返回）'} "
        f"elapsed_ms={result.elapsed_ms}"
    )
    print("[DEBUG] raw_response_preview:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    print("[DEBUG] raw_content:")
    print(result.content)


def _debug_print_stream_result(summary: StreamSummary, debug_label: str | None = None) -> None:
    if debug_label:
        print(f"\n{'=' * 72}")
        print(f"[DEBUG] {debug_label} -> 流式返回结果")
        print("=" * 72)
    print(
        "[DEBUG] stream.result "
        f"provider={summary.provider} "
        f"model={summary.model} "
        f"mocked={summary.mocked} "
        f"chunk_count={summary.chunk_count} "
        f"first_token_ms={summary.first_token_ms} "
        f"elapsed_ms={summary.elapsed_ms}"
    )
    print("[DEBUG] full_text:")
    print(summary.full_text)


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
    keep_last_messages: int = 10,
) -> list[dict[str, str]]:
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    return system_messages + others[-keep_last_messages:]


def ensure_system_message(messages: list[dict[str, str]], system_prompt: str | None) -> list[dict[str, str]]:
    target_prompt = (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()
    others = [item for item in messages if item["role"] != "system"]
    return [{"role": "system", "content": target_prompt}] + others


def build_messages_for_turn(
    history: list[dict[str, str]],
    user_text: str,
    system_prompt: str | None = None,
    keep_last_messages: int = 10,
) -> list[dict[str, str]]:
    base_messages = ensure_system_message(history, system_prompt)
    base_messages = trim_messages_by_recent_messages(base_messages, keep_last_messages=keep_last_messages)
    return base_messages + [{"role": "user", "content": user_text}]


def append_assistant_message(
    messages: list[dict[str, str]],
    assistant_text: str,
    keep_last_messages: int = 10,
) -> list[dict[str, str]]:
    updated = messages + [{"role": "assistant", "content": assistant_text}]
    return trim_messages_by_recent_messages(updated, keep_last_messages=keep_last_messages)


def create_session_id() -> str:
    return uuid.uuid4().hex[:12]


class InMemorySessionStore:
    def __init__(self) -> None:
        self._store: dict[str, SessionRecord] = {}

    def get_or_create(self, session_id: str | None = None) -> SessionRecord:
        key = session_id or create_session_id()
        if key not in self._store:
            self._store[key] = SessionRecord(session_id=key)
        return self._store[key]

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return list(self._store.get(session_id, SessionRecord(session_id=session_id)).messages)

    def save_history(self, session_id: str, messages: list[dict[str, str]]) -> None:
        record = self.get_or_create(session_id)
        record.messages = list(messages)
        record.updated_at = datetime.now().isoformat()

    def dump_session(self, session_id: str) -> dict[str, Any]:
        record = self.get_or_create(session_id)
        return {
            "session_id": record.session_id,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "messages": record.messages,
            "estimated_tokens": estimate_messages_tokens(record.messages),
        }


def _extract_last_user(messages: list[dict[str, str]]) -> str:
    for item in reversed(messages):
        if item["role"] == "user":
            return item["content"]
    return ""


def _extract_system_prompt(messages: list[dict[str, str]]) -> str:
    for item in messages:
        if item["role"] == "system":
            return item["content"]
    return ""


def _build_mock_reply(messages: list[dict[str, str]]) -> str:
    user_text = _extract_last_user(messages)
    system_text = _extract_system_prompt(messages)
    return (
        f"这是一个 mock 回复。\n"
        f"你刚才的问题是：{user_text}\n"
        f"当前 system prompt 摘要：{system_text[:40] or '（无）'}\n"
        f"如果接入真实 provider，这里会按 token 逐段返回内容。"
    )


async def chat_once(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 400,
    debug: bool = DEFAULT_DEBUG,
    debug_label: str | None = None,
) -> ChatResult:
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, stream=False)
    if debug:
        _debug_print_start(config, request_preview, debug_label)
    started = time.perf_counter()

    if not config.is_ready:
        content = _build_mock_reply(messages)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if debug:
            print(
                "[DEBUG] mock_fallback "
                f"provider={config.provider} "
                "reason=missing_api_key"
            )
        result = ChatResult(
            provider=config.provider,
            model=config.model,
            content=content,
            usage=None,
            mocked=True,
            request_preview=request_preview,
            raw_response_preview={
                "id": "mock-chat",
                "model": config.model,
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
                "usage": None,
            },
            elapsed_ms=elapsed_ms,
        )
        if debug:
            _debug_print_result(result, debug_label)
        return result

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
    try:
        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        if debug:
            print(
                "[DEBUG] request_failed "
                f"provider={config.provider} "
                f"error={type(exc).__name__}: {exc}"
            )
        raise
    usage = None
    if response.usage:
        usage = ChatUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )
    message = response.choices[0].message
    elapsed_ms = (time.perf_counter() - started) * 1000
    result = ChatResult(
        provider=config.provider,
        model=config.model,
        content=message.content or "",
        usage=usage,
        mocked=False,
        request_preview=request_preview,
        raw_response_preview={
            "id": response.id,
            "model": response.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": response.choices[0].finish_reason,
                    "message": {
                        "role": message.role,
                        "content": message.content,
                    },
                }
            ],
            "usage": asdict(usage) if usage else None,
        },
        elapsed_ms=elapsed_ms,
    )
    if debug:
        _debug_print_result(result, debug_label)
    return result


def _split_mock_chunks(text: str) -> list[str]:
    chunk_sizes = [4, 5, 3, 6]
    parts: list[str] = []
    cursor = 0
    index = 0
    while cursor < len(text):
        size = chunk_sizes[index % len(chunk_sizes)]
        parts.append(text[cursor : cursor + size])
        cursor += size
        index += 1
    return parts


async def stream_chat_events(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 400,
    debug: bool = DEFAULT_DEBUG,
    debug_label: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, stream=True)
    if debug:
        _debug_print_start(config, request_preview, debug_label)
    started = time.perf_counter()
    first_token_ms: float | None = None
    collected: list[str] = []
    chunk_count = 0

    if not config.is_ready:
        if debug:
            print(
                "[DEBUG] mock_fallback "
                f"provider={config.provider} "
                "reason=missing_api_key"
            )
        mock_text = _build_mock_reply(messages)
        for part in _split_mock_chunks(mock_text):
            await asyncio.sleep(0.08)
            chunk_count += 1
            if first_token_ms is None:
                first_token_ms = (time.perf_counter() - started) * 1000
            collected.append(part)
            yield {"type": "token", "delta": part}

        full_text = "".join(collected)
        summary = StreamSummary(
            provider=config.provider,
            model=config.model,
            mocked=True,
            request_preview=request_preview,
            full_text=full_text,
            first_token_ms=first_token_ms,
            elapsed_ms=(time.perf_counter() - started) * 1000,
            chunk_count=chunk_count,
            input_tokens_estimate=estimate_messages_tokens(messages),
            output_tokens_estimate=estimate_tokens(full_text),
        )
        if debug:
            _debug_print_stream_result(summary, debug_label)
        yield {
            "type": "done",
            "summary": summary,
        }
        return

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
    try:
        stream = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
    except Exception as exc:
        if debug:
            print(
                "[DEBUG] request_failed "
                f"provider={config.provider} "
                f"error={type(exc).__name__}: {exc}"
            )
        raise

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        chunk_count += 1
        if first_token_ms is None:
            first_token_ms = (time.perf_counter() - started) * 1000
        collected.append(delta)
        yield {"type": "token", "delta": delta}

    full_text = "".join(collected)
    summary = StreamSummary(
        provider=config.provider,
        model=config.model,
        mocked=False,
        request_preview=request_preview,
        full_text=full_text,
        first_token_ms=first_token_ms,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        chunk_count=chunk_count,
        input_tokens_estimate=estimate_messages_tokens(messages),
        output_tokens_estimate=estimate_tokens(full_text),
    )
    if debug:
        _debug_print_stream_result(summary, debug_label)
    yield {
        "type": "done",
        "summary": summary,
    }


def encode_sse_event(event: str, data: Any, event_id: str | None = None) -> str:
    lines: list[str] = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    for line in payload.splitlines():
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


def write_json_export(filename: str, payload: Any) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
