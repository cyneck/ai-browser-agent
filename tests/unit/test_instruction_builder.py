#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
指令构建器单元测试

注意：此为单元测试，使用mock对象模拟LLM服务，
以隔离测试InstructionBuilder的逻辑功能，而非测试与LLM的集成。
如需测试真实LLM环境，请参考tests/integration/test_reasoning_integration.py
"""

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
        """测试使用Gemini API构建指令并解析JSON"""
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
            self.assertEqual(out.get("description"), "导航到示例站")

    def test_build_handles_gemini_api_error(self):
        """测试处理Gemini API错误"""
        def raise_exception(*args, **kwargs):
            raise Exception("API调用失败")

        fake_genai = SimpleNamespace(
            configure=lambda api_key=None: None,
            GenerativeModel=lambda name=None: SimpleNamespace(
                generate_content=raise_exception
            )
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
            # 应该返回错误指令
            self.assertIsInstance(out, dict)
            self.assertEqual(out.get("action"), "error")
            self.assertIn("API调用失败", out.get("message", ""))

    def test_build_handles_invalid_json_response(self):
        """测试处理无效的JSON响应"""
        class _Resp:
            def __init__(self, text: str):
                self.text = text

        class _Model:
            def generate_content(self, prompt: str):
                return _Resp('{"action": "navigate", "value": "https://www.jd.com"')  # 无效JSON，缺少闭合括号

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
            # 应该返回错误指令
            self.assertIsInstance(out, dict)
            self.assertEqual(out.get("action"), "error")
            self.assertIn("JSON解析失败", out.get("message", ""))

    def test_build_with_empty_user_text(self):
        """测试使用空用户文本构建指令"""
        builder = InstructionBuilder()
        page_data = {
            "url": "about:blank",
            "title": "空白",
            "elements": [],
            "functional_areas": [],
            "page_type": "generic",
        }
        out = builder.build("", page_data, session_state={})
        # 应该返回错误指令
        self.assertIsInstance(out, dict)
        self.assertEqual(out.get("action"), "error")
        self.assertIn("用户输入为空", out.get("message", ""))


if __name__ == "__main__":
    unittest.main()