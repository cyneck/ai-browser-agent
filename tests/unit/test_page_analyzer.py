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
        self.mock_page.content.return_value = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试页面</title>
        </head>
        <body>
            <header>
                <h1>测试网站</h1>
                <nav>
                    <ul>
                        <li><a href="/">首页</a></li>
                        <li><a href="/about">关于</a></li>
                        <li><a href="/contact">联系我们</a></li>
                    </ul>
                </nav>
            </header>
            <main>
                <h2>欢迎访问</h2>
                <p>这是一个测试页面，用于单元测试。</p>
                <form>
                    <input type="text" placeholder="搜索...">
                    <button type="submit">搜索</button>
                </form>
            </main>
            <footer>
                <p>&copy; 2023 测试网站</p>
            </footer>
        </body>
        </html>
        """
        
        # 创建PageAnalyzer实例
        self.analyzer = PageAnalyzer(self.mock_page)
    
    def test_extract_page_title(self):
        """测试提取页面标题"""
        title = self.analyzer.extract_page_title()
        self.assertEqual(title, "测试页面")
    
    def test_extract_page_type(self):
        """测试识别页面类型"""
        page_type = self.analyzer.identify_page_type()
        self.assertEqual(page_type, "generic")
    
    def test_extract_main_content(self):
        """测试提取主要内容"""
        main_content = self.analyzer.extract_main_content()
        self.assertIn("欢迎访问", main_content)
        self.assertIn("这是一个测试页面，用于单元测试。", main_content)
    
    def test_extract_navigation_links(self):
        """测试提取导航链接"""
        nav_links = self.analyzer.extract_navigation_links()
        self.assertIn({"text": "首页", "url": "/"}, nav_links)
        self.assertIn({"text": "关于", "url": "/about"}, nav_links)
        self.assertIn({"text": "联系我们", "url": "/contact"}, nav_links)
    
    def test_extract_form_elements(self):
        """测试提取表单元素"""
        forms = self.analyzer.extract_form_elements()
        self.assertEqual(len(forms), 1)
        self.assertIn("搜索", str(forms))
    
    def test_generate_page_intent_graph(self):
        """测试生成页面意图图"""
        graph = self.analyzer.generate_page_intent_graph()
        self.assertIsNotNone(graph)
        self.assertIn("title", graph)
        self.assertIn("type", graph)
        self.assertIn("elements", graph)


if __name__ == "__main__":
    unittest.main()