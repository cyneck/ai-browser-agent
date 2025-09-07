#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面分析器集成测试

验证PageAnalyzer与真实浏览器环境的交互能力。
"""

import unittest
import tempfile
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.perception.page_analyzer import PageAnalyzer


class TestPageAnalyzerIntegration(unittest.TestCase):
    """页面分析器集成测试类"""

    def setUp(self):
        """设置测试环境"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        """清理测试环境"""
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def test_analyze_with_real_page(self):
        """测试使用真实页面进行分析"""
        # 创建一个简单的测试页面
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试页面</title>
        </head>
        <body>
            <h1>欢迎来到测试页面</h1>
            <p>这是一个用于测试的段落。</p>
            <form>
                <input type="text" name="username" placeholder="用户名">
                <input type="password" name="password" placeholder="密码">
                <button type="submit">登录</button>
            </form>
        </body>
        </html>
        """
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(test_html)
            temp_file_path = f.name

        try:
            # 导航到测试页面
            self.page.goto(f"file://{temp_file_path}")
            
            # 创建PageAnalyzer实例并分析页面
            analyzer = PageAnalyzer(self.page)
            result = analyzer.analyze()
            
            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("url", result)
            self.assertIn("title", result)
            self.assertIn("text_content", result)  # 实际键名为text_content而不是content
            self.assertIn("elements", result)
            self.assertIn("functional_areas", result)
            self.assertEqual(result["title"], "测试页面")
            self.assertTrue(result["is_valid"])
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)

    def test_analyze_complex_page(self):
        """测试分析复杂页面"""
        # 导航到一个真实网站进行测试
        self.page.goto("https://httpbin.org/html")
        
        # 创建PageAnalyzer实例并分析页面
        analyzer = PageAnalyzer(self.page)
        result = analyzer.analyze()
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn("url", result)
        self.assertIn("title", result)
        self.assertIn("text_content", result)  # 实际键名为text_content而不是content
        self.assertIn("elements", result)
        self.assertIn("functional_areas", result)
        self.assertEqual(result["url"], "https://httpbin.org/html")
        self.assertTrue(result["is_valid"])


if __name__ == "__main__":
    unittest.main()