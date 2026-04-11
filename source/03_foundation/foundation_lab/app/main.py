"""
Minimal API entrypoint for foundation_lab.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.observability.logger import setup_logger
from app.services.qa_service import build_default_service

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
except ImportError:  # pragma: no cover - optional dependency for later phases
    FastAPI = None
    StreamingResponse = None


logger = setup_logger()
service = build_default_service()


def _stream_answer(question: str, engine: str) -> Iterator[str]:
    for chunk in service.stream(question, engine=engine):
        yield chunk


def create_app() -> "FastAPI":
    if FastAPI is None or StreamingResponse is None:
        raise RuntimeError("fastapi is not installed. Install fastapi and uvicorn before running the API.")

    app = FastAPI(title="foundation_lab", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask")
    async def ask(payload: dict[str, str]) -> dict[str, object]:
        question = payload.get("question", "").strip()
        engine = payload.get("engine", "langchain").strip() or "langchain"
        response = service.ask(question=question, engine=engine)
        logger.info("ask path=%s engine=%s", response.path, response.engine)
        return {
            "question": response.question,
            "answer": response.answer,
            "path": response.path,
            "engine": response.engine,
            "mocked": response.mocked,
            "used_documents": [item.title for item in response.used_documents],
            "used_tool": response.used_tool.tool_name if response.used_tool else None,
        }

    @app.post("/ask/stream")
    async def ask_stream(payload: dict[str, str]) -> "StreamingResponse":
        question = payload.get("question", "").strip()
        engine = payload.get("engine", "langchain").strip() or "langchain"
        logger.info("ask_stream engine=%s", engine)
        return StreamingResponse(_stream_answer(question, engine), media_type="text/plain")

    return app


app = create_app() if FastAPI is not None and StreamingResponse is not None else None
