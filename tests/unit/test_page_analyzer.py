#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面分析器测试
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.perception.page_analyzer import PageAnalyzer


class TestPageAnalyzer(unittest.TestCase):
    """页面分析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟的Page对象
        self.mock_page = MagicMock()
        
        # 设置模拟页面内容
        self.mock_page.url = "https://test.com"
        self.mock_page.title.return_value = "测试页面"
        self.mock_page.evaluate.return_value = [
            {
                "type": "link",
                "text": "首页",
                "attributes": {"href": "/"},
                "selector": "a[href='/']"
            },
            {
                "type": "button",
                "text": "搜索",
                "attributes": {"type": "submit"},
                "selector": "button[type='submit']"
            }
        ]
        self.mock_page.accessibility.snapshot.return_value = {"role": "WebArea", "name": "测试页面"}
        
        # 创建PageAnalyzer实例
        self.analyzer = PageAnalyzer(self.mock_page)
    
    def test_analyze_page(self):
        """测试页面分析"""
        result = self.analyzer.analyze()
        
        # 验证结果结构
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("is_valid", False))
        self.assertEqual(result.get("title"), "测试页面")
        self.assertEqual(result.get("url"), "https://test.com")
        self.assertIn("elements", result)
        self.assertIn("functional_areas", result)
        
    def test_get_aria_snapshot(self):
        """测试获取ARIA快照"""
        snapshot = self.analyzer.get_aria_snapshot()
        
        # 验证结果
        self.assertIsNotNone(snapshot)
        self.assertIsInstance(snapshot, dict)
    



if __name__ == "__main__":
    unittest.main()