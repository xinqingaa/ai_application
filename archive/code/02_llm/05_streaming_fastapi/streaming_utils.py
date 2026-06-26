"""
streaming_utils.py
第五章公共工具：provider 配置、异步聊天、流式输出、SSE 编码、会话状态

这个文件不是某个单独示例脚本的入口，而是第五章所有示例共享的“流式与 FastAPI 工具箱”。
它主要负责 6 类事情：

1. 尝试加载 `.env`，并整理统一的 provider 配置
2. 提供一次性异步聊天调用 `chat_once()`
3. 提供流式事件生成器 `stream_chat_events()`
4. 提供消息组装、历史裁剪和 system prompt 兜底
5. 提供内存会话存储，方便 FastAPI 示例演示 session/history
6. 提供 SSE 事件编码、token 估算和导出等辅助能力

阅读顺序建议：
load_env_if_possible()
-> load_provider_config()
-> build_messages_for_turn()
-> chat_once()
-> stream_chat_events()
-> InMemorySessionStore
-> encode_sse_event()

如果你在看第五章代码时有几个典型疑问：
1. “普通聊天接口和流式接口到底共用了哪些底层能力？”
2. “为什么流式接口里只返回 token/done，而完整回复仍然能写回 session？”
3. “SSE 格式是在哪里从 Python 对象变成文本协议的？”

答案基本都在这个文件里。

如果按“第 2 个脚本 / 第 3 个脚本”的主流程来对照：

1. `02_fastapi_chat.py`
   `load_provider_config()`
   -> `build_messages_for_turn()`
   -> `chat_once()`
   -> `append_assistant_message()`
   -> `InMemorySessionStore.save_history()`

2. `03_fastapi_stream.py`
   `load_provider_config()`
   -> `build_messages_for_turn()`
   -> `stream_chat_events()`
   -> `encode_sse_event()`
   -> `append_assistant_message()`
   -> `InMemorySessionStore.save_history()`

调试时最值得先看的日志点是：
- `_debug_print_start()`：请求发出前，到底带了什么 payload
- `_debug_print_result()`：普通聊天最终拿到了什么结果
- `_debug_print_stream_result()`：流式调用最终汇总了什么统计信息
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
    """作用：
    尝试加载 `.env` 环境变量，降低第五章示例脚本的环境准备成本。

    参数：
    无。若本地未安装 `python-dotenv`，则直接跳过，不影响 mock 演示。

    这也是为什么第五章示例即使没配好真实 API Key，仍然可以继续学习主流程：
    后续 `load_provider_config()` 会读到缺失的 key，然后自动落到 mock 分支。
    """
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
    """第五章统一的 provider 运行时配置对象。

    FastAPI 示例和最小流式脚本都统一依赖这个对象，
    而不是各自零散读取环境变量。
    """

    provider: str
    api_key: str | None
    base_url: str | None
    model: str
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None

    @property
    def is_ready(self) -> bool:
        """判断当前配置是否具备真实调用模型的基本条件。"""
        return bool(self.api_key)


@dataclass
class ChatUsage:
    """统一的 token 用量结构。"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatResult:
    """普通非流式聊天调用的统一结果结构。

    `02_fastapi_chat.py` 里的 `/chat` 接口最终就是围绕这个对象取值并返回 JSON。
    """

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
    """一次流式调用结束后的汇总信息。

    流式过程中会先不断产出 `token` 事件，
    最终再通过 `done` 事件把这份汇总对象交给上层。
    """

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
    """内存会话记录对象。

    第五章不引入数据库，先用这层简单结构演示：
    一个 session 里如何保存消息历史、创建时间和更新时间。
    """

    session_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    """作用：
    按 provider 名称从环境变量中整理出统一配置。

    参数：
    provider: 可选的平台名；不传时读取 `DEFAULT_PROVIDER`，默认回退到 `bailian`。

    返回：
    一个 `ProviderConfig`，供普通聊天和流式聊天两条链路共用。

    调试时要重点确认这 4 个值：
    - `provider`
    - `model`
    - `base_url`
    - `is_ready`

    因为后面是走真实模型，还是走 mock 分支，基本就在这里决定了。
    """
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
    """作用：
    生成一次聊天请求的预览对象。

    这份对象主要用于：
    1. 调试日志打印
    2. FastAPI 返回值里的 `request_preview`
    3. 对比普通请求和流式请求是否只有 `stream=True` 的区别
    """
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
    """粗略估算一段文本的 token 数。

    有 `tiktoken` 时走更准确估算；
    没装依赖时退回一个足够教学用途的近似算法。
    """
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
    """估算整段消息历史的 token 数。

    这主要用于第五章示例里的会话长度观察，
    帮助理解 history 增长后上下文成本会如何上升。
    """
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
    """按“保留最近若干条消息”的策略裁剪历史。

    system 消息始终保留，其余消息只保留最近 `keep_last_messages` 条，
    用来演示最简单的上下文窗口控制。
    """
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    return system_messages + others[-keep_last_messages:]


def ensure_system_message(messages: list[dict[str, str]], system_prompt: str | None) -> list[dict[str, str]]:
    """确保消息列表最前面总有一条 system prompt。"""
    target_prompt = (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()
    others = [item for item in messages if item["role"] != "system"]
    return [{"role": "system", "content": target_prompt}] + others


def build_messages_for_turn(
    history: list[dict[str, str]],
    user_text: str,
    system_prompt: str | None = None,
    keep_last_messages: int = 10,
) -> list[dict[str, str]]:
    """作用：
    为“当前这一轮对话”组装最终要发给模型的 messages。

    它把第五章最常见的三件事收口到一起：
    1. 给历史补上 system prompt
    2. 按最近消息策略裁剪历史
    3. 把当前用户输入追加到最后

    `02_fastapi_chat.py` 和 `03_fastapi_stream.py` 的接口都会先走这一步。

    所以当你调试“为什么普通接口和流式接口表现不一致”时，
    先检查的通常不是路由，而是这里产出的 `messages` 是否一致。
    """
    base_messages = ensure_system_message(history, system_prompt)
    base_messages = trim_messages_by_recent_messages(base_messages, keep_last_messages=keep_last_messages)
    return base_messages + [{"role": "user", "content": user_text}]


def append_assistant_message(
    messages: list[dict[str, str]],
    assistant_text: str,
    keep_last_messages: int = 10,
) -> list[dict[str, str]]:
    """把 assistant 回复追加到历史中，并再次按最近消息策略裁剪。"""
    updated = messages + [{"role": "assistant", "content": assistant_text}]
    return trim_messages_by_recent_messages(updated, keep_last_messages=keep_last_messages)


def create_session_id() -> str:
    """生成一个足够短、适合教学演示的 session_id。"""
    return uuid.uuid4().hex[:12]


class InMemorySessionStore:
    """最小内存会话存储。

    第五章重点是理解 session/history 链路，不是持久化实现，
    所以先用这层内存对象把概念跑通。
    """

    def __init__(self) -> None:
        self._store: dict[str, SessionRecord] = {}

    def get_or_create(self, session_id: str | None = None) -> SessionRecord:
        """按 session_id 获取会话；不存在时自动创建。"""
        key = session_id or create_session_id()
        if key not in self._store:
            self._store[key] = SessionRecord(session_id=key)
        return self._store[key]

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """读取某个会话当前的消息历史。"""
        return list(self._store.get(session_id, SessionRecord(session_id=session_id)).messages)

    def save_history(self, session_id: str, messages: list[dict[str, str]]) -> None:
        """覆盖保存某个会话的最新消息历史，并刷新更新时间。"""
        record = self.get_or_create(session_id)
        record.messages = list(messages)
        record.updated_at = datetime.now().isoformat()

    def dump_session(self, session_id: str) -> dict[str, Any]:
        """导出某个会话的完整快照，便于 `/sessions/{session_id}` 调试查看。"""
        record = self.get_or_create(session_id)
        return {
            "session_id": record.session_id,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "messages": record.messages,
            "estimated_tokens": estimate_messages_tokens(record.messages),
        }


def _extract_last_user(messages: list[dict[str, str]]) -> str:
    """提取最后一条 user 消息内容。"""
    for item in reversed(messages):
        if item["role"] == "user":
            return item["content"]
    return ""


def _extract_system_prompt(messages: list[dict[str, str]]) -> str:
    """提取当前消息列表中的 system prompt。"""
    for item in messages:
        if item["role"] == "system":
            return item["content"]
    return ""


def _build_mock_reply(messages: list[dict[str, str]]) -> str:
    """根据当前 messages 生成一段可读的 mock 回复。

    这样在没有真实 API Key 时，普通聊天和流式聊天都还能继续演示完整链路。
    """
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
    """作用：
    发起一次非流式异步聊天请求，并统一返回 `ChatResult`。

    这是第五章普通聊天接口的底层入口。
    `02_fastapi_chat.py` 和 `03_fastapi_stream.py` 里的普通 `/chat` 都会走这里。

    这条链路的职责是：
    1. 打印请求调试日志
    2. 根据配置决定走真实调用还是 mock 回退
    3. 收集完整文本、usage 和 elapsed_ms

    `02_fastapi_chat.py` 调试时可以把它理解成“真正访问模型的单点入口”。
    如果 `/chat` 行为异常，先看这里打印出的 `request_preview` 和最终 `raw_response_preview`。
    """
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, stream=False)
    if debug:
        _debug_print_start(config, request_preview, debug_label)
    started = time.perf_counter()

    if not config.is_ready:
        # 没有 API Key 时，非流式接口直接走 mock，方便先把会话流程、接口结构和调试信息跑通。
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
        # 这里是普通 `/chat` 路径里最核心的异步等待点：
        # FastAPI 路由会在这里等待上游 provider 返回完整响应对象。
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
    """把 mock 文本切成几段，用来模拟流式 token/chunk 到达。"""
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
    """作用：
    发起一次流式聊天，并把模型输出转换成事件流。

    这条链路不会直接返回完整文本，而是按顺序产出：
    - `{"type": "token", "delta": ...}`：一段新到达的文本
    - `{"type": "done", "summary": ...}`：整次流式调用结束后的汇总信息

    `01_stream_basic.py` 会直接消费这些事件；
    `03_fastapi_stream.py` 会再把这些事件编码成 SSE 文本返回给前端。

    所以它的定位不是“最终 HTTP 输出层”，而是“内部统一事件层”：
    上层脚本可以直接消费这些 Python 事件，再决定是打印到终端还是转成 SSE。
    """
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, stream=True)
    if debug:
        _debug_print_start(config, request_preview, debug_label)
    started = time.perf_counter()
    first_token_ms: float | None = None
    collected: list[str] = []
    chunk_count = 0

    if not config.is_ready:
        # 没有真实 key 时，仍然模拟“逐段到达”的体验，
        # 这样可以在本地完整演示 token、首字耗时和 done 事件。
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
        # 这里先异步拿到“流对象”本身；随后真正逐段等待内容，
        # 发生在下面的 `async for chunk in stream`。
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
        # OpenAI-compatible 的流式接口会不断返回 chunk；
        # 这里把每次增量内容统一整理成 token 事件交给上层。
        #
        # `03_fastapi_stream.py` 里虽然没有在消费端显式写 `await chunk`，
        # 但 `async for` 本身就在反复等待下一段 chunk 到达。
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
    """作用：
    把 Python 对象编码成一条标准 SSE 文本事件。

    例如：
    - `event: token`
    - `data: {"delta": "..."}`

    `03_fastapi_stream.py` 最终就是靠这个函数把内部事件流转成浏览器可消费的 SSE 协议文本。

    调试 `curl -N` 输出时，如果你看到的就是：
    - `id: ...`
    - `event: ...`
    - `data: ...`

    那么这些文本基本都是在这里拼出来的。
    """
    lines: list[str] = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    for line in payload.splitlines():
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


def write_json_export(filename: str, payload: Any) -> Path:
    """把 JSON 数据导出到第五章 `exports/` 目录。"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    """生成适合导出文件名的时间戳片段。"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
