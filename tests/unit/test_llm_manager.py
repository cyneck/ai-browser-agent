#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM管理器测试

测试AI浏览器代理的多LLM提供商支持功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.common.llm_manager import LLMManager, GeminiProvider, OpenAIProvider, OllamaProvider
from src.common.config import get_config


class TestLLMManager(unittest.TestCase):
    """测试LLM管理器"""
    
    def setUp(self):
        """设置测试环境"""
        pass
    
    @patch('src.common.llm_manager.get_config')
    def test_initialize_providers(self, mock_get_config):
        """测试提供商初始化"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "GEMINI_API_KEY": "test-gemini-key",
                "OPENAI_API_KEY": "test-openai-key",
                "QWEN_API_KEY": "test-qwen-key",
                "OLLAMA_ENABLED": "true"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 创建LLM管理器
        manager = LLMManager()
        
        # 验证提供商已初始化
        self.assertIn("gemini", manager.providers)
        self.assertIn("openai", manager.providers)
        self.assertIn("qwen", manager.providers)
        self.assertIn("ollama", manager.providers)
        
        # 验证提供商类型
        self.assertIsInstance(manager.providers["gemini"], GeminiProvider)
        self.assertIsInstance(manager.providers["openai"], OpenAIProvider)
        self.assertIsInstance(manager.providers["qwen"], OpenAIProvider)  # Qwen使用OpenAI兼容接口
        self.assertIsInstance(manager.providers["ollama"], OllamaProvider)
    
    @patch('src.common.llm_manager.get_config')
    def test_get_available_providers(self, mock_get_config):
        """测试获取可用提供商"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "GEMINI_API_KEY": "test-gemini-key",
                "OPENAI_API_KEY": "",  # 空API密钥，不应初始化
                "QWEN_API_KEY": "test-qwen-key",
                "OLLAMA_ENABLED": "false"  # 禁用Ollama
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 创建LLM管理器（需要确保在创建时OLLAMA_ENABLED为false）
        with patch.dict('os.environ', {'OLLAMA_ENABLED': 'false'}):
            manager = LLMManager()
        
        # 验证可用提供商
        available = manager.get_available_providers()
        self.assertIn("gemini", available)
        self.assertIn("qwen", available)
        self.assertNotIn("openai", available)
        self.assertNotIn("ollama", available)
    
    def test_extract_json_from_response(self):
        """测试从响应中提取JSON"""
        manager = LLMManager()
        
        # 测试包含JSON代码块的响应
        response_with_json = '''
        这是LLM的响应，包含JSON指令：
        ```json
        {
            "action": "navigate",
            "value": "https://www.baidu.com",
            "description": "导航到百度"
        }
        ```
        这是响应的其余部分。
        '''
        
        result = manager.extract_json_from_response(response_with_json)
        self.assertEqual(result["action"], "navigate")
        self.assertEqual(result["value"], "https://www.baidu.com")
        self.assertEqual(result["description"], "导航到百度")
    
    @patch('src.common.llm_manager.get_config')
    def test_call_llm_with_gemini(self, mock_get_config):
        """测试调用Gemini"""
        # 模拟配置
        def config_side_effect(key, default=None):
            config_map = {
                "GEMINI_API_KEY": "test-gemini-key",
                "GEMINI_MODEL": "gemini-pro"
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        # 创建LLM管理器
        manager = LLMManager()
        
        # 模拟Gemini提供商
        with patch.object(manager.providers["gemini"], 'call_llm') as mock_call:
            mock_call.return_value = {"text": '{"action": "navigate", "value": "https://example.com"}'}
            
            # 调用LLM
            result = manager.call_llm("测试提示词", "gemini", "gemini-pro")
            
            # 验证调用
            mock_call.assert_called_once_with("测试提示词", "gemini-pro")
            self.assertEqual(result["text"], '{"action": "navigate", "value": "https://example.com"}')


class TestGeminiProvider(unittest.TestCase):
    """测试Gemini提供商"""
    
    def test_gemini_call(self):
        """测试Gemini调用"""
        # 创建提供商
        provider = GeminiProvider("test-api-key")
        
        # 如果genai模块未安装，则跳过测试
        if provider.genai is None:
            self.skipTest("Google Generative AI SDK not installed")
        
        # 模拟响应
        mock_response = Mock()
        mock_response.text = '{"action": "navigate", "value": "https://example.com"}'
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        
        with patch.object(provider.genai, 'configure') as mock_configure, \
             patch.object(provider.genai, 'GenerativeModel', return_value=mock_model) as mock_generative_model:
            
            # 调用提供商
            result = provider.call_llm("测试提示词", "gemini-pro")
            
            # 验证调用
            mock_configure.assert_called_once_with(api_key="test-api-key")
            mock_generative_model.assert_called_once_with("gemini-pro")
            mock_model.generate_content.assert_called_once_with("测试提示词")
            self.assertEqual(result["text"], '{"action": "navigate", "value": "https://example.com"}')


class TestOpenAIProvider(unittest.TestCase):
    """测试OpenAI提供商"""
    
    def test_openai_call(self):
        """测试OpenAI调用"""
        # 创建提供商
        provider = OpenAIProvider("test-api-key")
        
        # 如果openai模块未安装，则跳过测试
        if provider.openai_module is None:
            self.skipTest("OpenAI SDK not installed")
        
        # 模拟响应
        mock_choice = Mock()
        mock_choice.message.content = '{"action": "navigate", "value": "https://example.com"}'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider.openai_module, 'OpenAI', return_value=mock_client) as mock_openai_constructor:
            # 调用提供商
            result = provider.call_llm("测试提示词", "gpt-3.5-turbo")
            
            # 验证调用
            mock_openai_constructor.assert_called_once_with(api_key="test-api-key")
            mock_client.chat.completions.create.assert_called_once()
            self.assertEqual(result["text"], '{"action": "navigate", "value": "https://example.com"}')


class TestOllamaProvider(unittest.TestCase):
    """测试Ollama提供商"""
    
    def test_ollama_call(self):
        """测试Ollama调用"""
        # 创建提供商
        provider = OllamaProvider("http://localhost:11434")
        
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {"response": '{"action": "navigate", "value": "https://example.com"}'}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            # 调用提供商
            result = provider.call_llm("测试提示词", "llama2")
            
            # 验证调用
            mock_post.assert_called_once()
            self.assertEqual(result["text"], '{"action": "navigate", "value": "https://example.com"}')


def run_tests():
    """运行测试"""
    print("🧪 开始LLM管理器测试")
    print("=" * 50)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestLLMManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGeminiProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestOpenAIProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaProvider))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    if result.wasSuccessful():
        print("✅ 所有测试通过！LLM管理器工作正常。")
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