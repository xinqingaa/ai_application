"""测试 mock retriever 的最小命中逻辑。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 允许直接运行当前测试文件。
    sys.path.append(str(PROJECT_ROOT))

from app.retrievers.mock_retriever import MockRetriever


class MockRetrieverTest(unittest.TestCase):
    """验证关键词检索是否能返回预期文档。"""

    def test_retrieve_returns_service_document(self) -> None:
        """查询 service 相关问题时，应命中 service 边界文档。"""

        retriever = MockRetriever()
        documents = retriever.retrieve("service boundary")
        titles = [item.title for item in documents]
        self.assertIn("Service Layer Boundary", titles)


if __name__ == "__main__":
    unittest.main()
