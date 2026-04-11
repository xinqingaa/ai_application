"""
对照 native 与 LangChain 风格两条路径的输出。

这个脚本帮助你理解：service 和 prompt 结构相同，但底层客户端可以替换。
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
    """执行一次双路径对照输出。"""

    question = "What is foundation_lab validating at this stage?"
    service = build_default_service()
    native = service.ask(question, engine="native")
    langchain = service.ask(question, engine="langchain")

    print("=== Native ===")
    print(native.answer)
    print()
    print("=== LangChain ===")
    print(langchain.answer)


if __name__ == "__main__":
    main()
