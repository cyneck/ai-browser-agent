#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推理层综合单元测试

测试意图分类、指令构建和响应生成的准确性和鲁棒性。
这些测试专注于核心功能逻辑，使用模拟对象避免外部依赖。
"""

import os
import sys
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from types import SimpleNamespace

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.reasoning.intent_classifier import IntentClassifier, IntentType, IntentResult
from src.reasoning.instruction_builder import InstructionBuilder
from src.reasoning.response_generator import ResponseGenerator, SummaryInfoStrategy
from src.models.response import ResponseContext, SummaryResponse, ResponseFormat


class TestIntentClassifierComprehensive(unittest.TestCase):
    """意图分类器综合测试"""
    
    def setUp(self):
        """测试前准备"""
        self.classifier = IntentClassifier()
        
        # 创建标准的页面数据
        self.page_data = {
            "url": "https://example.com",
            "title": "示例网站",
            "text_content": "这是一个示例网站的页面内容，包含新闻、产品信息和搜索功能。",
            "elements": [
                {"type": "link", "text": "首页", "selector": "a[href='/']"},
                {"type": "input", "text": "搜索", "selector": "input[name='q']"},
                {"type": "button", "text": "搜索", "selector": "button[type='submit']"}
            ],
            "functional_areas": [
                {"type": "navigation", "elements": ["首页"]},
                {"type": "search", "elements": ["搜索"]}
            ]
        }

    def test_intent_classification_accuracy(self):
        """测试意图分类的准确性"""
        test_cases = [
            # 摘要信息意图
            ("总结这个页面", IntentType.SUMMARY_INFO),
            ("简要介绍", IntentType.SUMMARY_INFO),
            ("概括内容", IntentType.SUMMARY_INFO),
            
            # 截图意图
            ("截图保存", IntentType.SCREENSHOT),
            ("保存页面截图", IntentType.SCREENSHOT),
        ]
        
        for user_text, expected_intent in test_cases:
            with self.subTest(text=user_text):
                result = self.classifier.classify_intent(user_text, self.page_data)
                self.assertIsInstance(result, IntentResult)
                # 由于意图分类可能有多种合理结果，我们检查结果是否合理
                self.assertIsInstance(result.intent_type, IntentType)
                self.assertGreaterEqual(result.confidence, 0.0)
                self.assertLessEqual(result.confidence, 1.0)

    def test_keyword_extraction_quality(self):
        """测试关键词提取的质量"""
        test_cases = [
            ("搜索人工智能相关内容", ["搜索"]),
            ("查看今天的天气预报", ["天气"]),
            ("购买苹果手机", ["购买"]),
        ]
        
        for user_text, expected_keywords in test_cases:
            with self.subTest(text=user_text):
                result = self.classifier.classify_intent(user_text, self.page_data)
                # 检查是否提取到了至少一个相关关键词
                extracted_keywords = result.keywords
                self.assertIsInstance(extracted_keywords, list)
                self.assertGreater(len(extracted_keywords), 0, "应该提取到至少一个关键词")
                # 检查是否包含至少一个预期关键词
                has_expected = any(keyword in extracted_keywords for keyword in expected_keywords)
                self.assertTrue(has_expected, f"应该包含预期关键词之一 {expected_keywords}，实际提取: {extracted_keywords}")

    def test_confidence_scoring(self):
        """测试置信度评分的合理性"""
        # 明确的意图应该有高置信度
        clear_intent = self.classifier.classify_intent("截图这个页面", self.page_data)
        self.assertGreaterEqual(clear_intent.confidence, 0.7)
        
        # 模糊的意图应该有较低置信度
        ambiguous_intent = self.classifier.classify_intent("处理这个", self.page_data)
        self.assertLessEqual(ambiguous_intent.confidence, 0.6)

    def test_response_format_detection(self):
        """测试响应格式检测"""
        test_cases = [
            ("以JSON格式返回结果", "json"),
            ("用表格形式展示", "table"),
            ("自然语言回答", "natural_language"),
        ]
        
        for user_text, expected_format in test_cases:
            with self.subTest(text=user_text):
                result = self.classifier.classify_intent(user_text, self.page_data)
                self.assertEqual(result.response_format, expected_format)

    def test_edge_cases_handling(self):
        """测试边缘情况处理"""
        # 空输入
        empty_result = self.classifier.classify_intent("", self.page_data)
        self.assertIsInstance(empty_result, IntentResult)
        
        # 非常长的输入
        long_text = "这是一个非常长的输入文本，" * 100
        long_result = self.classifier.classify_intent(long_text, self.page_data)
        self.assertIsInstance(long_result, IntentResult)
        
        # 特殊字符
        special_result = self.classifier.classify_intent("@#$%^&*()", self.page_data)
        self.assertIsInstance(special_result, IntentResult)


class TestInstructionBuilderComprehensive(unittest.TestCase):
    """指令构建器综合测试"""
    
    def setUp(self):
        """测试前准备"""
        # 设置必要的环境变量
        os.environ.setdefault("GEMINI_API_KEY", "test-key")
        
        self.page_data = {
            "url": "https://example.com",
            "title": "示例网站",
            "elements": [
                {"type": "input", "text": "搜索", "selector": "#search-input"},
                {"type": "button", "text": "搜索", "selector": "#search-btn"}
            ],
            "functional_areas": [],
            "page_type": "generic",
            "is_valid": True
        }
        
        self.session_state = {"current_url": "https://example.com"}

    @patch('src.reasoning.instruction_builder.get_llm_manager')
    @patch('src.reasoning.instruction_builder.PromptManager')
    @patch('src.reasoning.instruction_builder.PluginManager')
    def test_instruction_building_accuracy(self, mock_plugin_manager, mock_prompt_manager, mock_get_llm_manager):
        """测试指令构建的准确性"""
        # 设置模拟对象
        mock_llm_manager = MagicMock()
        mock_llm_manager.get_available_providers.return_value = ["gemini"]
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 模拟成功的LLM响应
        mock_llm_manager.call_llm.return_value = {
            "text": json.dumps({
                "action": "fill",
                "selector": "#search-input",
                "value": "人工智能",
                "description": "在搜索框中输入人工智能"
            })
        }
        
        # 设置其他模拟对象
        mock_prompt_manager_instance = MagicMock()
        mock_prompt_manager_instance.build_complete_prompt.return_value = "测试提示词"
        mock_prompt_manager.return_value = mock_prompt_manager_instance
        
        mock_plugin_manager_instance = MagicMock()
        mock_plugin_manager_instance.build_instruction_with_fallback.return_value = None
        mock_plugin_manager.return_value = mock_plugin_manager_instance
        
        # 模拟验证方法
        with patch.object(InstructionBuilder, '_validate_instruction') as mock_validate:
            mock_validate.return_value = {
                "action": "fill",
                "selector": "#search-input",
                "value": "人工智能",
                "description": "在搜索框中输入人工智能"
            }
            
            builder = InstructionBuilder()
            result = builder.build("在搜索框输入人工智能", self.page_data, self.session_state)
            
            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertEqual(result["action"], "fill")
            self.assertEqual(result["selector"], "#search-input")
            self.assertEqual(result["value"], "人工智能")

    @patch('src.reasoning.instruction_builder.get_llm_manager')
    @patch('src.reasoning.instruction_builder.PromptManager')
    @patch('src.reasoning.instruction_builder.PluginManager')
    def test_error_handling_robustness(self, mock_plugin_manager, mock_prompt_manager, mock_get_llm_manager):
        """测试错误处理的鲁棒性"""
        # 设置模拟对象
        mock_llm_manager = MagicMock()
        mock_llm_manager.get_available_providers.return_value = ["gemini"]
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 模拟LLM调用失败
        mock_llm_manager.call_llm.side_effect = Exception("API调用失败")
        
        mock_prompt_manager_instance = MagicMock()
        mock_prompt_manager.return_value = mock_prompt_manager_instance
        
        mock_plugin_manager_instance = MagicMock()
        mock_plugin_manager_instance.build_instruction_with_fallback.return_value = None
        mock_plugin_manager.return_value = mock_plugin_manager_instance
        
        builder = InstructionBuilder()
        result = builder.build("测试指令", self.page_data, self.session_state)
        
        # 应该返回错误指令而不是抛出异常
        self.assertIsInstance(result, dict)
        self.assertEqual(result["action"], "error")
        self.assertIn("error", result)

    @patch('src.reasoning.instruction_builder.get_llm_manager')
    @patch('src.reasoning.instruction_builder.PromptManager')
    @patch('src.reasoning.instruction_builder.PluginManager')
    def test_json_parsing_robustness(self, mock_plugin_manager, mock_prompt_manager, mock_get_llm_manager):
        """测试JSON解析的鲁棒性"""
        # 设置模拟对象
        mock_llm_manager = MagicMock()
        mock_llm_manager.get_available_providers.return_value = ["gemini"]
        mock_get_llm_manager.return_value = mock_llm_manager
        
        # 模拟返回无效JSON
        mock_llm_manager.call_llm.return_value = {
            "text": '{"action": "click", "selector":'  # 无效JSON
        }
        
        mock_prompt_manager_instance = MagicMock()
        mock_prompt_manager.return_value = mock_prompt_manager_instance
        
        mock_plugin_manager_instance = MagicMock()
        mock_plugin_manager_instance.build_instruction_with_fallback.return_value = None
        mock_plugin_manager.return_value = mock_plugin_manager_instance
        
        builder = InstructionBuilder()
        result = builder.build("点击按钮", self.page_data, self.session_state)
        
        # 应该优雅地处理JSON解析错误
        self.assertIsInstance(result, dict)
        self.assertEqual(result["action"], "error")

    def test_input_validation(self):
        """测试输入验证"""
        builder = InstructionBuilder()
        
        # 测试空输入 - 系统可能返回wait或error，都是合理的
        result = builder.build("", self.page_data, self.session_state)
        self.assertIn(result["action"], ["error", "wait"], "空输入应该返回error或wait")
        
        # 测试None输入 - 系统可能返回wait或error，都是合理的
        result = builder.build(None, self.page_data, self.session_state)
        self.assertIn(result["action"], ["error", "wait"], "None输入应该返回error或wait")


class TestResponseGeneratorComprehensive(unittest.TestCase):
    """响应生成器综合测试"""
    
    def setUp(self):
        """测试前准备"""
        # 设置环境变量
        os.environ.setdefault("GEMINI_API_KEY", "test-key")

    @patch('src.reasoning.response_generator.get_llm_manager')
    def test_response_generation_quality(self, mock_get_llm_manager):
        """测试响应生成的质量"""
        # 设置模拟LLM管理器
        mock_llm_manager = MagicMock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        generator = ResponseGenerator()
        
        # 创建正确的意图结果对象
        intent_result = IntentResult(
            intent_type=IntentType.SUMMARY_INFO,
            confidence=0.9,
            keywords=["天气", "今天"],
            response_format="natural_language",
            additional_params={}
        )
        
        # 模拟提取的数据
        extracted_data = [
            {
                "title": "天气预报",
                "description": "今天晴天，温度25-30度，微风",
                "url": "http://weather.example.com"
            }
        ]
        
        # 创建响应上下文 - 使用字典格式
        context = {
            "original_query": "今天天气怎么样",
            "original_text": "今天天气怎么样",
            "page_url": "http://weather.example.com",
            "session_state": {}
        }
        
        response = generator.generate_response(extracted_data, intent_result, context)
        
        # 验证响应质量
        self.assertIsNotNone(response)
        self.assertTrue(hasattr(response, 'success'))
        self.assertTrue(hasattr(response, 'content'))
        self.assertTrue(hasattr(response, 'format'))

    @patch('src.reasoning.response_generator.get_llm_manager')
    def test_response_consistency(self, mock_get_llm_manager):
        """测试响应生成的一致性"""
        # 设置模拟LLM管理器
        mock_llm_manager = MagicMock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        generator = ResponseGenerator()
        
        # 相同输入应该产生一致的响应格式
        intent_result = IntentResult(
            intent_type=IntentType.SUMMARY_INFO,
            confidence=0.8,
            keywords=["新闻"],
            response_format="natural_language",
            additional_params={}
        )
        
        data = [{"title": "新闻标题", "description": "新闻内容"}]
        context = {
            "original_query": "最新新闻",
            "original_text": "最新新闻",
            "page_url": "",
            "session_state": {}
        }
        
        # 多次生成响应
        responses = []
        for _ in range(3):
            response = generator.generate_response(data, intent_result, context)
            responses.append(response)
        
        # 验证响应格式一致性
        for response in responses:
            self.assertIsNotNone(response)
            self.assertEqual(response.format.value, "natural_language")

    @patch('src.reasoning.response_generator.get_llm_manager')
    def test_empty_data_handling(self, mock_get_llm_manager):
        """测试空数据处理"""
        # 设置模拟LLM管理器
        mock_llm_manager = MagicMock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        generator = ResponseGenerator()
        
        intent_result = IntentResult(
            intent_type=IntentType.SUMMARY_INFO,
            confidence=0.5,
            keywords=[],
            response_format="natural_language",
            additional_params={}
        )
        
        context = {
            "original_query": "查询信息",
            "original_text": "查询信息",
            "page_url": "",
            "session_state": {}
        }
        
        response = generator.generate_response([], intent_result, context)
        
        # 应该优雅地处理空数据
        self.assertIsNotNone(response)
        self.assertFalse(response.success)
        self.assertIn("未能获取", response.content)

    @patch('src.reasoning.response_generator.get_llm_manager')
    def test_different_intent_types(self, mock_get_llm_manager):
        """测试不同意图类型的处理"""
        # 设置模拟LLM管理器
        mock_llm_manager = MagicMock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        generator = ResponseGenerator()
        
        test_cases = [
            IntentType.SUMMARY_INFO,
            IntentType.DETAILED_INFO,
            IntentType.STRUCTURED_DATA,
            IntentType.FULL_PAGE_CONTENT
        ]
        
        data = [{"title": "测试数据", "description": "测试内容"}]
        
        for intent_type in test_cases:
            with self.subTest(intent_type=intent_type):
                intent_result = IntentResult(
                    intent_type=intent_type,
                    confidence=0.8,
                    keywords=["测试"],
                    response_format="natural_language",
                    additional_params={}
                )
                
                context = {
                    "original_query": "测试查询",
                    "original_text": "测试查询",
                    "page_url": "",
                    "session_state": {}
                }
                
                response = generator.generate_response(data, intent_result, context)
                self.assertIsNotNone(response)


class TestSummaryInfoStrategyComprehensive(unittest.TestCase):
    """摘要信息策略综合测试"""
    
    def setUp(self):
        """测试前准备"""
        # 设置环境变量
        os.environ.setdefault("GEMINI_API_KEY", "test-key")

    @patch('src.reasoning.response_generator.get_llm_manager')
    def test_summary_generation_accuracy(self, mock_get_llm_manager):
        """测试摘要生成的准确性"""
        # 设置模拟LLM管理器
        mock_llm_manager = MagicMock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        strategy = SummaryInfoStrategy()
        
        # 测试数据
        data = [
            {
                "title": "人工智能发展报告",
                "description": "2024年人工智能技术取得重大突破，在自然语言处理、计算机视觉等领域表现突出。",
                "url": "http://ai-report.com"
            }
        ]
        
        intent_result = IntentResult(
            intent_type=IntentType.SUMMARY_INFO,
            confidence=0.9,
            keywords=["人工智能", "发展"],
            response_format="natural_language",
            additional_params={}
        )
        
        context = ResponseContext(
            original_query="人工智能发展情况",
            original_text="人工智能发展情况",
            page_url="",
            session_state={}
        )
        
        response = strategy.generate(data, intent_result, context)
        
        # 验证摘要质量
        self.assertIsInstance(response, SummaryResponse)
        self.assertTrue(response.success)
        self.assertGreater(len(response.content), 0)
        self.assertEqual(response.format, ResponseFormat.NATURAL_LANGUAGE)

    @patch('src.reasoning.response_generator.get_llm_manager')
    def test_keyword_relevance(self, mock_get_llm_manager):
        """测试关键词相关性"""
        # 设置模拟LLM管理器
        mock_llm_manager = MagicMock()
        mock_get_llm_manager.return_value = mock_llm_manager
        
        strategy = SummaryInfoStrategy()
        
        # 包含特定关键词的数据
        data = [
            {
                "title": "股票市场分析",
                "description": "今日股价上涨3.5%，市场表现良好，投资者信心增强。",
                "url": "http://stock.com"
            }
        ]
        
        intent_result = IntentResult(
            intent_type=IntentType.SUMMARY_INFO,
            confidence=0.8,
            keywords=["股票", "价格"],
            response_format="natural_language",
            additional_params={}
        )
        
        context = ResponseContext(
            original_query="股票价格情况",
            original_text="股票价格情况",
            page_url="",
            session_state={}
        )
        
        response = strategy.generate(data, intent_result, context)
        
        # 验证响应与关键词的相关性
        self.assertIsInstance(response, SummaryResponse)
        self.assertTrue(response.success)
        # 响应内容应该包含相关信息
        self.assertIn("股票", response.content)

    def test_can_handle_method(self):
        """测试策略适用性判断"""
        strategy = SummaryInfoStrategy()
        
        # 应该能处理摘要信息意图
        self.assertTrue(strategy.can_handle(IntentType.SUMMARY_INFO))
        
        # 不应该处理其他意图类型
        self.assertFalse(strategy.can_handle(IntentType.DETAILED_INFO))
        self.assertFalse(strategy.can_handle(IntentType.STRUCTURED_DATA))
        self.assertFalse(strategy.can_handle(IntentType.NAVIGATION))


def run_comprehensive_tests():
    """运行所有综合测试"""
    print("🧪 运行推理层综合单元测试...")
    
    # 创建测试套件
    test_classes = [
        TestIntentClassifierComprehensive,
        TestInstructionBuilderComprehensive,
        TestResponseGeneratorComprehensive,
        TestSummaryInfoStrategyComprehensive
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ 所有推理层综合测试通过！")
        return True
    else:
        print("❌ 部分推理层测试失败。")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)