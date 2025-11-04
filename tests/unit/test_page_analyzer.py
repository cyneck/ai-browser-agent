#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面分析器单元测试

测试PageAnalyzer类的各项功能，使用mock对象模拟Playwright页面对象。
包含对各种网页类型解析准确性和异常情况处理逻辑的全面测试。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from src.perception.page_analyzer import PageAnalyzer
import json


class TestPageAnalyzer(unittest.TestCase):
    """PageAnalyzer单元测试类"""

    def setUp(self):
        """设置测试环境"""
        # 创建mock页面对象
        self.mock_page = Mock()
        self.mock_page.title.return_value = "测试页面"
        self.mock_page.url = "https://test.com"
        self.mock_page.content.return_value = "<html><head><title>测试页面</title></head><body><p>测试</p></body></html>"
        
        # 创建Accessibility mock
        self.mock_page.accessibility = Mock()
        self.mock_page.accessibility.snapshot.return_value = {"role": "WebArea", "name": "测试页面"}
        
        # 创建PageAnalyzer实例
        self.analyzer = PageAnalyzer(self.mock_page)

    def test_analyze_page(self):
        """测试页面分析"""
        # 设置mock返回值
        mock_elements = [
            {"type": "link", "text": "首页", "selector": "a[href='/']"},
            {"type": "button", "text": "提交", "selector": "button[type='submit']"}
        ]
        
        # 使用patch来mock内部方法
        with patch.object(self.analyzer, '_extract_elements_info', return_value=mock_elements), \
             patch.object(self.analyzer, '_extract_text_content', return_value="测试页面内容"), \
             patch.object(self.analyzer, '_identify_functional_areas', return_value=[]):
            
            result = self.analyzer.analyze()
            
            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["title"], "测试页面")
            self.assertEqual(result["url"], "https://test.com")
            self.assertEqual(result["elements"], mock_elements)
            self.assertEqual(result["text_content"], "测试页面内容")
            
            # 验证方法调用（注意：在实际实现中，title()方法可能被调用多次）
            self.assertGreaterEqual(self.mock_page.title.call_count, 1)

    def test_get_aria_snapshot(self):
        """测试获取ARIA快照"""
        snapshot = self.analyzer.get_aria_snapshot()
        
        # 验证结果
        self.assertIsNotNone(snapshot)
        self.assertIsInstance(snapshot, dict)
        self.assertEqual(snapshot, {"role": "WebArea", "name": "测试页面"})
        
        # 验证方法调用
        self.mock_page.accessibility.snapshot.assert_called_once()
        
    def test_extract_elements(self):
        """测试元素提取"""
        # 修改测试用例以使用实际的方法名
        elements = self.analyzer._extract_elements_info()
        
        # 因为是mock对象，我们无法直接测试实际的JavaScript执行结果
        # 但我们可以通过mock来验证方法被正确调用
        # 这里我们验证方法不会抛出异常
        self.assertTrue(hasattr(self.analyzer, '_extract_elements_info'))

    def test_extract_page_content(self):
        """测试页面内容提取"""
        # 修改测试用例以使用实际的方法名
        content = self.analyzer._extract_text_content()
        
        # 因为是mock对象，我们无法直接测试实际的JavaScript执行结果
        # 但我们可以通过mock来验证方法被正确调用
        # 这里我们验证方法不会抛出异常
        self.assertTrue(hasattr(self.analyzer, '_extract_text_content'))

    def test_enhanced_element_extraction_structure(self):
        """测试增强的元素提取功能返回的数据结构"""
        # Mock the page.evaluate method to return enhanced element structure
        mock_enhanced_elements = [
            {
                'type': 'button',
                'subType': '',
                'tagName': 'button',
                'text': '提交',
                'altText': '',
                'ariaLabel': '',
                'title': '',
                'placeholder': '',
                'value': '',
                'attributes': {'type': 'submit', 'class': 'btn-primary'},
                'position': {
                    'x': 100, 'y': 200, 'width': 80, 'height': 32,
                    'centerX': 140, 'centerY': 216,
                    'visible': True, 'inViewport': True, 'partiallyInViewport': True
                },
                'selectors': [
                    {'type': 'css', 'value': 'button[type="submit"]', 'priority': 5, 'reliability': 'medium'}
                ],
                'selector': 'button[type="submit"]',
                'bestSelector': 'button[type="submit"]',
                'isInteractive': True,
                'isVisible': True,
                'isInteractable': True,
                'canClick': True,
                'canType': False,
                'canSelect': False,
                'canDrag': False,
                'canFocus': True,
                'semanticInfo': {
                    'isFormElement': True,
                    'isNavigationElement': False,
                    'isMediaElement': False,
                    'isContainerElement': False,
                    'hasLabel': False,
                    'isRequired': False,
                    'isDisabled': False
                },
                'extractedAt': 1234567890,
                'confidence': 0.7
            }
        ]
        
        self.mock_page.evaluate.return_value = mock_enhanced_elements
        
        elements = self.analyzer._extract_elements_info()
        
        # 验证返回的元素包含增强的字段
        self.assertIsInstance(elements, list)
        if elements:  # 如果有元素返回
            element = elements[0]
            
            # 验证基础字段
            self.assertIn('type', element)
            self.assertIn('subType', element)
            self.assertIn('tagName', element)
            
            # 验证文本信息字段
            self.assertIn('text', element)
            self.assertIn('altText', element)
            self.assertIn('ariaLabel', element)
            self.assertIn('title', element)
            self.assertIn('placeholder', element)
            self.assertIn('value', element)
            
            # 验证位置信息包含增强字段
            self.assertIn('position', element)
            position = element['position']
            self.assertIn('centerX', position)
            self.assertIn('centerY', position)
            self.assertIn('partiallyInViewport', position)
            
            # 验证选择器信息
            self.assertIn('selectors', element)
            self.assertIn('bestSelector', element)
            
            # 验证交互能力字段
            self.assertIn('canClick', element)
            self.assertIn('canType', element)
            self.assertIn('canSelect', element)
            self.assertIn('canDrag', element)
            self.assertIn('canFocus', element)
            
            # 验证语义信息
            self.assertIn('semanticInfo', element)
            semantic_info = element['semanticInfo']
            self.assertIn('isFormElement', semantic_info)
            self.assertIn('isNavigationElement', semantic_info)
            self.assertIn('isMediaElement', semantic_info)
            
            # 验证元数据
            self.assertIn('extractedAt', element)
            self.assertIn('confidence', element)

    def test_analyze_with_enhanced_elements(self):
        """测试分析方法返回增强的元素信息"""
        # Mock enhanced elements
        mock_enhanced_elements = [
            {
                'type': 'input',
                'subType': 'text',
                'tagName': 'input',
                'text': '',
                'placeholder': '请输入用户名',
                'selectors': [
                    {'type': 'css', 'value': '#username', 'priority': 1, 'reliability': 'high'},
                    {'type': 'css', 'value': '[name="username"]', 'priority': 3, 'reliability': 'high'}
                ],
                'bestSelector': '#username',
                'canType': True,
                'semanticInfo': {'isFormElement': True},
                'isVisible': True,
                'isInteractable': True,
                'confidence': 0.9
            }
        ]
        
        with patch.object(self.analyzer, '_extract_elements_info', return_value=mock_enhanced_elements), \
             patch.object(self.analyzer, '_extract_text_content', return_value="测试页面内容"), \
             patch.object(self.analyzer, '_identify_functional_areas', return_value=[]):
            
            result = self.analyzer.analyze()
            
            # 验证结果包含增强的元素信息
            self.assertTrue(result["is_valid"])
            self.assertEqual(len(result["elements"]), 1)
            
            element = result["elements"][0]
            self.assertEqual(element['type'], 'input')
            self.assertEqual(element['subType'], 'text')
            self.assertEqual(element['bestSelector'], '#username')
            self.assertTrue(element['canType'])
            self.assertTrue(element['semanticInfo']['isFormElement'])


    def test_blank_page_handling(self):
        """测试空白页面处理"""
        # 设置空白页面
        self.mock_page.url = "about:blank"
        self.mock_page.title.return_value = ""
        
        result = self.analyzer.analyze()
        
        # 验证空白页面返回无效分析
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["url"], "about:blank")
        self.assertEqual(result["title"], "空白页面")
        self.assertEqual(result["page_type"], "blank")
        self.assertEqual(result["elements"], [])
        self.assertEqual(result["text_content"], "")

    def test_page_analysis_exception_handling(self):
        """测试页面分析异常处理"""
        # 模拟页面访问异常 - 需要在analyze方法内部抛出异常
        with patch.object(self.analyzer, '_extract_elements_info', side_effect=Exception("页面访问失败")):
            result = self.analyzer.analyze()
            
            # 验证异常处理返回无效分析
            self.assertFalse(result["is_valid"])
            self.assertIn("error", result)
            self.assertEqual(result["elements"], [])

    def test_aria_snapshot_exception_handling(self):
        """测试ARIA快照获取异常处理"""
        # 模拟ARIA快照获取失败
        self.mock_page.accessibility.snapshot.side_effect = Exception("ARIA访问失败")
        
        snapshot = self.analyzer.get_aria_snapshot()
        
        # 验证异常处理返回None
        self.assertIsNone(snapshot)

    def test_elements_extraction_exception_handling(self):
        """测试元素提取异常处理"""
        # 模拟JavaScript执行失败
        self.mock_page.evaluate.side_effect = Exception("JavaScript执行失败")
        
        elements = self.analyzer._extract_elements_info()
        
        # 验证异常处理返回空列表
        self.assertEqual(elements, [])

    def test_text_content_extraction_exception_handling(self):
        """测试文本内容提取异常处理"""
        # 模拟JavaScript执行失败
        self.mock_page.evaluate.side_effect = Exception("JavaScript执行失败")
        
        content = self.analyzer._extract_text_content()
        
        # 验证异常处理返回空字符串
        self.assertEqual(content, "")

    def test_search_results_page_type_detection(self):
        """测试搜索结果页面类型检测"""
        self.mock_page.url = "https://www.baidu.com/s?wd=测试"
        self.mock_page.title.return_value = "测试_百度搜索"
        
        with patch.object(self.analyzer, '_extract_elements_info', return_value=[]):
            page_type = self.analyzer._determine_page_type()
            
        self.assertEqual(page_type, "search_results")

    def test_product_page_type_detection(self):
        """测试产品页面类型检测"""
        self.mock_page.url = "https://item.taobao.com/item.htm?id=123456"
        self.mock_page.title.return_value = "商品详情页"
        
        with patch.object(self.analyzer, '_extract_elements_info', return_value=[]):
            page_type = self.analyzer._determine_page_type()
            
        self.assertEqual(page_type, "product_page")

    def test_article_page_type_detection(self):
        """测试文章页面类型检测"""
        self.mock_page.url = "https://blog.example.com/article/test"
        self.mock_page.title.return_value = "测试文章"
        
        with patch.object(self.analyzer, '_extract_elements_info', return_value=[]):
            page_type = self.analyzer._determine_page_type()
            
        self.assertEqual(page_type, "article_page")

    def test_form_page_type_detection(self):
        """测试表单页面类型检测"""
        self.mock_page.url = "https://example.com/form"
        self.mock_page.title.return_value = "表单页面"
        
        mock_elements = [{"type": "form", "tagName": "form"}]
        with patch.object(self.analyzer, '_extract_elements_info', return_value=mock_elements):
            page_type = self.analyzer._determine_page_type()
            
        self.assertEqual(page_type, "form_page")

    def test_generic_page_type_detection(self):
        """测试通用页面类型检测"""
        self.mock_page.url = "https://example.com/about"
        self.mock_page.title.return_value = "关于我们"
        
        with patch.object(self.analyzer, '_extract_elements_info', return_value=[]):
            page_type = self.analyzer._determine_page_type()
            
        self.assertEqual(page_type, "generic")

    def test_page_type_detection_exception_handling(self):
        """测试页面类型检测异常处理"""
        # 模拟URL访问异常
        type(self.mock_page).url = PropertyMock(side_effect=Exception("URL访问失败"))
        
        page_type = self.analyzer._determine_page_type()
        
        # 验证异常处理返回unknown
        self.assertEqual(page_type, "unknown")

    def test_functional_areas_identification(self):
        """测试功能区域识别"""
        # 创建mock元素
        mock_search_input = Mock()
        mock_search_input.is_visible.return_value = True
        
        mock_nav_element = Mock()
        mock_main_element = Mock()
        
        # 设置query_selector_all返回值
        def mock_query_selector_all(selector):
            if 'input[type="text"]' in selector or 'input[type="search"]' in selector:
                return [mock_search_input]
            elif 'nav' in selector or 'navigation' in selector:
                return [mock_nav_element]
            elif 'main' in selector or 'article' in selector:
                return [mock_main_element]
            return []
        
        self.mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        functional_areas = self.analyzer._identify_functional_areas()
        
        # 验证识别到的功能区域
        self.assertIsInstance(functional_areas, list)
        area_types = [area["type"] for area in functional_areas]
        self.assertIn("search_box", area_types)
        self.assertIn("navigation_bar", area_types)
        self.assertIn("main_content", area_types)

    def test_functional_areas_identification_exception_handling(self):
        """测试功能区域识别异常处理"""
        # 模拟query_selector_all异常
        self.mock_page.query_selector_all.side_effect = Exception("元素查询失败")
        
        functional_areas = self.analyzer._identify_functional_areas()
        
        # 验证异常处理返回空列表
        self.assertEqual(functional_areas, [])

    def test_functional_areas_with_invisible_elements(self):
        """测试包含不可见元素的功能区域识别"""
        # 创建不可见的搜索框
        mock_invisible_input = Mock()
        mock_invisible_input.is_visible.return_value = False
        
        self.mock_page.query_selector_all.return_value = [mock_invisible_input]
        
        functional_areas = self.analyzer._identify_functional_areas()
        
        # 验证不可见元素不被识别为功能区域
        search_areas = [area for area in functional_areas if area["type"] == "search_box"]
        self.assertEqual(len(search_areas), 0)

    def test_dynamic_content_monitoring_integration(self):
        """测试动态内容监控集成"""
        # 测试监控方法存在性
        self.assertTrue(hasattr(self.analyzer, 'start_monitoring'))
        self.assertTrue(hasattr(self.analyzer, 'stop_monitoring'))
        self.assertTrue(hasattr(self.analyzer, 'add_change_listener'))
        self.assertTrue(hasattr(self.analyzer, 'remove_change_listener'))
        self.assertTrue(hasattr(self.analyzer, 'wait_for_dynamic_content'))
        self.assertTrue(hasattr(self.analyzer, 'wait_for_element_stable'))
        self.assertTrue(hasattr(self.analyzer, 'detect_page_changes'))

    def test_analyze_with_dynamic_content(self):
        """测试包含动态内容的页面分析"""
        mock_elements = [{"type": "button", "text": "动态按钮"}]
        
        with patch.object(self.analyzer, 'wait_for_dynamic_content', return_value=True), \
             patch.object(self.analyzer, '_extract_elements_info', return_value=mock_elements), \
             patch.object(self.analyzer, '_extract_text_content', return_value="动态内容"), \
             patch.object(self.analyzer, '_identify_functional_areas', return_value=[]):
            
            result = self.analyzer.analyze_with_dynamic_content(wait_for_stable=True, timeout=5.0)
            
            # 验证动态内容分析结果
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["elements"], mock_elements)
            self.assertEqual(result["text_content"], "动态内容")

    def test_analyze_with_dynamic_content_exception_handling(self):
        """测试动态内容分析异常处理"""
        # 模拟动态内容等待失败
        with patch.object(self.analyzer, 'wait_for_dynamic_content', side_effect=Exception("等待失败")), \
             patch.object(self.analyzer, 'analyze', return_value={"is_valid": True, "fallback": True}):
            
            result = self.analyzer.analyze_with_dynamic_content(wait_for_stable=True)
            
            # 验证降级到普通分析
            self.assertTrue(result["is_valid"])
            self.assertTrue(result.get("fallback", False))

    def test_complex_element_structure_parsing(self):
        """测试复杂元素结构解析"""
        # 模拟复杂的元素结构
        complex_elements = [
            {
                'type': 'input',
                'subType': 'email',
                'tagName': 'input',
                'text': '',
                'placeholder': '请输入邮箱',
                'attributes': {'type': 'email', 'required': 'true', 'class': 'form-control'},
                'position': {'x': 10, 'y': 20, 'width': 200, 'height': 30, 'visible': True},
                'selectors': [
                    {'type': 'css', 'value': '#email', 'priority': 1, 'reliability': 'high'},
                    {'type': 'css', 'value': '[type="email"]', 'priority': 5, 'reliability': 'medium'}
                ],
                'bestSelector': '#email',
                'canType': True,
                'canClick': True,
                'semanticInfo': {'isFormElement': True, 'isRequired': True},
                'confidence': 0.9
            },
            {
                'type': 'button',
                'subType': 'submit',
                'tagName': 'button',
                'text': '提交表单',
                'attributes': {'type': 'submit', 'class': 'btn btn-primary'},
                'position': {'x': 10, 'y': 60, 'width': 100, 'height': 40, 'visible': True},
                'selectors': [
                    {'type': 'css', 'value': 'button[type="submit"]', 'priority': 3, 'reliability': 'medium'},
                    {'type': 'text', 'value': 'text="提交表单"', 'priority': 8, 'reliability': 'medium'}
                ],
                'bestSelector': 'button[type="submit"]',
                'canClick': True,
                'semanticInfo': {'isFormElement': True},
                'confidence': 0.8
            }
        ]
        
        self.mock_page.evaluate.return_value = complex_elements
        
        elements = self.analyzer._extract_elements_info()
        
        # 验证复杂元素结构解析
        self.assertEqual(len(elements), 2)
        
        # 验证邮箱输入框
        email_input = elements[0]
        self.assertEqual(email_input['type'], 'input')
        self.assertEqual(email_input['subType'], 'email')
        self.assertTrue(email_input['canType'])
        self.assertTrue(email_input['semanticInfo']['isRequired'])
        
        # 验证提交按钮
        submit_button = elements[1]
        self.assertEqual(submit_button['type'], 'button')
        self.assertEqual(submit_button['text'], '提交表单')
        self.assertTrue(submit_button['canClick'])

    def test_different_webpage_types_parsing(self):
        """测试不同网页类型的解析准确性"""
        # 测试电商网站
        ecommerce_elements = [
            {'type': 'button', 'text': '加入购物车', 'semanticInfo': {'isFormElement': True}},
            {'type': 'input', 'subType': 'number', 'text': '', 'placeholder': '数量', 'canType': True},
            {'type': 'link', 'text': '商品详情', 'semanticInfo': {'isNavigationElement': True}}
        ]
        
        # 测试社交媒体网站
        social_elements = [
            {'type': 'button', 'text': '点赞', 'canClick': True},
            {'type': 'textarea', 'text': '', 'placeholder': '写评论...', 'canType': True},
            {'type': 'button', 'text': '分享', 'semanticInfo': {'isFormElement': True}}
        ]
        
        # 测试新闻网站
        news_elements = [
            {'type': 'link', 'text': '阅读全文', 'semanticInfo': {'isNavigationElement': True}},
            {'type': 'input', 'subType': 'search', 'text': '', 'placeholder': '搜索新闻', 'canType': True},
            {'type': 'button', 'text': '订阅', 'canClick': True}
        ]
        
        test_cases = [
            (ecommerce_elements, "电商网站"),
            (social_elements, "社交媒体"),
            (news_elements, "新闻网站")
        ]
        
        for elements, site_type in test_cases:
            with self.subTest(site_type=site_type):
                self.mock_page.evaluate.return_value = elements
                
                result_elements = self.analyzer._extract_elements_info()
                
                # 验证元素解析准确性
                self.assertEqual(len(result_elements), len(elements))
                for i, element in enumerate(result_elements):
                    expected = elements[i]
                    self.assertEqual(element['type'], expected['type'])
                    if 'text' in expected:
                        self.assertEqual(element.get('text', ''), expected['text'])

    def test_edge_cases_and_malformed_content(self):
        """测试边缘情况和格式错误的内容"""
        # 测试空元素列表
        self.mock_page.evaluate.return_value = []
        elements = self.analyzer._extract_elements_info()
        self.assertEqual(elements, [])
        
        # 测试None返回值
        self.mock_page.evaluate.return_value = None
        elements = self.analyzer._extract_elements_info()
        self.assertEqual(elements, [])
        
        # 测试格式错误的元素数据
        malformed_elements = [
            {'type': 'button'},  # 缺少必要字段
            {'text': '按钮', 'canClick': True},  # 缺少type字段
            None,  # None元素
            {'type': 'input', 'subType': None, 'text': None}  # 包含None值
        ]
        
        self.mock_page.evaluate.return_value = malformed_elements
        elements = self.analyzer._extract_elements_info()
        
        # 验证能够处理格式错误的数据
        self.assertIsInstance(elements, list)

    def test_performance_with_large_page(self):
        """测试大型页面的性能处理"""
        # 模拟包含大量元素的页面
        large_elements_list = []
        for i in range(100):
            large_elements_list.append({
                'type': 'button',
                'text': f'按钮{i}',
                'selector': f'#btn{i}',
                'canClick': True,
                'isVisible': True,
                'confidence': 0.8
            })
        
        self.mock_page.evaluate.return_value = large_elements_list
        
        elements = self.analyzer._extract_elements_info()
        
        # 验证能够处理大量元素
        self.assertEqual(len(elements), 100)
        self.assertTrue(all(elem['type'] == 'button' for elem in elements))

    def test_unicode_and_special_characters(self):
        """测试Unicode和特殊字符处理"""
        unicode_elements = [
            {
                'type': 'button',
                'text': '🔍 搜索',
                'ariaLabel': '点击搜索按钮',
                'title': '执行搜索操作',
                'canClick': True
            },
            {
                'type': 'input',
                'placeholder': '请输入关键词...',
                'value': 'test@example.com',
                'canType': True
            }
        ]
        
        self.mock_page.evaluate.return_value = unicode_elements
        
        elements = self.analyzer._extract_elements_info()
        
        # 验证Unicode字符处理
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0]['text'], '🔍 搜索')
        self.assertEqual(elements[1]['placeholder'], '请输入关键词...')

    def test_monitoring_methods_delegation(self):
        """测试监控方法委托"""
        # 测试监控方法正确委托给PageMonitor
        with patch.object(self.analyzer.page_monitor, 'start_monitoring') as mock_start, \
             patch.object(self.analyzer.page_monitor, 'stop_monitoring') as mock_stop, \
             patch.object(self.analyzer.page_monitor, 'add_listener') as mock_add, \
             patch.object(self.analyzer.page_monitor, 'remove_listener') as mock_remove, \
             patch.object(self.analyzer.page_monitor, 'wait_for_dynamic_content') as mock_wait, \
             patch.object(self.analyzer.page_monitor, 'wait_for_element_stable') as mock_stable, \
             patch.object(self.analyzer.page_monitor, 'detect_page_changes') as mock_detect:
            
            # 调用监控方法
            callback = lambda: None
            self.analyzer.start_monitoring()
            self.analyzer.stop_monitoring()
            self.analyzer.add_change_listener(callback)
            self.analyzer.remove_change_listener(callback)
            self.analyzer.wait_for_dynamic_content(timeout=5.0, stable_time=1.0)
            self.analyzer.wait_for_element_stable("button", timeout=5.0, stable_time=1.0)
            self.analyzer.detect_page_changes()
            
            # 验证方法被正确调用
            mock_start.assert_called_once()
            mock_stop.assert_called_once()
            mock_add.assert_called_once_with(callback)
            mock_remove.assert_called_once_with(callback)
            mock_wait.assert_called_once_with(5.0, 1.0)
            mock_stable.assert_called_once_with("button", 5.0, 1.0)
            mock_detect.assert_called_once()


if __name__ == "__main__":
    unittest.main()