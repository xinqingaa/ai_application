"""
Compare native and LangChain-style outputs using the same service layer.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.services.qa_service import build_default_service


def main() -> None:
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
