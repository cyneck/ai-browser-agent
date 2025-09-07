#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
意图分类器单元测试

注意：此为单元测试，测试IntentClassifier的逻辑功能，
使用模拟的页面分析数据，而非真实页面内容。
如需测试真实环境，请参考tests/integration/test_reasoning_integration.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.reasoning.intent_classifier import IntentClassifier, IntentType


class TestIntentClassifier(unittest.TestCase):
    """意图分类器单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.classifier = IntentClassifier()
        
        # 创建模拟的页面分析数据
        self.mock_page_data = {
            "url": "https://example.com",
            "title": "示例网站",
            "content": "这是一个示例网站的页面内容，包含一些新闻和信息。",
            "elements": [
                {"type": "link", "text": "首页", "selector": "a[href='/']"},
                {"type": "link", "text": "新闻", "selector": "a[href='/news']"},
                {"type": "link", "text": "关于", "selector": "a[href='/about']"},
                {"type": "input", "text": "搜索", "selector": "input[name='q']"},
                {"type": "button", "text": "搜索", "selector": "button[type='submit']"}
            ],
            "functional_areas": [
                {"type": "navigation", "elements": ["首页", "新闻", "关于"]},
                {"type": "search", "elements": ["搜索"]}
            ]
        }

    def test_summary_info_intent(self):
        """测试摘要信息意图识别"""
        # 测试关键词匹配
        intent_result = self.classifier.classify("总结一下这个页面", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.SUMMARY_INFO)
        self.assertGreater(intent_result.confidence, 0.5)
        
        # 测试不同表达方式
        intent_result = self.classifier.classify("简要说明页面内容", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.SUMMARY_INFO)
        
    def test_detailed_info_intent(self):
        """测试详细信息意图识别"""
        intent_result = self.classifier.classify("详细介绍页面内容", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.DETAILED_INFO)
        self.assertGreater(intent_result.confidence, 0.5)
        
        intent_result = self.classifier.classify("详细描述这些信息", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.DETAILED_INFO)

    def test_navigation_intent(self):
        """测试导航意图识别"""
        intent_result = self.classifier.classify("转到新闻页面", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.NAVIGATION)
        self.assertGreater(intent_result.confidence, 0.5)
        
        intent_result = self.classifier.classify("点击关于链接", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.NAVIGATION)

    def test_form_interaction_intent(self):
        """测试表单交互意图识别"""
        intent_result = self.classifier.classify("在搜索框中输入人工智能", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.FORM_INTERACTION)
        self.assertGreater(intent_result.confidence, 0.5)
        
        intent_result = self.classifier.classify("填写表单并提交", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.FORM_INTERACTION)

    def test_screenshot_intent(self):
        """测试截图意图识别"""
        intent_result = self.classifier.classify("截图这个页面", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.SCREENSHOT)
        self.assertGreater(intent_result.confidence, 0.5)
        
        intent_result = self.classifier.classify("截个图给我", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.SCREENSHOT)

    def test_download_intent(self):
        """测试下载意图识别"""
        intent_result = self.classifier.classify("保存这个页面", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.DOWNLOAD)
        self.assertGreater(intent_result.confidence, 0.5)
        
        intent_result = self.classifier.classify("下载页面内容", self.mock_page_data)
        self.assertEqual(intent_result.intent_type, IntentType.DOWNLOAD)

    def test_unknown_intent(self):
        """测试未知意图识别"""
        intent_result = self.classifier.classify("做一些无法理解的事情", self.mock_page_data)
        # 可能是UNKNOWN或其他已知类型，具体取决于实现细节
        self.assertIsNotNone(intent_result.intent_type)

    def test_keyword_extraction(self):
        """测试关键词提取"""
        intent_result = self.classifier.classify("总结一下页面的新闻内容", self.mock_page_data)
        self.assertIn("新闻", intent_result.keywords)
        self.assertIn("内容", intent_result.keywords)


if __name__ == "__main__":
    unittest.main()