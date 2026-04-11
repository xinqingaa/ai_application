"""
Run the LangChain-style path with the current foundation_lab skeleton.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.services.qa_service import build_default_service


def main() -> None:
    service = build_default_service()
    response = service.ask("Explain the LangChain abstraction boundary.", engine="langchain")
    print("=== LangChain Demo ===")
    print(f"path: {response.path}")
    print(f"engine: {response.engine}")
    print(f"answer: {response.answer}")


if __name__ == "__main__":
    main()
