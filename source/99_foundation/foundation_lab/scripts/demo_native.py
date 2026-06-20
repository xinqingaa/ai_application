"""
演示 native 路径的最小运行方式。

这个脚本负责展示三件事：
1. service 层如何调度到 native 客户端
2. native 客户端如何暴露结构化输出接口
3. native 客户端如何暴露流式输出接口
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 允许直接从脚本目录运行，而不用先安装成包。
    sys.path.append(str(PROJECT_ROOT))

from app.llm.client_native import NativeLLMClient
from app.services.qa_service import build_default_service


def main() -> None:
    """执行 native 路径的普通、结构化和流式三种最小演示。"""

    service = build_default_service()
    client = NativeLLMClient()

    # 第一段：从 service 层进入，观察完整请求如何被编排到 native 链路。
    response = service.ask("What is the service layer responsible for?", engine="native")
    print("=== Native Demo ===")
    print(f"path: {response.path}")
    print(f"engine: {response.engine}")
    print(f"mocked: {response.mocked}")
    print(f"answer: {response.answer}")

    # 第二段：直接调用 client，观察原生客户端层的结构化输出接口长什么样。
    structured = client.structured_invoke("What is the difference between a retriever and a tool?")
    print("\n=== Native Structured Demo ===")
    print(structured)

    # 第三段：直接调用 client，观察流式输出会如何逐片返回。
    print("\n=== Native Stream Demo ===")
    stream_prompt = "Explain why the service layer should not live in the API layer."
    for chunk in client.stream(stream_prompt):
        print(chunk, end="")
    print()


if __name__ == "__main__":
    main()
