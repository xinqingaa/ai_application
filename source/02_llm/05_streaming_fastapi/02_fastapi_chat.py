"""
02_fastapi_chat.py
非流式 FastAPI 聊天接口：请求体、会话管理、普通 JSON 返回

运行方式：
    uvicorn 02_fastapi_chat:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
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
    estimate_messages_tokens,
    load_env_if_possible,
    load_provider_config,
)


load_env_if_possible()
app = FastAPI(title="LLM Chat API", version="0.1.0")
store = InMemorySessionStore()


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="会话 ID，不传则自动创建")
    message: str = Field(min_length=1, description="用户当前消息")
    provider: str | None = Field(default=None, description="可选 provider 覆盖")
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT, description="system prompt")
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=400, ge=1, le=4096)
    keep_last_messages: int = Field(default=10, ge=2, le=40, description="保留最近消息条数")


class ChatResponse(BaseModel):
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
    return {"status": "ok"}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    return store.dump_session(session_id)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session = store.get_or_create(request.session_id)
    history = store.get_history(session.session_id)
    messages = build_messages_for_turn(
        history=history,
        user_text=request.message,
        system_prompt=request.system_prompt,
        keep_last_messages=request.keep_last_messages,
    )
    config = load_provider_config(request.provider)
    result = await chat_once(
        config=config,
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    updated_history = append_assistant_message(
        messages=messages,
        assistant_text=result.content,
        keep_last_messages=request.keep_last_messages,
    )
    store.save_history(session.session_id, updated_history)
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
