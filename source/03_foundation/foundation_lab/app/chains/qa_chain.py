"""
定义 foundation_lab 的最小链路。

这里用一个非常轻量的 chain 对象，把 Prompt 组装、模型调用和结果解析明确
串起来，帮助理解后续 LCEL 的角色。
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol

from app.prompts.qa_prompt import format_qa_prompt


class PromptClient(Protocol):
    """约束 chain 所依赖的客户端接口。"""

    def invoke(self, prompt: str) -> str:
        """执行一次普通调用。"""

        ...

    def stream(self, prompt: str) -> Iterator[str]:
        """执行一次流式调用。"""

        ...


def parse_text_output(text: str) -> str:
    """对模型文本输出做最小清洗。"""

    return text.strip()


class SimpleQAChain:
    """最小问答链，负责串联 prompt、client 和 parser。

    阅读这个类时，可以按下面顺序理解：
    1. 上层先把原始问题传进来
    2. chain 把问题和额外上下文组装成统一 Prompt
    3. client 负责真正“调用模型”这一步
    4. parser 对输出做最小清洗

    这就是 `prompt -> llm -> parser` 的最小版本。
    """

    def __init__(self, client: PromptClient) -> None:
        """注入一个满足协议的客户端实现。"""

        self.client = client

    def invoke(
        self,
        question: str,
        context_blocks: Sequence[str] | None = None,
        tool_result: str | None = None,
    ) -> str:
        """执行同步问答流程。

        这是最值得先读的方法，因为它完整体现了一次普通调用的顺序：
        1. 先把问题、检索结果、工具结果拼成 Prompt
        2. 再把 Prompt 交给底层 client
        3. 最后把返回文本做最小清洗
        """

        # 第一步：把离散输入收束成一个统一 Prompt，避免上层直接拼字符串。
        prompt = format_qa_prompt(question, context_blocks=context_blocks, tool_result=tool_result)
        # 第二步和第三步：调用客户端，再做最小 parser 清洗。
        return parse_text_output(self.client.invoke(prompt))

    def stream(
        self,
        question: str,
        context_blocks: Sequence[str] | None = None,
        tool_result: str | None = None,
    ) -> Iterator[str]:
        """执行流式问答流程。

        这里和 `invoke()` 的区别只在最后一步：
        Prompt 仍然要先组装好，但返回值不再是完整字符串，而是一个逐段输出的迭代器。
        """

        # 流式调用同样先固定 Prompt，保证同步和流式两条路径使用同一套输入结构。
        prompt = format_qa_prompt(question, context_blocks=context_blocks, tool_result=tool_result)
        return self.client.stream(prompt)
