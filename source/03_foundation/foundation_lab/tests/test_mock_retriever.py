from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.retrievers.mock_retriever import MockRetriever


class MockRetrieverTest(unittest.TestCase):
    def test_retrieve_returns_service_document(self) -> None:
        retriever = MockRetriever()
        documents = retriever.retrieve("service boundary")
        titles = [item.title for item in documents]
        self.assertIn("Service Layer Boundary", titles)


if __name__ == "__main__":
    unittest.main()
