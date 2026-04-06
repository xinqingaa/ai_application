"""
03_fastapi_stream.py
FastAPI SSE 流式聊天接口：StreamingResponse、事件编码、心跳保活

运行方式：
    uvicorn 03_fastapi_stream:app --reload --port 8000
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
app = FastAPI(title="LLM Streaming Chat API", version="0.1.0")
store = InMemorySessionStore()


class StreamChatRequest(BaseModel):
    session_id: str | None = Field(default=None)
    message: str = Field(min_length=1)
    provider: str | None = Field(default=None)
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT)
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=400, ge=1, le=4096)
    keep_last_messages: int = Field(default=10, ge=2, le=40)
    heartbeat_seconds: float = Field(default=1.5, ge=0.5, le=10.0)


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None)
    message: str = Field(min_length=1)
    provider: str | None = Field(default=None)
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT)
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=400, ge=1, le=4096)
    keep_last_messages: int = Field(default=10, ge=2, le=40)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    return store.dump_session(session_id)


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    session = store.get_or_create(request.session_id)
    history = store.get_history(session.session_id)
    messages = build_messages_for_turn(
        history=history,
        user_text=request.message,
        system_prompt=request.system_prompt,
        keep_last_messages=request.keep_last_messages,
    )
    config = load_provider_config(request.provider)
    result = await chat_once(config, messages, temperature=request.temperature, max_tokens=request.max_tokens)
    updated_history = append_assistant_message(messages, result.content, keep_last_messages=request.keep_last_messages)
    store.save_history(session.session_id, updated_history)
    return {
        "session_id": session.session_id,
        "provider": result.provider,
        "model": result.model,
        "reply": result.content,
        "mocked": result.mocked,
        "elapsed_ms": result.elapsed_ms,
        "session_estimated_tokens": estimate_messages_tokens(updated_history),
    }


async def build_sse_stream(request: StreamChatRequest) -> AsyncIterator[str]:
    session = store.get_or_create(request.session_id)
    history = store.get_history(session.session_id)
    messages = build_messages_for_turn(
        history=history,
        user_text=request.message,
        system_prompt=request.system_prompt,
        keep_last_messages=request.keep_last_messages,
    )
    config = load_provider_config(request.provider)
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    producer_done = asyncio.Event()

    async def producer() -> None:
        try:
            async for event in stream_chat_events(
                config=config,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                await queue.put(event)
        except Exception as exc:
            await queue.put({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
        finally:
            producer_done.set()

    producer_task = asyncio.create_task(producer())
    stream_id = f"{session.session_id}-{int(time.time() * 1000)}"
    assembled_parts: list[str] = []

    try:
        yield encode_sse_event(
            "start",
            {
                "session_id": session.session_id,
                "provider": config.provider,
                "model": config.model,
            },
            event_id=stream_id,
        )

        while not producer_done.is_set() or not queue.empty():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=request.heartbeat_seconds)
            except asyncio.TimeoutError:
                yield encode_sse_event("ping", {"ts": time.time()}, event_id=stream_id)
                continue

            if event["type"] == "token":
                delta = event["delta"]
                assembled_parts.append(delta)
                yield encode_sse_event("token", {"delta": delta}, event_id=stream_id)
            elif event["type"] == "done":
                summary = event["summary"]
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
                yield encode_sse_event("error", {"message": event["message"]}, event_id=stream_id)
                break
    finally:
        producer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await producer_task


@app.post("/chat/stream")
async def chat_stream(request: StreamChatRequest) -> StreamingResponse:
    return StreamingResponse(
        build_sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
