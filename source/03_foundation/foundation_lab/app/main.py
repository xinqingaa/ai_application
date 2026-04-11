"""
foundation_lab 的最小 API 入口。

可以把这个文件理解成“HTTP 请求进入项目后的第一站”。

推荐阅读顺序：
1. 先看 `create_app()`，理解接口是怎么挂上的
2. 再看 `/ask`，理解普通请求如何进入 service
3. 再看 `/ask/stream`，理解流式请求如何进入 service
4. 最后看 `_stream_answer()`，理解 API 和 service 的衔接点

这个文件的职责要刻意保持很薄：
- 负责收请求
- 负责取参数
- 负责调 service
- 负责把结果转成 HTTP 响应

真正的业务判断应该留在 `qa_service.py`，而不是堆在这里。
"""

from __future__ import annotations

from collections.abc import Iterator

from app.observability.logger import setup_logger
from app.services.qa_service import build_default_service

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
except ImportError:  # pragma: no cover - optional dependency for later phases
    # FastAPI 在当前阶段是可选依赖，因此未安装时先允许模块被导入。
    FastAPI = None
    StreamingResponse = None


logger = setup_logger()
service = build_default_service()


def _stream_answer(question: str, engine: str) -> Iterator[str]:
    """把 service 的流式结果转成接口可直接返回的迭代器。

    请求流转顺序是：
    1. `/ask/stream` 路由拿到 HTTP 请求
    2. 路由调用这个函数
    3. 这个函数再调用 `service.stream()`
    4. service 返回的片段被逐个 yield 给 StreamingResponse
    """

    # 这里不做业务判断，只负责把 service 的输出继续向上转交给接口层。
    for chunk in service.stream(question, engine=engine):
        yield chunk


def create_app() -> "FastAPI":
    """创建 FastAPI 应用，并挂载最小健康检查与问答接口。

    这个函数相当于整个 API 层的装配入口：
    - 创建 app
    - 定义路由
    - 把路由和 service 连接起来
    """

    if FastAPI is None or StreamingResponse is None:
        raise RuntimeError("fastapi is not installed. Install fastapi and uvicorn before running the API.")

    app = FastAPI(title="foundation_lab", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        """提供最简单的健康检查接口。"""

        return {"status": "ok"}

    @app.post("/ask")
    async def ask(payload: dict[str, str]) -> dict[str, object]:
        """返回一次完整的非流式问答结果。

        这条路由最适合用来理解“请求是怎么流进 service 的”：
        1. FastAPI 把请求体解析成 `payload`
        2. 路由从 `payload` 里取出 `question` 和 `engine`
        3. 路由把参数交给 `service.ask()`
        4. service 内部再决定走 plain / retrieval / tool
        5. 路由把 `AskResponse` 转成可返回的字典

        注意：这里不负责判断业务路径，只负责参数提取和响应封装。
        """

        # 第一步：从 HTTP 请求体中取出最小必要参数。
        question = payload.get("question", "").strip()
        engine = payload.get("engine", "langchain").strip() or "langchain"
        # 第二步：把业务处理交给 service，而不是在 API 层写分支逻辑。
        response = service.ask(question=question, engine=engine)
        # 第三步：记录一次请求的最小日志，帮助观察走了哪条路径。
        logger.info("ask path=%s engine=%s", response.path, response.engine)
        # 第四步：把 service 返回对象压平成 HTTP 更容易消费的结构。
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
        """返回最小流式问答响应。

        这条路由和 `/ask` 的差别主要在返回方式：
        - `/ask` 会等 service 产出完整结果后一次性返回
        - `/ask/stream` 会把结果片段持续往外发送

        但两者的核心思想相同：
        API 层仍然不做业务编排，只负责把请求转交给 service。
        """

        # 先提取请求参数，保持和普通问答接口一致的输入风格。
        question = payload.get("question", "").strip()
        engine = payload.get("engine", "langchain").strip() or "langchain"
        logger.info("ask_stream engine=%s", engine)
        # 再把流式输出包装成 StreamingResponse，交给 HTTP 层持续发送。
        return StreamingResponse(_stream_answer(question, engine), media_type="text/plain")

    return app


# 模块被导入时，如果 FastAPI 已安装，就直接暴露 `app` 供 uvicorn 使用。
app = create_app() if FastAPI is not None and StreamingResponse is not None else None
