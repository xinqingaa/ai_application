"""FastAPI SSE demo for 02_llm/04."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from llm_core import ConversationBuffer, LLMClient, encode_sse

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[2]
SAMPLES_PATH = REPO_ROOT / "source" / "demos" / "02_first_chat" / "samples.json"
INDEX_PATH = APP_DIR / "index.html"

DEFAULT_SYSTEM_PROMPT = (
    "你是研发团队的需求评审助手。你只根据用户提供的需求内容分析，"
    "用简洁中文输出研发风险、需要补充的信息和下一步建议。"
)

app = FastAPI(title="02 LLM Streaming API", version="0.1.0")
_conversations: dict[str, ConversationBuffer] = {}


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _load_sample(sample_id: str) -> dict:
    samples = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    by_id = {sample["id"]: sample for sample in samples}
    if sample_id not in by_id:
        valid = ", ".join(sorted(by_id))
        raise HTTPException(status_code=404, detail=f"未知样例 {sample_id!r}，可选：{valid}")
    return by_id[sample_id]


def _conversation_for(session_id: str) -> ConversationBuffer:
    if session_id not in _conversations:
        _conversations[session_id] = ConversationBuffer(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            max_messages=8,
        )
    return _conversations[session_id]


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "app": "02_llm_streaming_api"})


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(INDEX_PATH)


@app.get("/ui", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse(INDEX_PATH)


@app.get("/api/review/stream")
def stream_review(
    sample_id: str = Query("S2"),
    session_id: str = Query("demo"),
    config_ref: str = Query("chat.dev_chat"),
    temperature: float = Query(0),
) -> StreamingResponse:
    _load_env()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise HTTPException(status_code=500, detail="未配置 OPENAI_API_KEY")

    sample = _load_sample(sample_id)
    history = _conversation_for(session_id)
    user_content = sample["user_content"]
    history.add_user(user_content)
    messages = history.to_messages()
    client = LLMClient.from_default_config()
    run_id = f"{session_id}-{sample_id}-{uuid4().hex[:8]}"

    def event_stream() -> Iterator[str]:
        final_content = ""
        for event in client.stream_chat(
            messages,
            config_ref,
            temperature=temperature,
            run_id=run_id,
        ):
            if event.type == "message_done" and event.content:
                final_content = event.content
            yield encode_sse(event)
        if final_content:
            history.add_assistant(final_content)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
