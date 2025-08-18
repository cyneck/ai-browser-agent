#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浏览器代理集成测试
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.reasoning.agent import BrowserAgent


class TestBrowserAgent(unittest.TestCase):
    """浏览器代理集成测试类"""
    
    @patch('src.reasoning.agent.sync_playwright')
    def setUp(self, mock_playwright):
        """测试前准备"""
        # 设置模拟的Playwright对象
        self.mock_playwright = mock_playwright.return_value.__enter__.return_value
        self.mock_browser = self.mock_playwright.chromium.launch.return_value
        self.mock_context = self.mock_browser.new_context.return_value
        self.mock_page = self.mock_context.new_page.return_value
        
        # 创建BrowserAgent实例
        self.agent = BrowserAgent(headless=True)
    
    def tearDown(self):
        """测试后清理"""
        self.agent.close()
    
    def test_execute_navigation_instruction(self):
        """测试执行导航指令"""
        # 设置模拟页面标题
        self.mock_page.title.return_value = "测试页面"
        
        # 执行导航指令
        result = self.agent.execute_instruction("打开百度首页")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("成功导航", result["message"])
    
    def test_execute_search_instruction(self):
        """测试执行搜索指令"""
        # 设置模拟页面标题
        self.mock_page.title.return_value = "搜索结果 - 测试"
        
        # 执行搜索指令
        result = self.agent.execute_instruction("搜索人工智能最新进展")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("搜索", result["message"].lower())
    
    def test_execute_click_instruction(self):
        """测试执行点击指令"""
        # 执行点击指令
        result = self.agent.execute_instruction("点击第一个搜索结果")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("点击", result["message"].lower())
    
    def test_execute_form_fill_instruction(self):
        """测试执行表单填写指令"""
        # 执行表单填写指令
        result = self.agent.execute_instruction("在搜索框中输入'测试内容'并提交")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("输入", result["message"].lower())
    
    def test_execute_multi_step_instruction(self):
        """测试执行多步指令"""
        # 执行多步指令
        result = self.agent.execute_instruction(
            "打开百度首页，搜索'Python教程'，点击第一个结果"
        )
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("执行完成", result["message"])
    
    def test_error_handling(self):
        """测试错误处理"""
        # 设置模拟页面抛出异常
        self.mock_page.goto.side_effect = Exception("连接超时")
        
        # 执行导航指令
        result = self.agent.execute_instruction("打开不存在的网站")
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("错误", result["message"].lower())


if __name__ == "__main__":
    unittest.main()