"""
chat_api.py
第七章综合项目：把统一服务层同时暴露为普通聊天 API 和 SSE 流式聊天 API

运行方式：
    uvicorn chat_api:app --reload --port 8000
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    # 直接运行当前文件时，确保可以导入同目录下的服务层模块。
    sys.path.append(str(CURRENT_DIR))

from llm_service import ProjectLLMService, encode_sse_event, load_env_if_possible


load_env_if_possible()
app = FastAPI(title="LLM Project API", version="0.1.0")
service = ProjectLLMService()


class ChatRequest(BaseModel):
    """API 请求体：既包含当前消息，也允许覆盖部分 session 配置。"""

    session_id: str | None = Field(default=None)
    message: str = Field(min_length=1)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    system_prompt: str | None = Field(default=None)
    json_mode: bool | None = Field(default=None)
    stream_mode: bool | None = Field(default=None)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)


@app.get("/health")
async def health() -> dict[str, str]:
    """最小健康检查接口。"""
    return {"status": "ok"}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """查看某个 session 当前累积出来的状态快照。"""
    return service.session_snapshot(session_id)


def apply_request_settings(request: ChatRequest) -> str:
    """把请求里的 provider / model / mode 等设置同步到目标 session。"""
    session = service.get_or_create_session(request.session_id)
    updates: dict[str, Any] = {}
    if request.provider:
        config = service.resolve_config(request.provider, model_override=request.model)
        updates["provider"] = config.provider
        updates["model"] = request.model or config.model
    elif request.model:
        updates["model"] = request.model
    if request.system_prompt is not None:
        updates["system_prompt"] = request.system_prompt
    if request.json_mode is not None:
        updates["json_mode"] = request.json_mode
    if request.stream_mode is not None:
        updates["stream_mode"] = request.stream_mode
    if request.temperature is not None:
        updates["temperature"] = request.temperature
    if request.max_tokens is not None:
        updates["max_tokens"] = request.max_tokens
    if updates:
        session = service.update_session_settings(session.session_id, **updates)
    return session.session_id


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """普通聊天接口：直接返回完整 `TurnResult`。"""
    session_id = apply_request_settings(request)
    result = service.chat(session_id, request.message, quota_subject=session_id)
    return asdict(result)


def build_sse_stream(session_id: str, message: str) -> Iterator[str]:
    """把服务层事件流翻译成 SSE 文本流。"""
    stream_id = f"{session_id}-stream"
    for event in service.stream_chat(session_id, message, quota_subject=session_id):
        # API 层不创造业务事件，只负责把服务层事件编码成 SSE 协议。
        if event["type"] == "start":
            yield encode_sse_event("start", event, event_id=stream_id)
        elif event["type"] == "token":
            yield encode_sse_event("token", {"delta": event["delta"]}, event_id=stream_id)
        elif event["type"] == "done":
            yield encode_sse_event("done", event["result"], event_id=stream_id)
        elif event["type"] == "error":
            yield encode_sse_event("error", event["error"], event_id=stream_id)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """流式聊天接口：把统一服务层包装成 SSE 响应。"""
    session_id = apply_request_settings(request)
    return StreamingResponse(
        build_sse_stream(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
