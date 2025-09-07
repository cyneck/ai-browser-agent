#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM提取器测试

测试AI浏览器代理的LLM-based内容提取功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.reasoning.llm_extractor import LLMExtractor


class TestLLMExtractor(unittest.TestCase):
    """测试LLM提取器"""
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def setUp(self, mock_get_config, mock_get_llm_manager):
        """设置测试环境"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        self.mock_llm_manager = Mock()
        mock_get_llm_manager.return_value = self.mock_llm_manager
        
        # 创建提取器实例
        self.extractor = LLMExtractor()
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_extract_information_success(self, mock_get_config, mock_get_llm_manager):
        """测试信息提取成功"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        mock_llm_manager = Mock()
        mock_llm_manager.call_llm.return_value = {
            "text": '{"extracted_content": "今天天气是晴天，温度23°C~32°C"}'
        }
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = [
            {
                "title": "北京天气预报",
                "description": "今天北京晴转多云，温度23-32°C，微风2级",
                "url": "http://weather.com.cn/beijing"
            }
        ]
        user_query = "今日天气是怎么样"
        
        # 执行提取
        extractor = LLMExtractor()
        result = extractor.extract_information(search_results, user_query)
        
        # 验证结果
        self.assertEqual(result, "今天天气是晴天，温度23°C~32°C")
        mock_llm_manager.call_llm.assert_called_once()
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_extract_information_with_plain_text_response(self, mock_get_config, mock_get_llm_manager):
        """测试信息提取返回纯文本"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        mock_llm_manager = Mock()
        mock_llm_manager.call_llm.return_value = {
            "text": "今天天气是晴天，温度23°C~32°C"
        }
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = [
            {
                "title": "北京天气预报",
                "description": "今天北京晴转多云，温度23-32°C，微风2级",
                "url": "http://weather.com.cn/beijing"
            }
        ]
        user_query = "今日天气是怎么样"
        
        # 执行提取
        extractor = LLMExtractor()
        result = extractor.extract_information(search_results, user_query)
        
        # 验证结果
        self.assertEqual(result, "今天天气是晴天，温度23°C~32°C")
        mock_llm_manager.call_llm.assert_called_once()
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_extract_information_failure(self, mock_get_config, mock_get_llm_manager):
        """测试信息提取失败"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器抛出异常
        mock_llm_manager = Mock()
        mock_llm_manager.call_llm.side_effect = Exception("LLM调用失败")
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = [
            {
                "title": "北京天气预报",
                "description": "今天北京晴转多云，温度23-32°C，微风2级",
                "url": "http://weather.com.cn/beijing"
            }
        ]
        user_query = "今日天气是怎么样"
        
        # 执行提取
        extractor = LLMExtractor()
        result = extractor.extract_information(search_results, user_query)
        
        # 验证结果
        self.assertIsNone(result)
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_extract_information_empty_results(self, mock_get_config, mock_get_llm_manager):
        """测试空结果的信息提取"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        mock_llm_manager = Mock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = []
        user_query = "今日天气是怎么样"
        
        # 执行提取
        extractor = LLMExtractor()
        result = extractor.extract_information(search_results, user_query)
        
        # 验证结果
        self.assertIsNone(result)
        # 当搜索结果为空时，不应该调用LLM
        mock_llm_manager.call_llm.assert_not_called()
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_extract_structured_data_success(self, mock_get_config, mock_get_llm_manager):
        """测试结构化数据提取成功"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        mock_llm_manager = Mock()
        mock_llm_manager.call_llm.return_value = {
            "text": json.dumps({
                "structured_data": [
                    {"name": "产品A", "price": "100元"},
                    {"name": "产品B", "price": "200元"}
                ],
                "data_type": "商品信息"
            }, ensure_ascii=False)
        }
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = [
            {
                "title": "商品列表",
                "description": "产品A价格100元，产品B价格200元",
                "url": "http://shop.example.com"
            }
        ]
        structure_type = "table"
        
        # 执行提取
        extractor = LLMExtractor()
        result = extractor.extract_structured_data(search_results, structure_type)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn("structured_data", result)
        self.assertEqual(len(result["structured_data"]), 2)
        mock_llm_manager.call_llm.assert_called_once()
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_build_extraction_prompt(self, mock_get_config, mock_get_llm_manager):
        """测试提取提示词构建"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        mock_llm_manager = Mock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = [
            {
                "title": "测试标题",
                "description": "测试描述",
                "url": "http://example.com"
            }
        ]
        user_query = "测试查询"
        
        # 创建提取器实例
        extractor = LLMExtractor()
        
        # 使用反射访问私有方法
        prompt = extractor._build_extraction_prompt(search_results, user_query)
        
        # 验证提示词包含关键元素
        self.assertIn("测试查询", prompt)
        self.assertIn("测试标题", prompt)
        self.assertIn("测试描述", prompt)
        self.assertIn("JSON格式", prompt)
    
    @patch('src.reasoning.llm_extractor.get_llm_manager')
    @patch('src.reasoning.llm_extractor.get_config')
    def test_build_structured_extraction_prompt(self, mock_get_config, mock_get_llm_manager):
        """测试结构化数据提取提示词构建"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "LLM_PROVIDER": "gemini",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 模拟LLM管理器
        mock_llm_manager = Mock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 测试数据
        search_results = [
            {
                "title": "测试标题",
                "description": "测试描述",
                "url": "http://example.com"
            }
        ]
        structure_type = "table"
        
        # 创建提取器实例
        extractor = LLMExtractor()
        
        # 使用反射访问私有方法
        prompt = extractor._build_structured_extraction_prompt(search_results, structure_type)
        
        # 验证提示词包含关键元素
        self.assertIn("结构化数据", prompt)
        self.assertIn("table", prompt)
        self.assertIn("测试标题", prompt)
        self.assertIn("JSON格式", prompt)


def run_tests():
    """运行测试"""
    print("🧪 开始LLM提取器测试")
    print("=" * 50)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestLLMExtractor))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    if result.wasSuccessful():
        print("✅ 所有测试通过！LLM提取器工作正常。")
        print(f"📋 运行测试: {result.testsRun}")
        print(f"❌ 失败测试: {len(result.failures)}")
        print(f"🔥 错误测试: {len(result.errors)}")
    else:
        print("❌ 部分测试失败")
        if result.failures:
            print("\n失败的测试:")
            for test, trace in result.failures:
                print(f"  - {test}: {trace}")
        if result.errors:
            print("\n错误的测试:")
            for test, trace in result.errors:
                print(f"  - {test}: {trace}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)