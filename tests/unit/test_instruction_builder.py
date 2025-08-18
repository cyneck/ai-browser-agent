#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.reasoning.instruction_builder import InstructionBuilder


class TestInstructionBuilderWithGemini(unittest.TestCase):
    def setUp(self):
        # 保证最小配置满足加载
        os.environ.setdefault("GEMINI_API_KEY", "test-key")

    @patch("src.reasoning.instruction_builder.genai.GenerativeModel")
    @patch("src.reasoning.instruction_builder.genai.configure")
    def test_build_uses_gemini_and_parses_json(self, mock_configure, mock_model_cls):
        # 模拟 Gemini 返回 JSON 文本
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text=json.dumps({
            "action": "navigate",
            "value": "https://www.jd.com",
            "description": "导航到示例站"
        }))
        mock_model_cls.return_value = mock_model

        builder = InstructionBuilder()
        page_data = {
            "url": "about:blank",
            "title": "空白",
            "elements": [],
            "functional_areas": [],
            "page_type": "generic",
        }
        out = builder.build("打开示例站", page_data, session_state={})
        self.assertIsInstance(out, dict)
        self.assertEqual(out.get("action"), "navigate")
        self.assertEqual(out.get("value"), "https://www.jd.com")

    def test_build_without_api_key_falls_back(self):
        # 移除 API Key 触发降级路径
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        builder = InstructionBuilder()
        page_data = {"url": "about:blank", "title": "空白", "elements": [], "functional_areas": [], "page_type": "generic"}
        out = builder.build("搜索iPhone", page_data, session_state={})
        # 降级路径应返回多步 steps
        self.assertIn("steps", out)
        self.assertGreater(len(out["steps"]), 0)


if __name__ == "__main__":
    unittest.main()


