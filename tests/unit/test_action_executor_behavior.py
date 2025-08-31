#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ActionExecutor与人类行为模拟集成测试
"""

import unittest
import time
from unittest.mock import MagicMock, patch, call
from src.action.executor import ActionExecutor
from src.action.human_behavior_simulator import HumanBehaviorSimulator


class TestActionExecutorWithHumanBehavior(unittest.TestCase):
    """ActionExecutor与人类行为模拟集成测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_page = MagicMock()
        self.mock_page.locator.return_value = MagicMock()
        self.mock_page.viewport_size.return_value = {"width": 1920, "height": 1080}
        
        # 创建启用行为模拟的执行器
        behavior_config = {
            "enabled": True,
            "behavior_mode": "moderate",
            "base_delay_min": 0.1,
            "base_delay_max": 0.2,
            "action_interval_min": 0.1,
            "action_interval_max": 0.3,
            "random_pause_probability": 0.0,  # 禁用随机暂停以简化测试
        }
        self.executor = ActionExecutor(self.mock_page, behavior_config=behavior_config)
        
        # 创建禁用行为模拟的执行器用于对比
        disabled_config = {"enabled": False}
        self.executor_disabled = ActionExecutor(self.mock_page, behavior_config=disabled_config)
        
    @patch('time.sleep')
    def test_navigate_with_behavior_simulation(self, mock_sleep):
        """测试导航操作的行为模拟"""
        instruction = {
            "action": "navigate",
            "value": "https://example.com",
            "description": "导航到示例网站"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        self.assertIn("成功导航到 https://example.com", result.get("message"))
        
        # 检查页面导航调用
        self.mock_page.goto.assert_called_once_with("https://example.com", wait_until="domcontentloaded")
        
        # 应该调用了sleep（页面加载等待 + 基础延迟 + 操作间隔）
        self.assertTrue(mock_sleep.called)
        self.assertGreater(mock_sleep.call_count, 1)
        
    def test_navigate_without_behavior_simulation(self):
        """测试禁用行为模拟的导航操作"""
        instruction = {
            "action": "navigate",
            "value": "https://example.com",
            "description": "导航到示例网站"
        }
        
        with patch('time.sleep') as mock_sleep:
            result = self.executor_disabled.execute(instruction, {})
            
            # 检查操作成功
            self.assertTrue(result.get("success"))
            
            # 不应该有额外的sleep调用
            mock_sleep.assert_not_called()
            
    @patch('time.sleep')
    def test_click_with_mouse_movement(self, mock_sleep):
        """测试点击操作的鼠标移动模拟"""
        # 设置元素边界框
        mock_element = MagicMock()
        mock_element.bounding_box.return_value = {
            "x": 100, "y": 100, "width": 50, "height": 30
        }
        self.mock_page.locator.return_value = mock_element
        
        # 设置鼠标模拟
        mock_mouse = MagicMock()
        self.mock_page.mouse = mock_mouse
        
        instruction = {
            "action": "click",
            "selector": "button#submit",
            "description": "点击提交按钮"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        
        # 检查鼠标移动被调用
        self.assertTrue(mock_mouse.move.called)
        
        # 检查元素点击
        mock_element.click.assert_called_once()
        
        # 应该有延迟调用
        self.assertTrue(mock_sleep.called)
        
    @patch('time.sleep')
    def test_fill_with_human_typing(self, mock_sleep):
        """测试输入操作的人类打字模拟"""
        mock_element = MagicMock()
        self.mock_page.locator.return_value = mock_element
        
        instruction = {
            "action": "fill",
            "selector": "input#username",
            "value": "testuser",
            "description": "输入用户名"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        
        # 检查人类打字行为（应该调用click, clear, 然后逐字符type）
        mock_element.click.assert_called_once()
        mock_element.clear.assert_called_once()
        
        # 检查逐字符输入
        expected_type_calls = [call(char) for char in "testuser"]
        mock_element.type.assert_has_calls(expected_type_calls)
        
        # 应该有打字延迟
        self.assertTrue(mock_sleep.called)
        self.assertGreater(mock_sleep.call_count, 1)
        
    def test_fill_without_human_behavior(self):
        """测试禁用行为模拟的输入操作"""
        mock_element = MagicMock()
        self.mock_page.locator.return_value = mock_element
        
        instruction = {
            "action": "fill",
            "selector": "input#username",
            "value": "testuser",
            "description": "输入用户名"
        }
        
        with patch('time.sleep') as mock_sleep:
            result = self.executor_disabled.execute(instruction, {})
            
            # 检查操作成功
            self.assertTrue(result.get("success"))
            
            # 应该直接调用fill方法
            mock_element.fill.assert_called_once_with("testuser")
            
            # 不应该有额外延迟
            mock_sleep.assert_not_called()
            
    @patch('time.sleep')
    def test_scroll_with_delays(self, mock_sleep):
        """测试滚动操作的延迟"""
        instruction = {
            "action": "scroll",
            "value": 500,
            "description": "向下滚动500像素"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作成功
        self.assertTrue(result.get("success"))
        
        # 检查页面滚动调用
        self.mock_page.evaluate.assert_called_with("window.scrollBy(0, 500)")
        
        # 应该有滚动后延迟
        self.assertTrue(mock_sleep.called)
        
    def test_multi_step_instruction_with_behavior(self):
        """测试多步操作的行为模拟"""
        instruction = {
            "description": "登录流程",
            "steps": [
                {"action": "fill", "selector": "#username", "value": "user"},
                {"action": "fill", "selector": "#password", "value": "pass"},
                {"action": "click", "selector": "#login-btn"}
            ]
        }
        
        with patch('time.sleep') as mock_sleep:
            result = self.executor.execute(instruction, {})
            
            # 检查操作成功
            self.assertTrue(result.get("success"))
            self.assertEqual(len(result.get("step_results", [])), 3)
            
            # 每个步骤都应该有延迟
            self.assertGreater(mock_sleep.call_count, 3)  # 至少每步一次延迟
            
    def test_behavior_stats_collection(self):
        """测试行为统计收集"""
        # 执行几个操作
        instructions = [
            {"action": "navigate", "value": "https://example.com"},
            {"action": "click", "selector": "button"},
            {"action": "fill", "selector": "input", "value": "test"}
        ]
        
        for instruction in instructions:
            self.executor.execute(instruction, {})
            
        # 获取统计信息
        stats = self.executor.get_behavior_stats()
        
        self.assertEqual(stats["total_actions"], 3)
        self.assertGreater(stats["success_rate"], 0)
        self.assertEqual(stats["behavior_mode"], "moderate")
        self.assertTrue(stats["enabled"])
        
    def test_behavior_configuration_update(self):
        """测试行为配置更新"""
        # 更新配置
        new_config = {
            "behavior_mode": "conservative",
            "base_delay_min": 1.0,
            "base_delay_max": 2.0
        }
        
        self.executor.configure_behavior(new_config)
        
        # 检查配置更新
        behavior_sim = self.executor.behavior_simulator
        self.assertEqual(behavior_sim.effective_config["behavior_mode"], "conservative")
        self.assertEqual(behavior_sim.effective_config["base_delay_min"], 1.0)
        
    @patch('time.sleep')
    def test_adaptive_timing_with_frequent_actions(self, mock_sleep):
        """测试频繁操作时的自适应时间调整"""
        # 启用自适应时间调整
        self.executor.behavior_simulator.effective_config["adaptive_timing"] = True
        
        # 执行多个快速操作
        instruction = {"action": "click", "selector": "button"}
        
        start_time = time.time()
        for i in range(5):
            # 模拟快速连续操作
            self.executor.behavior_simulator.record_action("click", True, 0.1)
            self.executor.execute(instruction, {})
            
        # 由于操作频繁，后续操作应该有更长的延迟
        # 这里主要验证自适应逻辑被触发
        self.assertTrue(mock_sleep.called)
        
    def test_error_handling_with_behavior_recording(self):
        """测试错误处理时的行为记录"""
        # 模拟会失败的操作
        self.mock_page.locator.side_effect = Exception("Element not found")
        
        instruction = {
            "action": "click",
            "selector": "non-existent-button"
        }
        
        result = self.executor.execute(instruction, {})
        
        # 检查操作失败
        self.assertFalse(result.get("success"))
        
        # 检查失败操作被记录
        stats = self.executor.get_behavior_stats()
        self.assertGreater(stats["total_actions"], 0)
        self.assertLess(stats["success_rate"], 1.0)  # 有失败记录
        
    def test_random_pause_integration(self):
        """测试随机暂停集成"""
        # 设置高概率随机暂停
        self.executor.behavior_simulator.effective_config["random_pause_probability"] = 1.0
        self.executor.behavior_simulator.effective_config["random_pause_min"] = 0.1
        self.executor.behavior_simulator.effective_config["random_pause_max"] = 0.2
        
        instruction = {"action": "click", "selector": "button"}
        
        with patch('time.sleep') as mock_sleep:
            result = self.executor.execute(instruction, {})
            
            # 检查操作成功
            self.assertTrue(result.get("success"))
            
            # 应该有额外的随机暂停调用
            self.assertTrue(mock_sleep.called)
            # 由于100%概率的随机暂停，应该有多次sleep调用
            self.assertGreater(mock_sleep.call_count, 1)
            
    def test_page_load_wait_after_navigation(self):
        """测试导航后的页面加载等待"""
        self.executor.behavior_simulator.effective_config["page_load_wait_min"] = 0.1
        self.executor.behavior_simulator.effective_config["page_load_wait_max"] = 0.2
        
        instruction = {
            "action": "navigate", 
            "value": "https://example.com"
        }
        
        with patch('time.sleep') as mock_sleep:
            result = self.executor.execute(instruction, {})
            
            # 检查操作成功
            self.assertTrue(result.get("success"))
            
            # 应该有页面加载等待
            self.assertTrue(mock_sleep.called)
            
            # 检查sleep参数在预期范围内
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            page_load_waits = [duration for duration in sleep_calls 
                             if 0.1 <= duration <= 0.2]
            self.assertGreater(len(page_load_waits), 0)
            
    def test_typing_speed_variation(self):
        """测试打字速度变化"""
        # 设置固定的打字速度范围
        self.executor.behavior_simulator.effective_config["typing_speed_min"] = 5
        self.executor.behavior_simulator.effective_config["typing_speed_max"] = 5
        
        text = "Hello World"
        delays = self.executor.behavior_simulator.get_typing_delay(text)
        
        # 验证延迟数量正确
        self.assertEqual(len(delays), len(text))
        
        # 验证所有延迟都是正数
        for delay in delays:
            self.assertGreater(delay, 0)
            
        # 由于速度固定为5字符/秒，基础延迟应该约为0.2秒
        # 但会有变化和特殊字符调整
        average_delay = sum(delays) / len(delays)
        self.assertGreater(average_delay, 0.1)  # 至少0.1秒
        self.assertLess(average_delay, 0.5)     # 不超过0.5秒


if __name__ == "__main__":
    unittest.main()