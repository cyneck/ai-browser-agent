#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面监控器单元测试

测试PageMonitor类的各项功能，使用mock对象模拟Playwright页面对象。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import time
from src.perception.page_monitor import PageMonitor


class TestPageMonitor(unittest.TestCase):
    """PageMonitor单元测试类"""

    def setUp(self):
        """设置测试环境"""
        # 创建mock页面对象
        self.mock_page = Mock()
        self.mock_page.evaluate.return_value = True
        self.mock_page.expose_function = Mock()
        self.mock_page.query_selector_all.return_value = []
        self.mock_page.query_selector.return_value = None
        
        # 创建PageMonitor实例
        self.monitor = PageMonitor(self.mock_page)

    def test_monitor_initialization(self):
        """测试监控器初始化"""
        self.assertIsNotNone(self.monitor.page)
        self.assertFalse(self.monitor._is_monitoring)
        self.assertEqual(len(self.monitor._listeners), 0)

    def test_add_remove_listener(self):
        """测试添加和移除监听器"""
        def test_callback(change_info):
            pass
        
        # 测试添加监听器
        self.monitor.add_listener(test_callback)
        self.assertEqual(len(self.monitor._listeners), 1)
        self.assertIn(test_callback, self.monitor._listeners)
        
        # 测试移除监听器
        self.monitor.remove_listener(test_callback)
        self.assertEqual(len(self.monitor._listeners), 0)
        self.assertNotIn(test_callback, self.monitor._listeners)

    def test_start_stop_monitoring(self):
        """测试开始和停止监控"""
        # 测试开始监控
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor._is_monitoring)
        
        # 验证页面evaluate被调用（设置观察器）
        self.mock_page.evaluate.assert_called()
        
        # 测试停止监控
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor._is_monitoring)

    def test_detect_page_changes(self):
        """测试页面变化检测"""
        # Mock页面状态
        mock_state = {
            "url": "https://test.com",
            "title": "测试页面",
            "element_count": 10,
            "content_hash": 12345,
            "timestamp": time.time() * 1000
        }
        
        with patch.object(self.monitor, '_capture_current_state', return_value=mock_state):
            # 第一次调用，应该没有变化
            changes = self.monitor.detect_page_changes()
            self.assertFalse(changes["has_changes"])
            
            # 修改状态
            modified_state = mock_state.copy()
            modified_state["title"] = "修改后的标题"
            
            with patch.object(self.monitor, '_capture_current_state', return_value=modified_state):
                # 第二次调用，应该检测到变化
                changes = self.monitor.detect_page_changes()
                self.assertTrue(changes["has_changes"])
                self.assertEqual(len(changes["changes"]), 1)
                self.assertEqual(changes["changes"][0]["type"], "title_change")

    def test_wait_for_element_appear(self):
        """测试等待元素出现"""
        # Mock元素
        mock_element = Mock()
        mock_element.is_visible.return_value = True
        
        # 第一次调用返回None，第二次返回元素
        self.mock_page.query_selector.side_effect = [None, mock_element]
        
        # 测试等待元素出现
        result = self.monitor.wait_for_element_appear("#test-element", timeout=1.0)
        self.assertTrue(result)

    def test_wait_for_element_disappear(self):
        """测试等待元素消失"""
        # Mock元素
        mock_element = Mock()
        mock_element.is_visible.return_value = False
        
        self.mock_page.query_selector.return_value = mock_element
        
        # 测试等待元素消失
        result = self.monitor.wait_for_element_disappear("#test-element", timeout=1.0)
        self.assertTrue(result)

    def test_get_page_state_info(self):
        """测试获取页面状态信息"""
        # Mock页面状态信息
        mock_state_info = {
            "basic": {
                "url": "https://test.com",
                "title": "测试页面",
                "readyState": "complete",
                "elementCount": 50,
                "timestamp": time.time() * 1000
            },
            "network": {
                "activeFetch": 0,
                "activeXHR": 0,
                "activeTimers": 0,
                "pendingPromises": 0
            },
            "loading": {
                "hasLoadingElements": False,
                "loadingElementCount": 0,
                "imagesLoading": 0,
                "imagesTotal": 5,
                "activeAnimations": 0
            },
            "isStable": True
        }
        
        self.mock_page.evaluate.return_value = mock_state_info
        
        state_info = self.monitor.get_page_state_info()
        
        # 验证返回的状态信息
        self.assertIsInstance(state_info, dict)
        self.assertIn("basic", state_info)
        self.assertIn("network", state_info)
        self.assertIn("loading", state_info)
        self.assertIn("isStable", state_info)
        self.assertTrue(state_info["isStable"])

    def test_is_page_stable(self):
        """测试页面稳定性检查"""
        # Mock稳定的页面状态
        mock_stable_state = {
            "isStable": True
        }
        
        with patch.object(self.monitor, 'get_page_state_info', return_value=mock_stable_state):
            self.assertTrue(self.monitor.is_page_stable())
        
        # Mock不稳定的页面状态
        mock_unstable_state = {
            "isStable": False
        }
        
        with patch.object(self.monitor, 'get_page_state_info', return_value=mock_unstable_state):
            self.assertFalse(self.monitor.is_page_stable())

    def test_has_loading_indicators(self):
        """测试加载指示器检测"""
        # Mock没有加载指示器
        self.mock_page.query_selector_all.return_value = []
        self.assertFalse(self.monitor._has_loading_indicators())
        
        # Mock有可见的加载指示器
        mock_element = Mock()
        mock_element.is_visible.return_value = True
        self.mock_page.query_selector_all.return_value = [mock_element]
        self.assertTrue(self.monitor._has_loading_indicators())

    def test_has_network_activity(self):
        """测试网络活动检测"""
        # Mock没有网络活动
        self.mock_page.evaluate.return_value = False
        self.assertFalse(self.monitor._has_network_activity())
        
        # Mock有网络活动
        self.mock_page.evaluate.return_value = True
        self.assertTrue(self.monitor._has_network_activity())

    def test_is_javascript_busy(self):
        """测试JavaScript繁忙状态检测"""
        # Mock JavaScript不繁忙
        self.mock_page.evaluate.return_value = False
        self.assertFalse(self.monitor._is_javascript_busy())
        
        # Mock JavaScript繁忙
        self.mock_page.evaluate.return_value = True
        self.assertTrue(self.monitor._is_javascript_busy())


if __name__ == "__main__":
    unittest.main()