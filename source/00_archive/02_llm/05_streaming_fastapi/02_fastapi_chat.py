"""
02_fastapi_chat.py
非流式 FastAPI 聊天接口：请求体、会话管理、普通 JSON 返回

运行方式：
    uvicorn 02_fastapi_chat:app --reload --port 8000

这个脚本演示的是第五章里“先把普通聊天接口跑通”的那一层。
它不会流式返回 token，而是先把这条基础链路固定下来：

1. 接收请求体 `ChatRequest`
2. 取出或创建 `session_id`
3. 读取已有 history
4. 组装本轮要发给模型的 messages
5. 调 `chat_once()` 拿到完整回复
6. 把 assistant 回复写回 history
7. 返回 JSON 给前端，同时附带调试信息和 token 估算

理解这个脚本后，再看 `03_fastapi_stream.py` 会更容易，
因为流式接口本质上只是把第 5 步和第 7 步换成了“逐步推送事件”。

阅读顺序建议：
1. `ChatRequest` / `ChatResponse`
2. `/chat`
3. `/sessions/{session_id}`
4. 回头对照 `streaming_utils.py` 里的 `build_messages_for_turn()` 和 `chat_once()`

调试方式建议：
1. 先启动：`uvicorn 02_fastapi_chat:app --reload --port 8000`
2. 打开：`http://localhost:8000/docs`
3. 先调 `POST /chat`，看返回里的 `session_id / request_preview / session_estimated_tokens`
4. 再调 `GET /sessions/{session_id}`，确认这一轮 assistant 回复是否真的写回 history
5. 同时观察终端里的 `[DEBUG]` 日志，理解请求是怎么发给模型的

这个脚本的主流程可以压缩成一行：
请求进入 `/chat` -> 读取会话 -> 组装 messages -> `await chat_once()` -> 保存历史 -> 返回 JSON
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
# 这一章先用一个最小 FastAPI app 和内存 store，把“会话 + 调用模型 + 返回结果”讲清楚。
app = FastAPI(title="LLM Chat API", version="0.1.0")
store = InMemorySessionStore()


class ChatRequest(BaseModel):
    """普通聊天接口的请求体。"""

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
    """普通非流式聊天接口。

    处理顺序是：
    1. 拿 session
    2. 读取 history
    3. 组装本轮 messages
    4. 调模型得到完整回复
    5. 把 assistant 回复写回 history
    6. 把结果和调试信息一起返回给前端
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
    # 这个 `await chat_once(...)` 就是这个脚本里最核心的异步等待点：
    # 路由之所以定义成 `async def`，主要就是为了在这里等待真实网络请求完成。
    config = load_provider_config(request.provider)
    result = await chat_once(
        config=config,
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        debug_label="FastAPI 普通聊天",
    )

    # 第 5 步：只有当完整 assistant 回复已经拿到，才写回会话历史。
    # 非流式接口没有“半成品消息”这个概念，所以保存时机很直接：结果完整返回之后再落 history。
    # 只有拿到完整 assistant 回复后，才把这一轮真正写回 session history。
    updated_history = append_assistant_message(
        messages=messages,
        assistant_text=result.content,
        keep_last_messages=request.keep_last_messages,
    )
    store.save_history(session.session_id, updated_history)

    # 第 6 步：把底层 `ChatResult` 规整成更适合接口返回和 Swagger 展示的 JSON 结构。
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
