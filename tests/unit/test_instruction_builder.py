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
        with patch("src.reasoning.instruction_builder.get_llm_manager") as mock_get_llm_manager, \
             patch("src.reasoning.instruction_builder.PromptManager") as mock_prompt_manager, \
             patch("src.reasoning.instruction_builder.PluginManager") as mock_plugin_manager:
            
            # 创建模拟的LLM管理器
            mock_llm_manager = MagicMock()
            mock_llm_manager.get_available_providers.return_value = ["gemini"]
            mock_get_llm_manager.return_value = mock_llm_manager
            
            # 模拟call_llm方法
            mock_llm_manager.call_llm.return_value = {
                "text": json.dumps({
                    "action": "navigate",
                    "value": "https://www.jd.com",
                    "description": "导航到示例站"
                })
            }
            
            # 模拟PromptManager
            mock_prompt_manager_instance = MagicMock()
            mock_prompt_manager_instance.build_complete_prompt.return_value = "测试提示词"
            mock_prompt_manager.return_value = mock_prompt_manager_instance
            
            # 模拟PluginManager
            mock_plugin_manager_instance = MagicMock()
            mock_plugin_manager_instance.build_instruction_with_fallback.return_value = None
            mock_plugin_manager.return_value = mock_plugin_manager_instance
            
            # 模拟验证方法
            with patch.object(InstructionBuilder, '_validate_instruction') as mock_validate:
                mock_validate.return_value = {
                    "action": "navigate",
                    "value": "https://www.jd.com",
                    "description": "导航到示例站"
                }
                
                builder = InstructionBuilder()
                page_data = {
                    "url": "about:blank",
                    "title": "空白",
                    "elements": [],
                    "functional_areas": [],
                    "page_type": "generic",
                    "is_valid": True
                }
                out = builder.build("打开示例站", page_data, session_state={})
                self.assertIsInstance(out, dict)
                self.assertEqual(out.get("action"), "navigate")
                self.assertEqual(out.get("value"), "https://www.jd.com")
                self.assertEqual(out.get("description"), "导航到示例站")

    def test_build_handles_gemini_api_error(self):
        """测试处理Gemini API错误"""
        with patch("src.reasoning.instruction_builder.get_llm_manager") as mock_get_llm_manager, \
             patch("src.reasoning.instruction_builder.PromptManager") as mock_prompt_manager, \
             patch("src.reasoning.instruction_builder.PluginManager") as mock_plugin_manager:
            
            # 创建模拟的LLM管理器
            mock_llm_manager = MagicMock()
            mock_llm_manager.get_available_providers.return_value = ["gemini"]
            mock_get_llm_manager.return_value = mock_llm_manager
            
            # 模拟call_llm方法抛出异常
            mock_llm_manager.call_llm.side_effect = Exception("API调用失败")
            
            # 模拟PromptManager
            mock_prompt_manager_instance = MagicMock()
            mock_prompt_manager_instance.build_complete_prompt.return_value = "测试提示词"
            mock_prompt_manager.return_value = mock_prompt_manager_instance
            
            # 模拟PluginManager
            mock_plugin_manager_instance = MagicMock()
            mock_plugin_manager_instance.build_instruction_with_fallback.return_value = None
            mock_plugin_manager.return_value = mock_plugin_manager_instance
            
            builder = InstructionBuilder()
            page_data = {
                "url": "about:blank",
                "title": "空白",
                "elements": [],
                "functional_areas": [],
                "page_type": "generic",
                "is_valid": True
            }
            out = builder.build("打开示例站", page_data, session_state={})
            # 应该返回错误指令
            self.assertIsInstance(out, dict)
            self.assertEqual(out.get("action"), "error")
            # 检查错误信息是否包含相关关键词
            self.assertIn("无法解析用户指令", out.get("error", ""))

    def test_build_handles_invalid_json_response(self):
        """测试处理无效的JSON响应"""
        with patch("src.reasoning.instruction_builder.get_llm_manager") as mock_get_llm_manager, \
             patch("src.reasoning.instruction_builder.PromptManager") as mock_prompt_manager, \
             patch("src.reasoning.instruction_builder.PluginManager") as mock_plugin_manager:
            
            # 创建模拟的LLM管理器
            mock_llm_manager = MagicMock()
            mock_llm_manager.get_available_providers.return_value = ["gemini"]
            mock_get_llm_manager.return_value = mock_llm_manager
            
            # 模拟call_llm方法返回无效JSON
            mock_llm_manager.call_llm.return_value = {
                "text": '{"action": "navigate", "value": "https://www.jd.com"'  # 无效JSON，缺少闭合括号
            }
            
            # 模拟PromptManager
            mock_prompt_manager_instance = MagicMock()
            mock_prompt_manager_instance.build_complete_prompt.return_value = "测试提示词"
            mock_prompt_manager.return_value = mock_prompt_manager_instance
            
            # 模拟PluginManager
            mock_plugin_manager_instance = MagicMock()
            mock_plugin_manager_instance.build_instruction_with_fallback.return_value = None
            mock_plugin_manager.return_value = mock_plugin_manager_instance
            
            # 模拟验证方法抛出异常
            with patch.object(InstructionBuilder, '_validate_instruction') as mock_validate:
                mock_validate.side_effect = Exception("JSON解析失败")
                
                builder = InstructionBuilder()
                page_data = {
                    "url": "about:blank",
                    "title": "空白",
                    "elements": [],
                    "functional_areas": [],
                    "page_type": "generic",
                    "is_valid": True
                }
                out = builder.build("打开示例站", page_data, session_state={})
                # 应该返回错误指令
                self.assertIsInstance(out, dict)
                self.assertEqual(out.get("action"), "error")
                # 检查错误信息是否包含相关关键词
                self.assertIn("JSON解析失败", out.get("error", ""))

    def test_build_with_empty_user_text(self):
        """测试使用空用户文本构建指令"""
        with patch("src.reasoning.instruction_builder.get_llm_manager") as mock_get_llm_manager, \
             patch("src.reasoning.instruction_builder.PromptManager") as mock_prompt_manager, \
             patch("src.reasoning.instruction_builder.PluginManager") as mock_plugin_manager:
            
            # 创建模拟的LLM管理器
            mock_llm_manager = MagicMock()
            mock_llm_manager.get_available_providers.return_value = ["gemini"]
            mock_get_llm_manager.return_value = mock_llm_manager
            
            # 模拟PromptManager
            mock_prompt_manager_instance = MagicMock()
            mock_prompt_manager.return_value = mock_prompt_manager_instance
            
            # 模拟PluginManager
            mock_plugin_manager_instance = MagicMock()
            mock_plugin_manager.return_value = mock_plugin_manager_instance
            
            # 模拟验证方法抛出异常
            with patch.object(InstructionBuilder, '_validate_instruction') as mock_validate:
                mock_validate.side_effect = Exception("用户输入为空")
                
                builder = InstructionBuilder()
                page_data = {
                    "url": "about:blank",
                    "title": "空白",
                    "elements": [],
                    "functional_areas": [],
                    "page_type": "generic",
                    "is_valid": True
                }
                out = builder.build("", page_data, session_state={})
                # 应该返回错误指令
                self.assertIsInstance(out, dict)
                self.assertEqual(out.get("action"), "error")
                # 检查错误信息是否包含相关关键词
                self.assertIn("用户输入为空", out.get("error", ""))


if __name__ == "__main__":
    unittest.main()