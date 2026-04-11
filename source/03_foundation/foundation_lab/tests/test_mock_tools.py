"""测试 mock tools 的最小行为是否稳定。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 允许直接运行当前测试文件。
    sys.path.append(str(PROJECT_ROOT))

from app.tools.mock_tools import lookup_rule, run_calculator


class MockToolsTest(unittest.TestCase):
    """验证工具层的核心占位功能。"""

    def test_calculator_returns_expected_result(self) -> None:
        """计算器工具应返回正确的四则运算结果。"""

        result = run_calculator("2 + 3 * 4")
        self.assertEqual(result.output, "14")

    def test_rule_lookup_returns_quality_rule(self) -> None:
        """规则查询工具应返回预置质量规范文本。"""

        result = lookup_rule("quality")
        self.assertIn("module boundaries", result.output)


if __name__ == "__main__":
    unittest.main()
