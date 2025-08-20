#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.reasoning.instruction_builder import InstructionBuilder


class TestInstructionBuilderWithGemini(unittest.TestCase):
    def setUp(self):
        # 保证最小配置满足加载
        os.environ.setdefault("GEMINI_API_KEY", "test-key")

    def test_build_uses_gemini_and_parses_json(self):
        # 构造一个假的 genai 模块并打桩
        class _Resp:
            def __init__(self, text: str):
                self.text = text

        class _Model:
            def generate_content(self, prompt: str):
                return _Resp(json.dumps({
                    "action": "navigate",
                    "value": "https://www.jd.com",
                    "description": "导航到示例站"
                }))

        fake_genai = SimpleNamespace(
            configure=lambda api_key=None: None,
            GenerativeModel=lambda name=None: _Model()
        )

        with patch("src.reasoning.instruction_builder.genai", fake_genai):
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

    def test_build_without_api_key_uses_stubbed_llm(self):
        # 移除 API Key
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]

        builder = InstructionBuilder()
        page_data = {"url": "about:blank", "title": "空白", "elements": [], "functional_areas": [], "page_type": "generic"}

        # 直接打桩 _call_llm，模拟模型输出
        with patch.object(builder, "_call_llm", return_value={
            "steps": [
                {"action": "wait", "value": 500, "description": "等待页面加载"}
            ],
            "description": "降级等待"
        }):
            out = builder.build("搜索iPhone", page_data, session_state={})

        self.assertIn("steps", out)
        self.assertGreater(len(out["steps"]), 0)


if __name__ == "__main__":
    unittest.main()


