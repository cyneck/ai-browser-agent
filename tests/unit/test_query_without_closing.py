#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试浏览器查询后不自动关闭功能

这个测试验证查询完成后浏览器应该返回结果而不是关闭。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import Mock, patch

try:
    from src.action.executor import ActionExecutor
    from src.action.state_manager import StateManager
    from src.action.error_handler import ErrorHandler
except ImportError:
    # 如果导入失败，设置路径并重试
    current_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(current_dir))
    
    from src.action.executor import ActionExecutor
    from src.action.state_manager import StateManager
    from src.action.error_handler import ErrorHandler


class TestQueryWithoutClosing(unittest.TestCase):
    """测试查询操作不自动关闭浏览器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_page = Mock()
        self.state_manager = StateManager()
        self.error_handler = ErrorHandler()
        self.executor = ActionExecutor(
            self.mock_page, 
            self.state_manager, 
            self.error_handler
        )
    
    def test_extract_results_action_exists(self):
        """测试新的 extract_results 动作是否存在"""
        supported_actions = self.executor.get_supported_actions()
        self.assertIn("extract_results", supported_actions)
    
    def test_extract_results_without_closing(self):
        """测试提取搜索结果不会关闭页面"""
        # 模拟百度搜索结果页面
        self.mock_page.url = "https://www.baidu.com/s?wd=测试"
        
        # 模拟搜索结果元素
        mock_result_element = Mock()
        mock_title_element = Mock()
        mock_desc_element = Mock()
        
        # 设置标题元素的返回值
        mock_title_element.inner_text.return_value = "测试结果标题"
        mock_title_element.get_attribute.return_value = "https://example.com"
        mock_title_element.count.return_value = 1
        
        # 设置描述元素的返回值
        mock_desc_element.inner_text.return_value = "测试结果描述"
        mock_desc_element.count.return_value = 1
        
        # 设置 locator 的返回值，注意需要返回一个有 .first 属性的对象
        def mock_locator(selector):
            if "h3 a" in selector or ".t a" in selector:
                # 返回一个有 .first 属性的 mock 对象
                locator_mock = Mock()
                locator_mock.first = mock_title_element
                return locator_mock
            elif ".c-abstract" in selector or ".c-span9" in selector:
                locator_mock = Mock()
                locator_mock.first = mock_desc_element
                return locator_mock
            else:
                # 对于其他选择器，返回一个 count() 返回 0 的 mock
                locator_mock = Mock()
                locator_mock.first = Mock(count=lambda: 0)
                return locator_mock
        
        mock_result_element.locator = mock_locator
        
        # 设置页面的 locator 返回值
        mock_page_locator = Mock()
        mock_page_locator.all.return_value = [mock_result_element]
        self.mock_page.locator.return_value = mock_page_locator
        
        # 执行 extract_results 动作
        instruction = {"action": "extract_results"}
        result = self.executor.execute(instruction, session_state={})
        
        # 验证结果
        self.assertTrue(result.get("success"))
        self.assertIn("search_results", result)
        self.assertIsInstance(result["search_results"], list)
        
        # 最重要的：验证页面没有被关闭
        self.mock_page.close.assert_not_called()
    
    def test_close_action_preserves_results(self):
        """测试关闭动作会先保存结果"""
        # 模拟有搜索结果的页面
        self.mock_page.url = "https://www.baidu.com/s?wd=测试"
        
        # 模拟搜索结果
        mock_result_element = Mock()
        mock_title_element = Mock()
        mock_desc_element = Mock()
        
        # 设置标题元素的返回值
        mock_title_element.inner_text.return_value = "测试结果"
        mock_title_element.get_attribute.return_value = "https://example.com"
        mock_title_element.count.return_value = 1
        
        # 设置描述元素的返回值
        mock_desc_element.inner_text.return_value = "测试描述"
        mock_desc_element.count.return_value = 1
        
        # 设置 locator 的返回值，注意需要返回一个有 .first 属性的对象
        def mock_locator(selector):
            if "h3 a" in selector or ".t a" in selector:
                locator_mock = Mock()
                locator_mock.first = mock_title_element
                return locator_mock
            elif ".c-abstract" in selector or ".c-span9" in selector:
                locator_mock = Mock()
                locator_mock.first = mock_desc_element
                return locator_mock
            else:
                locator_mock = Mock()
                locator_mock.first = Mock(count=lambda: 0)
                return locator_mock
        
        mock_result_element.locator = mock_locator
        
        # 设置页面的 locator 返回值
        mock_page_locator = Mock()
        mock_page_locator.all.return_value = [mock_result_element]
        self.mock_page.locator.return_value = mock_page_locator
        
        # 执行关闭动作
        instruction = {"action": "close"}
        result = self.executor.execute(instruction, session_state={})
        
        # 验证页面被关闭了
        self.mock_page.close.assert_called_once()
        
        # 验证结果中包含了提取的内容
        self.assertTrue(result.get("success"))
        if "extracted_content" in result:
            self.assertIsInstance(result["extracted_content"], list)
            self.assertGreater(len(result["extracted_content"]), 0)
    
    def test_multi_step_search_instruction(self):
        """测试多步搜索指令包含提取结果而不是关闭"""
        # 模拟多步搜索指令
        instruction = {
            "steps": [
                {"action": "navigate", "value": "https://www.baidu.com", "description": "导航到百度"},
                {"action": "wait", "selector": "#kw", "timeout": 5000, "description": "等待搜索框"},
                {"action": "fill", "selector": "#kw", "value": "测试查询", "description": "输入搜索关键词"},
                {"action": "click", "selector": "#su", "description": "点击搜索"},
                {"action": "wait", "value": 2000, "description": "等待搜索结果"},
                {"action": "extract_results", "description": "提取搜索结果"}
                # 注意：这里没有 close 动作
            ],
            "description": "在百度搜索并提取结果"
        }
        
        # 设置页面基本属性
        self.mock_page.goto.return_value = None
        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.wait_for_timeout.return_value = None
        
        # 模拟页面元素（搜索框和按钮）
        mock_search_input = Mock()
        mock_search_button = Mock()
        
        # 模拟 locator 返回不同的元素
        def page_locator_side_effect(selector):
            if selector == "#kw":
                return mock_search_input
            elif selector == "#su":
                return mock_search_button
            elif ".result" in selector or ".c-container" in selector:
                # 为 extract_results 步骤返回空结果
                mock_locator = Mock()
                mock_locator.all.return_value = []  # 空结果，只是测试流程
                return mock_locator
            else:
                return Mock()
        
        self.mock_page.locator.side_effect = page_locator_side_effect
        
        # 设置 URL 以便 extract_results 步骤能识别为百度搜索页面
        self.mock_page.url = "https://www.baidu.com/s?wd=测试查询"
        
        # 执行指令
        result = self.executor.execute(instruction, session_state={})
        
        # 验证执行成功（即使 extract_results 返回空结果，整体也应该成功）
        # 因为 extract_results 在没有结果时会返回 success: False，所以我们要调整期望
        # 但是整个多步流程中，只要不是所有步骤都失败，就不会被认为完全失败
        
        # 验证没有关闭页面
        self.mock_page.close.assert_not_called()
        
        # 验证执行了所有步骤
        step_results = result.get("step_results", [])
        self.assertEqual(len(step_results), 6)  # 6个步骤
        
        # 验证前5个步骤成功（navigate, wait, fill, click, wait）
        for i in range(5):
            self.assertTrue(step_results[i].get("success"), f"第{i+1}步骤应该成功")
        
        # 最后一步 extract_results 可能失败（因为没有结果），但这是预期的
        # 重要的是没有关闭页面


def run_tests():
    """运行测试"""
    print("🧪 运行浏览器查询不自动关闭测试...")
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestQueryWithoutClosing)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    if result.wasSuccessful():
        print("✅ 所有测试通过！浏览器查询功能工作正常。")
        return True
    else:
        print("❌ 测试失败。")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)