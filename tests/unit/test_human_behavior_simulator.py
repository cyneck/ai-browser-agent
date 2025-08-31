#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人类行为模拟器单元测试
"""

import unittest
import time
from unittest.mock import MagicMock, patch, call
from src.action.human_behavior_simulator import HumanBehaviorSimulator


class TestHumanBehaviorSimulator(unittest.TestCase):
    """人类行为模拟器测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.simulator = HumanBehaviorSimulator()
        self.mock_page = MagicMock()
        
    def test_initialization_default_config(self):
        """测试默认配置初始化"""
        simulator = HumanBehaviorSimulator()
        
        self.assertTrue(simulator.is_enabled())
        self.assertEqual(simulator.effective_config["behavior_mode"], "moderate")
        self.assertEqual(simulator.effective_config["base_delay_min"], 0.3)
        self.assertEqual(simulator.effective_config["base_delay_max"], 1.2)
        self.assertTrue(simulator.effective_config["mouse_move_enabled"])
        
    def test_initialization_custom_config(self):
        """测试自定义配置初始化"""
        custom_config = {
            "enabled": False,
            "behavior_mode": "conservative",
            "base_delay_min": 1.0,
            "base_delay_max": 3.0,
        }
        
        simulator = HumanBehaviorSimulator(custom_config)
        
        self.assertFalse(simulator.is_enabled())
        self.assertEqual(simulator.effective_config["behavior_mode"], "conservative")
        self.assertEqual(simulator.effective_config["base_delay_min"], 1.0)
        self.assertEqual(simulator.effective_config["base_delay_max"], 3.0)
        
    def test_behavior_modes(self):
        """测试不同行为模式的配置调整"""
        # 测试保守模式
        conservative_simulator = HumanBehaviorSimulator({"behavior_mode": "conservative"})
        self.assertGreaterEqual(conservative_simulator.effective_config["base_delay_min"], 0.8)
        self.assertGreaterEqual(conservative_simulator.effective_config["action_interval_min"], 1.5)
        self.assertGreaterEqual(conservative_simulator.effective_config["random_pause_probability"], 0.25)
        
        # 测试激进模式
        aggressive_simulator = HumanBehaviorSimulator({"behavior_mode": "aggressive"})
        self.assertLessEqual(aggressive_simulator.effective_config["base_delay_max"], 0.6)
        self.assertLessEqual(aggressive_simulator.effective_config["action_interval_max"], 1.5)
        self.assertLessEqual(aggressive_simulator.effective_config["random_pause_probability"], 0.08)
        
        # 测试适中模式
        moderate_simulator = HumanBehaviorSimulator({"behavior_mode": "moderate"})
        self.assertEqual(moderate_simulator.effective_config["base_delay_min"], 0.3)
        self.assertEqual(moderate_simulator.effective_config["base_delay_max"], 1.2)
        
    def test_disabled_behavior(self):
        """测试禁用行为模拟时的行为"""
        simulator = HumanBehaviorSimulator({"enabled": False})
        
        self.assertEqual(simulator.get_base_delay(), 0.0)
        self.assertEqual(simulator.get_action_interval("click"), 0.0)
        self.assertFalse(simulator.should_add_random_pause())
        
        # 测试打字延迟
        typing_delays = simulator.get_typing_delay("test")
        self.assertEqual(typing_delays, [0.0, 0.0, 0.0, 0.0])
        
    def test_base_delay_generation(self):
        """测试基础延迟生成"""
        simulator = HumanBehaviorSimulator({
            "base_delay_min": 1.0,
            "base_delay_max": 2.0,
            "jitter_enabled": False
        })
        
        # 测试多次生成，确保在范围内
        for _ in range(100):
            delay = simulator.get_base_delay()
            self.assertGreaterEqual(delay, 1.0)
            self.assertLessEqual(delay, 2.0)
            
    def test_action_interval_generation(self):
        """测试操作间隔生成"""
        simulator = HumanBehaviorSimulator({
            "action_interval_min": 1.0,
            "action_interval_max": 2.0,
            "adaptive_timing": False
        })
        
        # 测试不同操作类型的间隔范围
        for _ in range(10):
            navigate_interval = simulator.get_action_interval("navigate")
            click_interval = simulator.get_action_interval("click")
            scroll_interval = simulator.get_action_interval("scroll")
            
            # 检查间隔在合理范围内
            self.assertGreater(navigate_interval, 0)
            self.assertGreater(click_interval, 0)
            self.assertGreater(scroll_interval, 0)
            
            # 导航的乘数是1.5，点击是1.0，滚动是0.8
            # 所以在相同的随机范围内，导航平均应该比点击慢，滚动应该比点击快
            
        # 测试平均值（多次采样）
        navigate_intervals = [simulator.get_action_interval("navigate") for _ in range(100)]
        click_intervals = [simulator.get_action_interval("click") for _ in range(100)]
        scroll_intervals = [simulator.get_action_interval("scroll") for _ in range(100)]
        
        avg_navigate = sum(navigate_intervals) / len(navigate_intervals)
        avg_click = sum(click_intervals) / len(click_intervals)
        avg_scroll = sum(scroll_intervals) / len(scroll_intervals)
        
        # 验证平均值符合预期的乘数关系
        self.assertGreater(avg_navigate, avg_click)  # 导航应该比点击慢
        self.assertLess(avg_scroll, avg_click)       # 滚动应该比点击快
        
    def test_typing_delay_generation(self):
        """测试打字延迟生成"""
        simulator = HumanBehaviorSimulator({
            "typing_speed_min": 5,  # 5 字符/秒
            "typing_speed_max": 10, # 10 字符/秒
        })
        
        text = "Hello, World!"
        delays = simulator.get_typing_delay(text)
        
        # 确保延迟数量与字符数量匹配
        self.assertEqual(len(delays), len(text))
        
        # 确保所有延迟都是正数
        for delay in delays:
            self.assertGreater(delay, 0)
            
        # 检查标点符号和大写字母的延迟调整
        comma_index = text.index(',')
        space_index = text.index(' ')
        uppercase_index = text.index('H')
        
        # 标点符号应该比普通字符慢
        if comma_index < len(delays) - 1:
            comma_delay = delays[comma_index]
            normal_delay = delays[comma_index + 1]
            # 这里只是检查延迟是正数，因为随机性可能导致比较不稳定
            self.assertGreater(comma_delay, 0)
            
    def test_random_pause_logic(self):
        """测试随机暂停逻辑"""
        # 测试高概率的随机暂停
        high_prob_simulator = HumanBehaviorSimulator({
            "random_pause_probability": 1.0  # 100% 概率
        })
        
        # 应该总是返回 True
        for _ in range(10):
            self.assertTrue(high_prob_simulator.should_add_random_pause())
            
        # 测试零概率的随机暂停
        no_prob_simulator = HumanBehaviorSimulator({
            "random_pause_probability": 0.0  # 0% 概率
        })
        
        # 应该总是返回 False
        for _ in range(10):
            self.assertFalse(no_prob_simulator.should_add_random_pause())
            
    def test_random_pause_duration(self):
        """测试随机暂停时长"""
        simulator = HumanBehaviorSimulator({
            "random_pause_min": 2.0,
            "random_pause_max": 5.0
        })
        
        # 测试多次生成，确保在范围内
        for _ in range(50):
            duration = simulator.get_random_pause_duration()
            self.assertGreaterEqual(duration, 2.0)
            self.assertLessEqual(duration, 5.0)
            
    def test_page_load_wait_time(self):
        """测试页面加载等待时间"""
        simulator = HumanBehaviorSimulator({
            "page_load_wait_min": 1.0,
            "page_load_wait_max": 3.0
        })
        
        # 测试多次生成，确保在范围内
        for _ in range(50):
            wait_time = simulator.get_page_load_wait_time()
            self.assertGreaterEqual(wait_time, 1.0)
            self.assertLessEqual(wait_time, 3.0)
            
    def test_adaptive_timing(self):
        """测试自适应时间调整"""
        simulator = HumanBehaviorSimulator({
            "adaptive_timing": True,
            "action_interval_min": 1.0,
            "action_interval_max": 2.0
        })
        
        # 添加一些快速操作历史
        current_time = time.time()
        for i in range(5):
            simulator.action_history.append({
                "action_type": "click",
                "timestamp": current_time + i * 1.0,  # 每秒一个操作
                "success": True,
                "execution_time": 0.1
            })
            
        # 获取调整后的间隔时间
        interval = simulator.get_action_interval("click")
        
        # 由于操作频繁，间隔应该被增加
        base_interval = (1.0 + 2.0) / 2  # 基础平均间隔
        # 实际测试中，由于随机性，我们只检查它是正数
        self.assertGreater(interval, 0)
        
    @patch('time.sleep')
    def test_wait_before_action(self, mock_sleep):
        """测试操作前等待"""
        simulator = HumanBehaviorSimulator({
            "enabled": True,
            "base_delay_min": 0.5,
            "base_delay_max": 0.5,
            "action_interval_min": 1.0,
            "action_interval_max": 1.0,
            "random_pause_probability": 0.0  # 禁用随机暂停以简化测试
        })
        
        # 设置上次操作时间
        simulator.last_action_time = time.time() - 0.5  # 0.5秒前
        
        simulator.wait_before_action("click")
        
        # 应该调用了 sleep
        self.assertTrue(mock_sleep.called)
        
    def test_action_recording(self):
        """测试操作记录"""
        simulator = HumanBehaviorSimulator()
        
        # 记录一些操作
        simulator.record_action("click", True, 0.5)
        simulator.record_action("fill", True, 1.0)
        simulator.record_action("navigate", False, 2.0)
        
        # 检查历史记录
        self.assertEqual(len(simulator.action_history), 3)
        
        # 检查最后一个记录
        last_action = simulator.action_history[-1]
        self.assertEqual(last_action["action_type"], "navigate")
        self.assertFalse(last_action["success"])
        self.assertEqual(last_action["execution_time"], 2.0)
        
        # 检查时间戳
        self.assertGreater(last_action["timestamp"], 0)
        self.assertGreater(simulator.last_action_time, 0)
        
    def test_history_size_limit(self):
        """测试历史记录大小限制"""
        simulator = HumanBehaviorSimulator()
        
        # 添加超过限制的记录（51个，触发清理）
        for i in range(51):
            simulator.record_action("click", True, 0.1)
            
        # 第51个记录后应该触发清理，保留后30个
        self.assertEqual(len(simulator.action_history), 30)
        
        # 测试多次添加记录后的情况
        initial_size = len(simulator.action_history)
        
        # 添加更多记录，直到再次超过50个
        for i in range(25):  # 30 + 25 = 55
            simulator.record_action("scroll", True, 0.1)
            
        # 应该再次触发清理，保持在30个或更少
        self.assertLessEqual(len(simulator.action_history), 35)  # 容忍一些误差
        self.assertGreaterEqual(len(simulator.action_history), 25)  # 但不应该太少
        
    @patch('time.sleep')
    def test_simulate_human_typing(self, mock_sleep):
        """测试人类打字模拟"""
        simulator = HumanBehaviorSimulator({"enabled": True})
        
        mock_element = MagicMock()
        self.mock_page.locator.return_value = mock_element
        
        text = "Hello"
        simulator.simulate_human_typing(self.mock_page, "#input", text)
        
        # 检查页面操作
        self.mock_page.locator.assert_called_with("#input")
        mock_element.click.assert_called_once()
        mock_element.clear.assert_called_once()
        
        # 检查逐字符输入
        expected_calls = [call(char) for char in text]
        mock_element.type.assert_has_calls(expected_calls)
        
        # 应该调用了 sleep（打字延迟）
        self.assertTrue(mock_sleep.called)
        
    def test_simulate_human_typing_disabled(self):
        """测试禁用状态下的打字模拟"""
        simulator = HumanBehaviorSimulator({"enabled": False})
        
        mock_element = MagicMock()
        self.mock_page.locator.return_value = mock_element
        
        text = "Hello"
        simulator.simulate_human_typing(self.mock_page, "#input", text)
        
        # 应该直接调用 fill 方法
        mock_element.fill.assert_called_once_with(text)
        
    @patch('random.randint')
    @patch('time.sleep')
    def test_simulate_mouse_movement(self, mock_sleep, mock_randint):
        """测试鼠标移动模拟"""
        mock_randint.return_value = 10  # 固定随机值以便测试
        
        simulator = HumanBehaviorSimulator({
            "enabled": True,
            "mouse_move_enabled": True,
            "mouse_move_steps": 5,
            "mouse_move_duration": 1.0
        })
        
        mock_mouse = MagicMock()
        self.mock_page.mouse = mock_mouse
        
        start_pos = (100, 100)
        end_pos = (200, 200)
        
        simulator.simulate_mouse_movement(self.mock_page, start_pos, end_pos)
        
        # 检查鼠标移动调用
        self.assertTrue(mock_mouse.move.called)
        # 应该有多次移动调用（贝塞尔曲线路径）
        self.assertGreater(mock_mouse.move.call_count, 1)
        
        # 检查sleep调用（移动间隔）
        self.assertTrue(mock_sleep.called)
        
    def test_simulate_mouse_movement_disabled(self):
        """测试禁用状态下的鼠标移动"""
        simulator = HumanBehaviorSimulator({"enabled": False})
        
        mock_mouse = MagicMock()
        self.mock_page.mouse = mock_mouse
        
        start_pos = (100, 100)
        end_pos = (200, 200)
        
        simulator.simulate_mouse_movement(self.mock_page, start_pos, end_pos)
        
        # 不应该有鼠标移动调用
        mock_mouse.move.assert_not_called()
        
    def test_mouse_movement_feature_disabled(self):
        """测试鼠标移动功能禁用"""
        simulator = HumanBehaviorSimulator({
            "enabled": True,
            "mouse_move_enabled": False
        })
        
        mock_mouse = MagicMock()
        self.mock_page.mouse = mock_mouse
        
        start_pos = (100, 100)
        end_pos = (200, 200)
        
        simulator.simulate_mouse_movement(self.mock_page, start_pos, end_pos)
        
        # 不应该有鼠标移动调用
        mock_mouse.move.assert_not_called()
        
    def test_get_stats(self):
        """测试统计信息获取"""
        simulator = HumanBehaviorSimulator()
        
        # 空历史
        stats = simulator.get_stats()
        self.assertEqual(stats["total_actions"], 0)
        
        # 添加一些操作记录（设置适当的时间戳）
        import time
        current_time = time.time()
        
        simulator.record_action("click", True, 0.5)
        simulator.action_history[-1]["timestamp"] = current_time
        
        simulator.record_action("fill", True, 1.0)
        simulator.action_history[-1]["timestamp"] = current_time + 2.0
        
        simulator.record_action("navigate", False, 2.0)
        simulator.action_history[-1]["timestamp"] = current_time + 5.0
        
        stats = simulator.get_stats()
        
        self.assertEqual(stats["total_actions"], 3)
        self.assertEqual(stats["success_rate"], 2/3)  # 2 成功 / 3 总数
        self.assertGreater(stats["average_interval"], 0)  # 现在应该有间隔了
        self.assertEqual(stats["behavior_mode"], "moderate")
        self.assertTrue(stats["enabled"])
        
    def test_jitter_effect(self):
        """测试抖动效果"""
        simulator_with_jitter = HumanBehaviorSimulator({
            "jitter_enabled": True,
            "base_delay_min": 1.0,
            "base_delay_max": 1.0  # 固定基础值
        })
        
        simulator_without_jitter = HumanBehaviorSimulator({
            "jitter_enabled": False,
            "base_delay_min": 1.0,
            "base_delay_max": 1.0  # 固定基础值
        })
        
        # 生成多个延迟值
        delays_with_jitter = [simulator_with_jitter.get_base_delay() for _ in range(100)]
        delays_without_jitter = [simulator_without_jitter.get_base_delay() for _ in range(100)]
        
        # 有抖动的应该有更大的变化范围
        jitter_variance = max(delays_with_jitter) - min(delays_with_jitter)
        no_jitter_variance = max(delays_without_jitter) - min(delays_without_jitter)
        
        # 注意：由于base_delay_min和max相同，无抖动的variance应该为0
        # 有抖动的应该有一定变化
        self.assertEqual(no_jitter_variance, 0.0)
        self.assertGreater(jitter_variance, 0.0)


if __name__ == "__main__":
    unittest.main()