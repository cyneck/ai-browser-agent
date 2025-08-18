#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.action.safety_validator import SafetyValidator


class TestSafetyValidator(unittest.TestCase):
    def setUp(self):
        self.validator = SafetyValidator([
            "navigate", "click", "type", "select", "wait", "screenshot",
            "extract", "scroll", "back", "forward", "refresh", "close", "error"
        ])

    def test_disallow_unsupported_action(self):
        with self.assertRaises(ValueError):
            self.validator.validate_and_sanitize({"action": "eval"})

    def test_sanitize_selector_and_value(self):
        instr = {"action": "type", "selector": "input[name=\"__proto__\"]", "value": "import os\nvalue", "description": "desc"}
        out = self.validator.validate_and_sanitize(instr)
        self.assertNotIn("__proto__", out["selector"])  # 双下划线被降级
        self.assertNotIn("import", out["value"])  # import 被去除

    def test_url_whitelist_all(self):
        instr = {"action": "navigate", "value": "https://example.com"}
        out = self.validator.validate_and_sanitize(instr)
        self.assertEqual(out["value"], "https://example.com")


if __name__ == "__main__":
    unittest.main()


