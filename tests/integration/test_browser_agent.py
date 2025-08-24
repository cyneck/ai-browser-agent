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
        self.mock_playwright_start = mock_playwright.return_value.start
        self.mock_playwright = self.mock_playwright_start.return_value
        self.mock_browser = self.mock_playwright.chromium.launch.return_value
        self.mock_context = self.mock_browser.new_context.return_value
        self.mock_page = self.mock_context.new_page.return_value
        
        # 设置模拟页面的基本属性
        self.mock_page.url = "https://example.com"
        self.mock_page.title.return_value = "测试页面"
        self.mock_page.evaluate.return_value = []
        self.mock_page.accessibility.snapshot.return_value = {}
        
        # 创建BrowserAgent实例（不传参数）
        self.agent = BrowserAgent()
        # 初始化标志设置为True避免真实初始化
        self.agent.initialized = True
        # 手动设置组件避免实际初始化
        self.agent.page = self.mock_page
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self.agent, 'cleanup'):
            self.agent.cleanup()
    
    @patch('src.reasoning.agent.PageAnalyzer')
    @patch('src.reasoning.agent.InstructionBuilder')
    @patch('src.reasoning.agent.ActionExecutor')
    def test_execute_navigation_instruction(self, mock_executor, mock_builder, mock_analyzer):
        """测试执行导航指令"""
        # 设置模拟返回值
        mock_analyzer_instance = mock_analyzer.return_value
        mock_builder_instance = mock_builder.return_value
        mock_executor_instance = mock_executor.return_value
        
        mock_analyzer_instance.analyze.return_value = {"is_valid": True, "url": "https://example.com"}
        mock_builder_instance.build.return_value = {"action": "navigate", "value": "https://example.com"}
        mock_executor_instance.execute.return_value = {"success": True, "message": "成功导航到页面"}
        
        # 设置代理的组件实例
        self.agent.page_analyzer = mock_analyzer_instance
        self.agent.instruction_builder = mock_builder_instance
        self.agent.action_executor = mock_executor_instance
        
        # 执行导航指令
        result = self.agent.execute("打开百度首页", {})
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("成功导航", result["message"])
    
    @patch('src.reasoning.agent.PageAnalyzer')
    @patch('src.reasoning.agent.InstructionBuilder')
    @patch('src.reasoning.agent.ActionExecutor')
    def test_execute_search_instruction(self, mock_executor, mock_builder, mock_analyzer):
        """测试执行搜索指令"""
        # 设置模拟返回值
        mock_analyzer_instance = mock_analyzer.return_value
        mock_builder_instance = mock_builder.return_value
        mock_executor_instance = mock_executor.return_value
        
        mock_analyzer_instance.analyze.return_value = {"is_valid": True, "url": "https://example.com"}
        mock_builder_instance.build.return_value = {"action": "fill", "selector": "input", "value": "人工智能"}
        mock_executor_instance.execute.return_value = {"success": True, "message": "成功执行搜索"}
        
        # 设置代理的组件实例
        self.agent.page_analyzer = mock_analyzer_instance
        self.agent.instruction_builder = mock_builder_instance
        self.agent.action_executor = mock_executor_instance
        
        # 执行搜索指令
        result = self.agent.execute("搜索人工智能最新进展", {})
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("搜索", result["message"].lower())
    
    @patch('src.reasoning.agent.PageAnalyzer')
    @patch('src.reasoning.agent.InstructionBuilder')
    @patch('src.reasoning.agent.ActionExecutor')
    def test_execute_click_instruction(self, mock_executor, mock_builder, mock_analyzer):
        """测试执行点击指令"""
        # 设置模拟返回值
        mock_analyzer_instance = mock_analyzer.return_value
        mock_builder_instance = mock_builder.return_value
        mock_executor_instance = mock_executor.return_value
        
        mock_analyzer_instance.analyze.return_value = {"is_valid": True, "url": "https://example.com"}
        mock_builder_instance.build.return_value = {"action": "click", "selector": "a:first"}
        mock_executor_instance.execute.return_value = {"success": True, "message": "成功点击元素"}
        
        # 设置代理的组件实例
        self.agent.page_analyzer = mock_analyzer_instance
        self.agent.instruction_builder = mock_builder_instance
        self.agent.action_executor = mock_executor_instance
        
        # 执行点击指令
        result = self.agent.execute("点击第一个搜索结果", {})
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("点击", result["message"].lower())
    
    @patch('src.reasoning.agent.PageAnalyzer')
    @patch('src.reasoning.agent.InstructionBuilder')
    @patch('src.reasoning.agent.ActionExecutor')
    def test_execute_form_fill_instruction(self, mock_executor, mock_builder, mock_analyzer):
        """测试执行表单填写指令"""
        # 设置模拟返回值
        mock_analyzer_instance = mock_analyzer.return_value
        mock_builder_instance = mock_builder.return_value
        mock_executor_instance = mock_executor.return_value
        
        mock_analyzer_instance.analyze.return_value = {"is_valid": True, "url": "https://example.com"}
        mock_builder_instance.build.return_value = {"action": "fill", "selector": "input[type=text]", "value": "测试内容"}
        mock_executor_instance.execute.return_value = {"success": True, "message": "成功输入内容"}
        
        # 设置代理的组件实例
        self.agent.page_analyzer = mock_analyzer_instance
        self.agent.instruction_builder = mock_builder_instance
        self.agent.action_executor = mock_executor_instance
        
        # 执行表单填写指令
        result = self.agent.execute("在搜索框中输入'测试内容'并提交", {})
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("输入", result["message"].lower())
    
    @patch('src.reasoning.agent.PageAnalyzer')
    @patch('src.reasoning.agent.InstructionBuilder')
    @patch('src.reasoning.agent.ActionExecutor')
    def test_execute_multi_step_instruction(self, mock_executor, mock_builder, mock_analyzer):
        """测试执行多步指令"""
        # 设置模拟返回值
        mock_analyzer_instance = mock_analyzer.return_value
        mock_builder_instance = mock_builder.return_value
        mock_executor_instance = mock_executor.return_value
        
        mock_analyzer_instance.analyze.return_value = {"is_valid": True, "url": "https://example.com"}
        mock_builder_instance.build.return_value = {"steps": [{"action": "navigate"}, {"action": "fill"}, {"action": "click"}]}
        mock_executor_instance.execute.return_value = {"success": True, "message": "执行完成"}
        
        # 设置代理的组件实例
        self.agent.page_analyzer = mock_analyzer_instance
        self.agent.instruction_builder = mock_builder_instance
        self.agent.action_executor = mock_executor_instance
        
        # 执行多步指令
        result = self.agent.execute(
            "打开百度首页，搜索'Python教程'，点击第一个结果", {}
        )
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertIn("执行完成", result["message"])
    
    @patch('src.reasoning.agent.PageAnalyzer')
    @patch('src.reasoning.agent.InstructionBuilder')
    @patch('src.reasoning.agent.ActionExecutor')
    def test_error_handling(self, mock_executor, mock_builder, mock_analyzer):
        """测试错误处理"""
        # 设置模拟页面抛出异常
        mock_analyzer_instance = mock_analyzer.return_value
        mock_builder_instance = mock_builder.return_value
        mock_executor_instance = mock_executor.return_value
        
        mock_analyzer_instance.analyze.return_value = {"is_valid": True, "url": "https://example.com"}
        mock_builder_instance.build.return_value = {"action": "navigate", "value": "https://invalid.com"}
        mock_executor_instance.execute.return_value = {"success": False, "error": "连接超时"}
        
        # 设置代理的组件实例
        self.agent.page_analyzer = mock_analyzer_instance
        self.agent.instruction_builder = mock_builder_instance
        self.agent.action_executor = mock_executor_instance
        
        # 执行导航指令
        result = self.agent.execute("打开不存在的网站", {})
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("超时", result.get("error", ""))


if __name__ == "__main__":
    unittest.main()