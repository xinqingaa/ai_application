"""测试 native 客户端在 mock 模式下的最小行为。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 允许直接运行当前测试文件。
    sys.path.append(str(PROJECT_ROOT))

from app.config import Settings
from app.llm.client_native import NativeLLMClient


class NativeClientTest(unittest.TestCase):
    """验证 native 客户端在教学阶段的稳定 mock 能力。"""

    def setUp(self) -> None:
        """构造一份固定走 mock 的最小配置。"""

        self.client = NativeLLMClient(Settings(provider="mock"))

    def test_invoke_returns_mock_response(self) -> None:
        """普通调用应返回可观察的 mock 文本。"""

        result = self.client.invoke("Explain the service layer.")
        self.assertIn("Native mock response.", result)

    def test_structured_invoke_returns_required_fields(self) -> None:
        """结构化调用应至少暴露统一字段。"""

        result = self.client.structured_invoke("What is a retriever?")
        self.assertEqual(result["engine"], "native")
        self.assertTrue(result["mocked"])
        self.assertIn("summary", result)
        self.assertIn("category", result)

    def test_stream_returns_incremental_chunks(self) -> None:
        """流式调用应能返回至少一个片段。"""

        chunks = list(self.client.stream("Explain the chain structure."))
        self.assertTrue(chunks)
        self.assertTrue(all(isinstance(item, str) for item in chunks))


if __name__ == "__main__":
    unittest.main()
