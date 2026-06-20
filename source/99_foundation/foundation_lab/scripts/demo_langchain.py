"""
演示 LangChain 风格路径的最小运行方式。

这个脚本用于观察同一 service 层在 LangChain 风格客户端下的输出形态。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 允许直接从脚本目录运行，而不用先安装成包。
    sys.path.append(str(PROJECT_ROOT))

from app.services.qa_service import build_default_service


def main() -> None:
    """执行一次 LangChain 风格路径演示并打印结果。"""

    service = build_default_service()
    response = service.ask("Explain the LangChain abstraction boundary.", engine="langchain")
    print("=== LangChain Demo ===")
    print(f"path: {response.path}")
    print(f"engine: {response.engine}")
    print(f"answer: {response.answer}")


if __name__ == "__main__":
    main()
