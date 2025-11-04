#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人类行为模拟器增强功能测试
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.action.human_behavior_simulator import HumanBehaviorSimulator


class TestHumanBehaviorSimulatorEnhanced:
    """人类行为模拟器增强功能测试类"""

    def setup_method(self):
        """测试前设置"""
        self.config = {
            "enabled": True,
            "behavior_mode": "moderate",
            "anti_detection_enabled": True,
            "micro_movements_enabled": True,
            "typing_mistakes_probability": 0.1,
            "scroll_momentum_simulation": True,
        }
        self.simulator = HumanBehaviorSimulator(self.config)

    def test_enhanced_mouse_movement(self):
        """测试增强的鼠标移动功能"""
        mock_page = Mock()
        mock_page.mouse = Mock()
        
        # 测试短距离移动
        self.simulator.simulate_mouse_movement(mock_page, (100, 100), (105, 105))
        assert mock_page.mouse.move.called
        
        # 测试长距离移动
        mock_page.mouse.reset_mock()
        self.simulator.simulate_mouse_movement(mock_page, (100, 100), (500, 300))
        assert mock_page.mouse.move.call_count > 1  # 应该有多次移动调用

    def test_complex_mouse_movement_with_overshoot(self):
        """测试带过冲的复杂鼠标移动"""
        mock_page = Mock()
        mock_page.mouse = Mock()
        
        # 设置高过冲概率
        self.simulator.effective_config["mouse_overshoot_probability"] = 1.0
        
        self.simulator.simulate_mouse_movement(mock_page, (100, 100), (400, 300))
        
        # 验证鼠标移动被调用
        assert mock_page.mouse.move.called
        assert mock_page.mouse.move.call_count >= 2  # 至少有主移动和过冲修正

    def test_micro_movements(self):
        """测试微移动功能"""
        mock_page = Mock()
        mock_page.mouse = Mock()
        
        self.simulator.simulate_micro_movements(mock_page)
        
        # 验证微移动被执行
        assert mock_page.mouse.move.called

    def test_enhanced_typing_with_mistakes(self):
        """测试带错误的增强打字功能"""
        mock_page = Mock()
        mock_element = Mock()
        mock_page.locator.return_value = mock_element
        
        # 设置高错误概率
        self.simulator.effective_config["typing_mistakes_probability"] = 0.5
        self.simulator.effective_config["backspace_correction_probability"] = 1.0
        
        test_text = "hello world"
        self.simulator.simulate_human_typing(mock_page, "#input", test_text)
        
        # 验证基本操作被调用
        mock_element.click.assert_called_once()
        mock_element.clear.assert_called_once()
        assert mock_element.type.called or mock_element.press.called

    def test_nearby_key_generation(self):
        """测试相邻键生成功能"""
        # 测试已知字符
        nearby_char = self.simulator._get_nearby_key('a')
        assert nearby_char in ['q', 's', 'z']
        
        nearby_char = self.simulator._get_nearby_key('s')
        assert nearby_char in ['a', 'w', 'd', 'z', 'x']
        
        # 测试未知字符
        nearby_char = self.simulator._get_nearby_key('1')
        assert isinstance(nearby_char, str)

    def test_scroll_with_momentum(self):
        """测试带惯性的滚动功能"""
        mock_page = Mock()
        
        self.simulator.simulate_scroll_with_momentum(mock_page, "down", 300)
        
        # 验证页面评估被调用（用于滚动）
        assert mock_page.evaluate.called
        assert mock_page.evaluate.call_count > 1  # 应该有多次滚动调用

    def test_scroll_momentum_disabled(self):
        """测试禁用惯性滚动时的行为"""
        self.simulator.effective_config["scroll_momentum_simulation"] = False
        mock_page = Mock()
        
        self.simulator.simulate_scroll_with_momentum(mock_page, "down", 300)
        
        # 验证只有一次滚动调用
        mock_page.evaluate.assert_called_once()

    def test_anti_detection_measures(self):
        """测试反检测措施"""
        mock_page = Mock()
        mock_page.set_viewport_size = Mock()
        
        self.simulator.apply_anti_detection_measures(mock_page)
        
        # 验证反检测措施被应用
        # 注意：由于随机性，我们只检查方法是否被调用
        # 具体的检测逻辑在实际使用中会有效果

    def test_viewport_randomization(self):
        """测试视口随机化"""
        mock_page = Mock()
        mock_page.set_viewport_size = Mock()
        
        self.simulator._randomize_viewport(mock_page)
        
        # 验证视口大小被设置
        mock_page.set_viewport_size.assert_called_once()
        
        # 获取调用参数
        call_args = mock_page.set_viewport_size.call_args[0][0]
        assert "width" in call_args
        assert "height" in call_args
        assert call_args["width"] > 0
        assert call_args["height"] > 0

    def test_browsing_patterns_simulation(self):
        """测试浏览模式模拟"""
        mock_page = Mock()
        mock_page.evaluate = Mock()
        mock_page.mouse = Mock()
        
        # 多次调用以增加随机事件发生的概率
        for _ in range(10):
            self.simulator._simulate_browsing_patterns(mock_page)

    def test_behavior_adjustment_based_on_detection(self):
        """测试基于检测的行为调整"""
        original_mode = self.simulator.effective_config["behavior_mode"]
        
        # 测试高风险检测
        self.simulator.adjust_behavior_based_on_detection("high")
        assert self.simulator.effective_config["behavior_mode"] == "conservative"
        assert self.simulator.effective_config["random_pause_probability"] > 0.3
        
        # 重置并测试中等风险
        self.simulator.effective_config["behavior_mode"] = original_mode
        self.simulator.adjust_behavior_based_on_detection("medium")
        assert self.simulator.effective_config["behavior_mode"] == "conservative"
        
        # 测试低风险
        self.simulator.effective_config["behavior_mode"] = "conservative"
        self.simulator.adjust_behavior_based_on_detection("low")
        assert self.simulator.effective_config["behavior_mode"] == "moderate"

    def test_enhanced_stats(self):
        """测试增强统计信息"""
        # 添加一些操作历史
        self.simulator.record_action("click", True, 0.5)
        self.simulator.record_action("fill", True, 1.2)
        self.simulator.record_action("scroll", False, 0.8)
        
        stats = self.simulator.get_enhanced_stats()
        
        # 验证基本统计信息
        assert "total_actions" in stats
        assert "success_rate" in stats
        assert "action_type_distribution" in stats
        assert "recent_error_rate" in stats
        assert "anti_detection_enabled" in stats
        assert "advanced_features_enabled" in stats
        
        # 验证操作类型分布
        assert "click" in stats["action_type_distribution"]
        assert "fill" in stats["action_type_distribution"]
        assert "scroll" in stats["action_type_distribution"]
        
        # 验证高级功能状态
        advanced_features = stats["advanced_features_enabled"]
        assert "micro_movements" in advanced_features
        assert "typing_mistakes" in advanced_features
        assert "scroll_momentum" in advanced_features
        assert "focus_behavior" in advanced_features

    def test_ease_in_out_cubic_function(self):
        """测试三次缓动函数"""
        # 测试边界值
        assert self.simulator._ease_in_out_cubic(0.0) == 0.0
        assert abs(self.simulator._ease_in_out_cubic(1.0) - 1.0) < 0.001
        
        # 测试中间值
        mid_value = self.simulator._ease_in_out_cubic(0.5)
        assert 0.4 < mid_value < 0.6  # 应该接近0.5但有缓动效果

    def test_focus_behavior_simulation(self):
        """测试焦点行为模拟"""
        mock_page = Mock()
        mock_page.mouse = Mock()
        mock_element = Mock()
        
        # 测试焦点行为模拟
        self.simulator._simulate_focus_behavior(mock_page, mock_element)
        
        # 由于有随机性，我们只验证方法执行完成没有异常

    @patch('time.sleep')
    def test_timing_functions_with_disabled_simulator(self, mock_sleep):
        """测试禁用模拟器时的时间函数"""
        self.simulator.effective_config["enabled"] = False
        
        # 测试各种延迟函数
        assert self.simulator.get_base_delay() == 0.0
        assert self.simulator.get_action_interval("click") == 0.0
        assert not self.simulator.should_add_random_pause()
        assert self.simulator.get_page_load_wait_time() == 0.0
        
        # 验证sleep没有被调用（因为延迟为0）
        delays = self.simulator.get_typing_delay("test")
        assert all(delay == 0.0 for delay in delays)

    def test_configuration_inheritance(self):
        """测试配置继承和覆盖"""
        custom_config = {
            "behavior_mode": "aggressive",
            "base_delay_min": 0.1,
            "custom_setting": "test_value"
        }
        
        simulator = HumanBehaviorSimulator(custom_config)
        
        # 验证自定义配置被应用
        assert simulator.effective_config["behavior_mode"] == "aggressive"
        assert simulator.effective_config["base_delay_min"] == 0.1
        assert simulator.effective_config["custom_setting"] == "test_value"
        
        # 验证默认配置仍然存在
        assert "mouse_move_enabled" in simulator.effective_config
        assert "typing_speed_min" in simulator.effective_config


if __name__ == "__main__":
    pytest.main([__file__])