"""测试 Prompt 组装后的基础结构是否完整。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 允许直接运行当前测试文件。
    sys.path.append(str(PROJECT_ROOT))

from app.prompts.qa_prompt import format_qa_prompt


class PromptFormatTest(unittest.TestCase):
    """验证 Prompt 中的核心区块是否都被正确拼接。"""

    def test_prompt_contains_required_sections(self) -> None:
        """检查 Prompt 必要标题和问题内容是否存在。"""

        prompt = format_qa_prompt(
            question="What is a retriever?",
            context_blocks=["Retriever returns related documents."],
            tool_result="No tool used.",
        )
        self.assertIn("System Instruction:", prompt)
        self.assertIn("Context:", prompt)
        self.assertIn("Tool Result:", prompt)
        self.assertIn("User Question:", prompt)
        self.assertIn("What is a retriever?", prompt)


if __name__ == "__main__":
    unittest.main()
