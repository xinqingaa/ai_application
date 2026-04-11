"""
原生 SDK 客户端占位实现。

这个文件当前不接真实 provider，而是先固定原生调用应承担的边界：
初始化、普通调用、流式调用、结构化输出示例。
"""

from __future__ import annotations

from collections.abc import Iterator

from app.config import Settings, get_settings


class NativeLLMClient:
    """
    A native client skeleton.

    This class is intentionally simple for the current phase. When real provider
    integration starts, replace the mock branch with the actual SDK call.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """保存运行配置，供后续真实 SDK 初始化复用。"""

        self.settings = settings or get_settings()

    @property
    def mocked(self) -> bool:
        """判断当前是否应该走 mock 路径。"""

        return self.settings.use_mock_when_unconfigured or not self.settings.api_key

    def invoke(self, prompt: str) -> str:
        """执行一次普通文本调用。"""

        if self.mocked:
            return self._mock_response(prompt)
        return "Native provider integration has not been implemented yet."

    def stream(self, prompt: str) -> Iterator[str]:
        """用最简单的分词方式模拟流式输出。"""

        text = self.invoke(prompt)
        for token in text.split():
            yield f"{token} "

    def structured_invoke(self, question: str) -> dict[str, str | bool]:
        """演示未来结构化输出会通过什么接口暴露。"""

        return {
            "question": question,
            "engine": "native",
            "mocked": self.mocked,
            "summary": self.invoke(f"Summarize the question: {question}"),
        }

    def _mock_response(self, prompt: str) -> str:
        """在未接真实模型前，返回可观察的占位结果。"""

        preview = " ".join(prompt.split())[:220]
        return (
            "Native mock response. "
            "This output proves the service layer and prompt pipeline are wired. "
            f"Prompt preview: {preview}"
        )
