from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.tools.mock_tools import lookup_rule, run_calculator


class MockToolsTest(unittest.TestCase):
    def test_calculator_returns_expected_result(self) -> None:
        result = run_calculator("2 + 3 * 4")
        self.assertEqual(result.output, "14")

    def test_rule_lookup_returns_quality_rule(self) -> None:
        result = lookup_rule("quality")
        self.assertIn("module boundaries", result.output)


if __name__ == "__main__":
    unittest.main()
