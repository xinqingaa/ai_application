"""
03_fastapi_stream.py
FastAPI SSE 流式聊天接口：StreamingResponse、事件编码、心跳保活

运行方式：
    uvicorn 03_fastapi_stream:app --reload --port 8000

这个脚本演示的是“把内部流式事件转成 SSE 返回给前端”的完整链路。
和 `02_fastapi_chat.py` 相比，最大的区别不是业务逻辑，而是返回方式：

1. 普通 `/chat`：等完整回复生成后，一次性返回 JSON
2. `/chat/stream`：边生成边推送 `start / token / ping / done / error` 事件

阅读顺序建议：
ChatRequest / StreamChatRequest
-> /chat
-> build_sse_stream()
-> /chat/stream

理解重点：
- `stream_chat_events()` 负责从模型拿内部事件
- `build_sse_stream()` 负责把内部事件转换成 SSE 对外协议
- `StreamingResponse` 负责把这个异步事件流持续推给客户端

调试方式建议：
1. 启动：`uvicorn 03_fastapi_stream:app --reload --port 8000`
2. 打开：`http://localhost:8000/docs`，先调普通 `POST /chat` 和 `GET /sessions/{session_id}`
3. 再用 `curl -N` 调 `POST /chat/stream`，因为 Swagger UI 不适合观察逐条 SSE 事件
4. 同时观察终端 `[DEBUG]` 日志，确认内部事件何时产生、何时结束
5. 流结束后再用 `GET /sessions/{session_id}`，确认完整 assistant 回复是在 `done` 后写回 history

这个脚本的主流程可以压缩成一行：
请求进入 `/chat/stream` -> `StreamingResponse(build_sse_stream(...))`
-> producer 从模型读取内部事件 -> consumer 转成 SSE -> `done` 时保存历史 -> 关闭任务
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import time
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from streaming_utils import (
    DEFAULT_SYSTEM_PROMPT,
    InMemorySessionStore,
    append_assistant_message,
    build_messages_for_turn,
    chat_once,
    encode_sse_event,
    estimate_messages_tokens,
    load_env_if_possible,
    load_provider_config,
    stream_chat_events,
)


load_env_if_possible()
# 同一个服务里同时保留普通 `/chat` 和流式 `/chat/stream`，
# 这样更容易对照“完整 JSON 返回”和“SSE 逐步返回”的差别。
app = FastAPI(title="LLM Streaming Chat API", version="0.1.0")
store = InMemorySessionStore()


class StreamChatRequest(BaseModel):
    """SSE 流式聊天接口的请求体。"""

    session_id: str | None = Field(default=None)
    message: str = Field(min_length=1)
    provider: str | None = Field(default=None)
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT)
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=400, ge=1, le=4096)
    keep_last_messages: int = Field(default=10, ge=2, le=40)
    heartbeat_seconds: float = Field(default=1.5, ge=0.5, le=10.0)


class ChatRequest(BaseModel):
    """同文件里保留的普通聊天接口请求体。

    这样你可以在同一个服务里同时对比非流式和流式两种返回方式。
    """

    session_id: str | None = Field(default=None, description="会话 ID，不传则自动创建")
    message: str = Field(min_length=1, description="用户当前消息")
    provider: str | None = Field(default=None, description="可选 provider 覆盖")
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT, description="system prompt")
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=400, ge=1, le=4096)
    keep_last_messages: int = Field(default=10, ge=2, le=40, description="保留最近消息条数")


class ChatResponse(BaseModel):
    """普通聊天接口的响应体。"""

    session_id: str
    provider: str
    model: str
    reply: str
    mocked: bool
    elapsed_ms: float
    usage: dict[str, Any] | None
    request_preview: dict[str, Any]
    session_estimated_tokens: int


ChatResponse.model_rebuild()


@app.get("/health")
async def health() -> dict[str, str]:
    """最小健康检查接口。"""
    return {"status": "ok"}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """查看某个 session 当前保存的历史记录。"""
    return store.dump_session(session_id)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """同服务下保留一个普通聊天接口，便于和 `/chat/stream` 做行为对比。

    调试建议是先把这个接口跑通，再看下面的流式接口，
    这样你会更容易分辨：哪些逻辑是“聊天本身需要的”，哪些逻辑是“SSE 才额外需要的”。
    """
    # 第 1 步：拿到一个可复用的 session_id。
    # 如果前端没传，store 会自动创建，方便你先把多轮对话跑通。
    session = store.get_or_create(request.session_id)

    # 第 2 步：读出这个 session 当前已有的历史。
    # 这里读到的是“上一轮已经确认完成”的历史，不包含本轮用户刚输入的 message。
    history = store.get_history(session.session_id)

    # 第 3 步：把历史、本轮用户输入、system prompt、裁剪策略组装成真正发给模型的 messages。
    # 这里会自动补 system prompt、裁剪历史，并把当前用户输入追加到最后。
    messages = build_messages_for_turn(
        history=history,
        user_text=request.message,
        system_prompt=request.system_prompt,
        keep_last_messages=request.keep_last_messages,
    )

    # 第 4 步：按 provider 名称整理配置，再异步等待完整模型回复。
    # 这个 `await chat_once(...)` 就是普通聊天链路里最核心的等待点。
    config = load_provider_config(request.provider)
    result = await chat_once(
        config=config,
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        debug_label="FastAPI 普通聊天",
    )

    # 第 5 步：只有拿到完整 assistant 回复后，才把这一轮真正写回 session history。
    updated_history = append_assistant_message(
        messages=messages,
        assistant_text=result.content,
        keep_last_messages=request.keep_last_messages,
    )
    store.save_history(session.session_id, updated_history)

    # 第 6 步：把底层 `ChatResult` 规整成更适合接口返回和 Swagger 展示的结构。
    usage_dict = None
    if result.usage:
        usage_dict = {
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
        }
    return ChatResponse(
        session_id=session.session_id,
        provider=result.provider,
        model=result.model,
        reply=result.content,
        mocked=result.mocked,
        elapsed_ms=result.elapsed_ms,
        usage=usage_dict,
        request_preview=result.request_preview,
        session_estimated_tokens=estimate_messages_tokens(updated_history),
    )


async def build_sse_stream(request: StreamChatRequest) -> AsyncIterator[str]:
    """作用：
    把一次流式模型调用封装成可直接返回给浏览器/前端的 SSE 文本流。

    这层做了三件核心事情：
    1. 先准备 session/history/messages
    2. 后台生产内部流式事件，前台消费并转成 SSE
    3. 在结束时保存完整 assistant 回复到 session

    你可以把它理解成“桥接层 + 调度层”：
    - 上游：`stream_chat_events()` 负责和模型 SDK 交互
    - 中间：`queue + producer` 负责把内部事件和心跳逻辑解耦
    - 下游：`yield encode_sse_event(...)` 负责把事件推给前端

    它是第五章最关键的桥接层：
    `stream_chat_events()` 给的是 Python 事件对象，
    而浏览器真正消费的是 SSE 文本协议。
    """
    # 第 1 步：准备本轮流式请求所需的会话、历史和 messages。
    session = store.get_or_create(request.session_id)
    history = store.get_history(session.session_id)
    messages = build_messages_for_turn(
        history=history,
        user_text=request.message,
        system_prompt=request.system_prompt,
        keep_last_messages=request.keep_last_messages,
    )
    config = load_provider_config(request.provider)

    # 第 2 步：建立一个队列作为“内部事件缓冲区”。
    # producer 负责往里放 token/done/error，外层 while 循环负责按节奏取出来并转成 SSE。
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    producer_done = asyncio.Event()

    async def producer() -> None:
        # producer 专门负责“向模型要流式结果”，并把内部事件放进队列。
        # 这样外层 consumer 才能独立处理 SSE 编码、心跳和客户端返回。
        try:
            async for event in stream_chat_events(
                config=config,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                debug_label="FastAPI SSE 流式聊天",
            ):
                await queue.put(event)
        except Exception as exc:
            await queue.put({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
        finally:
            producer_done.set()

    # 第 3 步：单独起一个后台任务读上游模型流。
    # 这样当前这个异步生成器就不会被上游 `async for` 完全阻塞住，
    # 才有机会在“暂时没新 token”时发 `ping` 心跳。
    producer_task = asyncio.create_task(producer())
    stream_id = f"{session.session_id}-{int(time.time() * 1000)}"

    try:
        # 第 4 步：先发一个 start 事件，告诉前端这条流已经建立。
        # 前端一般会在这里初始化当前聊天气泡、记录 session_id、切到“正在生成”状态。
        yield encode_sse_event(
            "start",
            {
                "session_id": session.session_id,
                "provider": config.provider,
                "model": config.model,
            },
            event_id=stream_id,
        )

        # 第 5 步：循环消费内部事件。
        # 如果在 `heartbeat_seconds` 时间内没等到新事件，就先发一个 `ping`，告诉前端连接还活着。
        while not producer_done.is_set() or not queue.empty():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=request.heartbeat_seconds)
            except asyncio.TimeoutError:
                # 如果一段时间没有新 token，就主动发 ping 保持连接活跃。
                yield encode_sse_event("ping", {"ts": time.time()}, event_id=stream_id)
                continue

            if event["type"] == "token":
                delta = event["delta"]
                # token 事件是面向前端最核心的增量输出，每来一段就立刻往外推。
                # 这一步不会改 session history，因为此时结果还没结束。
                yield encode_sse_event("token", {"delta": delta}, event_id=stream_id)
            elif event["type"] == "done":
                summary = event["summary"]
                # 只有流式完成后，我们才知道完整 assistant 回复是什么，
                # 所以 session history 也要等到这里再保存。
                updated_history = append_assistant_message(
                    messages=messages,
                    assistant_text=summary.full_text,
                    keep_last_messages=request.keep_last_messages,
                )
                store.save_history(session.session_id, updated_history)
                yield encode_sse_event(
                    "done",
                    {
                        "session_id": session.session_id,
                        "mocked": summary.mocked,
                        "first_token_ms": summary.first_token_ms,
                        "elapsed_ms": summary.elapsed_ms,
                        "chunk_count": summary.chunk_count,
                        "input_tokens_estimate": summary.input_tokens_estimate,
                        "output_tokens_estimate": summary.output_tokens_estimate,
                        "session_estimated_tokens": estimate_messages_tokens(updated_history),
                    },
                    event_id=stream_id,
                )
            elif event["type"] == "error":
                # 错误也通过 SSE 事件向前端显式传递，避免客户端一直等待超时。
                yield encode_sse_event("error", {"message": event["message"]}, event_id=stream_id)
                break
    finally:
        # 第 6 步：无论是正常结束、异常结束，还是客户端提前断开，
        # 都要确保后台 producer 任务被取消并清理干净。
        producer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await producer_task


@app.post("/chat/stream")
async def chat_stream(request: StreamChatRequest) -> StreamingResponse:
    """SSE 流式聊天接口。

    返回值不是普通 JSON，而是 `StreamingResponse`，
    其内容来源于 `build_sse_stream()` 这个异步生成器。

    这里本身几乎没有业务逻辑，真正的主流程都在 `build_sse_stream()` 里。
    所以调试这个接口时，优先读 `build_sse_stream()`，再看 `streaming_utils.py`。
    """
    return StreamingResponse(
        build_sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
