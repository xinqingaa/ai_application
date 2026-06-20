"""
LangChain 风格客户端占位实现。

当前先不引入真实 LangChain 依赖，只保留未来 `prompt -> llm -> parser`
链路的替换位置，方便后续逐步落地。
"""

from __future__ import annotations

from collections.abc import Iterator

from app.config import Settings, get_settings


class LangChainLLMClient:
    """
    A LangChain-facing placeholder.

    Real LangChain objects are intentionally not imported yet. This file fixes the
    boundary and leaves a stable replacement point for the next implementation step.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """保存运行配置，后续接真实 LangChain 模型时直接复用。"""

        self.settings = settings or get_settings()

    @property
    def mocked(self) -> bool:
        """当前版本固定走 mock，强调这是链路占位而非真实实现。"""

        return True

    def invoke(self, prompt: str) -> str:
        """模拟一次 LangChain 风格的链式调用结果。"""

        preview = " ".join(prompt.split())[:220]
        return (
            "LangChain mock response. "
            "This output stands in for prompt -> llm -> parser composition. "
            f"Prompt preview: {preview}"
        )

    def stream(self, prompt: str) -> Iterator[str]:
        """模拟链式调用下的流式输出。"""

        text = self.invoke(prompt)
        for token in text.split():
            yield f"{token} "
