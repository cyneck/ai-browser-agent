#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
键盘操作测试
测试新增的 key action 功能
"""

import unittest
from unittest.mock import MagicMock
from src.action.executor import ActionExecutor


class TestKeyboardActions(unittest.TestCase):
    """键盘操作测试类"""

    def setUp(self):
        """设置测试环境"""
        self.mock_page = MagicMock()
        self.mock_locator = MagicMock()
        self.mock_page.locator.return_value = self.mock_locator
        
        # 禁用人类行为模拟以简化测试
        behavior_config = {"enabled": False}
        self.executor = ActionExecutor(self.mock_page, behavior_config=behavior_config)

    def test_key_action_supported(self):
        """测试key动作被支持"""
        supported_actions = self.executor.get_supported_actions()
        self.assertIn("key", supported_actions)

    def test_key_action_with_selector(self):
        """测试带选择器的键盘操作"""
        instruction = {
            "action": "key", 
            "selector": "input#search", 
            "value": "Enter"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        self.assertIn("成功在 input#search 上按下 Enter 键", result.get("message"))
        
        # 检查调用了正确的方法
        self.mock_page.locator.assert_called_once_with("input#search")
        self.mock_locator.focus.assert_called_once()
        self.mock_page.keyboard.press.assert_called_once_with("Enter")

    def test_key_action_without_selector(self):
        """测试不带选择器的键盘操作"""
        instruction = {
            "action": "key",
            "value": "Escape"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        self.assertIn("成功按下 Escape 键", result.get("message"))
        
        # 检查调用了正确的方法
        self.mock_page.keyboard.press.assert_called_once_with("Escape")

    def test_key_action_with_key_parameter(self):
        """测试使用key参数而非value参数"""
        instruction = {
            "action": "key",
            "selector": "textarea",
            "key": "Tab"  # 使用key而不是value
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        
        # 检查调用了正确的方法
        self.mock_page.keyboard.press.assert_called_once_with("Tab")

    def test_key_action_missing_key_value(self):
        """测试缺少按键值的情况"""
        instruction = {
            "action": "key",
            "selector": "input"
            # 缺少value或key参数
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作失败
        self.assertFalse(result.get("success"))
        self.assertIn("按键失败：按键值为空", result.get("message"))

    def test_key_action_error_handling(self):
        """测试键盘操作错误处理"""
        # 模拟键盘操作失败
        self.mock_page.keyboard.press.side_effect = Exception("Keyboard error")
        
        instruction = {
            "action": "key",
            "value": "Enter"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作失败并包含错误信息
        self.assertFalse(result.get("success"))
        self.assertIn("按键失败", result.get("message"))

    def test_multi_step_with_key_action(self):
        """测试包含键盘操作的多步指令"""
        instruction = {
            "description": "搜索操作",
            "steps": [
                {"action": "fill", "selector": "input", "value": "test query"},
                {"action": "key", "selector": "input", "value": "Enter"},
                {"action": "wait", "value": 1000}
            ]
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查整体操作成功
        self.assertTrue(result.get("success"))
        self.assertEqual(len(result.get("step_results", [])), 3)
        
        # 检查键盘操作步骤成功
        step_results = result.get("step_results", [])
        key_step_result = step_results[1]  # 第二步是key操作
        self.assertTrue(key_step_result.get("success"))


if __name__ == "__main__":
    unittest.main()