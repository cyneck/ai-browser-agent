#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.action.executor import ActionExecutor


class TestActionExecutor(unittest.TestCase):
    def setUp(self):
        self.mock_page = MagicMock()
        # locator/操作直接返回可用的 mock
        loc = MagicMock()
        self.mock_page.locator.return_value = loc
        loc.click.return_value = None
        loc.fill.return_value = None
        loc.select_option.return_value = None
        self.executor = ActionExecutor(self.mock_page)

    def test_get_supported_actions(self):
        actions = self.executor.get_supported_actions()
        self.assertIn("click", actions)
        self.assertIn("navigate", actions)

    def test_execute_click(self):
        result = self.executor.execute({
            "action": "click",
            "selector": "button#ok",
            "description": "点击确定"
        }, session_state={})
        self.assertTrue(result.get("success"))

    def test_execute_navigate(self):
        result = self.executor.execute({
            "action": "navigate",
            "value": "https://example.com",
            "description": "去示例站"
        }, session_state={})
        self.assertIn("message", result)


if __name__ == "__main__":
    unittest.main()


