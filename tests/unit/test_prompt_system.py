#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Prompt Management System

Tests all components of the new prompt system including:
- SystemPrompts
- UserPrompts  
- SelectorRules
- PromptFactory
- PromptManager
"""

import unittest
import json
from src.prompts.prompt_manager import PromptManager
from src.prompts.system_prompts import SystemPrompts
from src.prompts.user_prompts import UserPrompts
from src.prompts.selector_rules import SelectorRules
from src.prompts.prompt_factory import PromptFactory


class TestSystemPrompts(unittest.TestCase):
    """Test SystemPrompts functionality"""
    
    def setUp(self):
        self.system_prompts = SystemPrompts()
    
    def test_get_default_system_prompt(self):
        """Test getting default system prompt"""
        prompt = self.system_prompts.get_default_system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("网页自动化助手", prompt)
        self.assertIn("JSON格式指令", prompt)
    
    def test_get_enhanced_system_prompt(self):
        """Test getting enhanced system prompt"""
        prompt = self.system_prompts.get_enhanced_system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("高级的网页自动化助手", prompt)
        self.assertIn("一次性完整规划", prompt)
    
    def test_get_action_types(self):
        """Test getting supported action types"""
        actions = self.system_prompts.get_action_types()
        self.assertIsInstance(actions, dict)
        self.assertIn("navigate", actions)
        self.assertIn("click", actions)
        self.assertIn("fill", actions)
        self.assertTrue(len(actions) > 10)
    
    def test_get_json_format_examples(self):
        """Test getting JSON format examples"""
        examples = self.system_prompts.get_json_format_examples()
        self.assertIsInstance(examples, dict)
        self.assertIn("single_step", examples)
        self.assertIn("multi_step", examples)
        # Test that examples are valid JSON-like strings
        self.assertIn("action", examples["single_step"])
        self.assertIn("steps", examples["multi_step"])
    
    def test_get_prompt_by_type(self):
        """Test getting prompts by type"""
        default_prompt = self.system_prompts.get_prompt_by_type("default")
        enhanced_prompt = self.system_prompts.get_prompt_by_type("enhanced")
        
        self.assertNotEqual(default_prompt, enhanced_prompt)
        
        # Test invalid type
        with self.assertRaises(ValueError):
            self.system_prompts.get_prompt_by_type("invalid")


class TestUserPrompts(unittest.TestCase):
    """Test UserPrompts functionality"""
    
    def setUp(self):
        self.user_prompts = UserPrompts()
        self.sample_page_data = {
            "url": "https://example.com",
            "title": "Test Page",
            "page_type": "website",
            "elements": [{"tag": "input", "id": "search"}],
            "functional_areas": [{"area": "navigation"}],
            "aria_snapshot": {"role": "main"}
        }
    
    def test_build_basic_user_prompt(self):
        """Test building basic user prompt"""
        user_text = "点击搜索按钮"
        prompt = self.user_prompts.build_basic_user_prompt(user_text, self.sample_page_data)
        
        self.assertIn("当前页面信息", prompt)
        self.assertIn("https://example.com", prompt)
        self.assertIn("Test Page", prompt)
        self.assertIn("点击搜索按钮", prompt)
    
    def test_build_enhanced_user_prompt(self):
        """Test building enhanced user prompt with context"""
        user_text = "搜索AI技术"
        context_analysis = {
            "search_intent": True,
            "search_keywords": ["AI技术"],
            "interaction_type": "search"
        }
        
        prompt = self.user_prompts.build_enhanced_user_prompt(
            user_text, self.sample_page_data, context_analysis
        )
        
        self.assertIn("搜索意图识别", prompt)
        self.assertIn("AI技术", prompt)
        self.assertIn("交互类型: search", prompt)
    
    def test_add_conversation_history(self):
        """Test adding conversation history to prompts"""
        base_prompt = "基础提示词"
        history = [
            {"role": "user", "content": "第一个消息"},
            {"role": "assistant", "content": "第一个回复"}
        ]
        
        prompt_with_history = self.user_prompts.add_conversation_history(base_prompt, history)
        
        self.assertIn("对话历史", prompt_with_history)
        self.assertIn("第一个消息", prompt_with_history)
        self.assertIn("第一个回复", prompt_with_history)
        self.assertIn("基础提示词", prompt_with_history)
    
    def test_format_page_data(self):
        """Test formatting page data for templates"""
        formatted = self.user_prompts.format_page_data(self.sample_page_data)
        
        self.assertIsInstance(formatted, dict)
        self.assertEqual(formatted["url"], "https://example.com")
        self.assertEqual(formatted["title"], "Test Page")
        self.assertIn("input", formatted["elements"])


class TestSelectorRules(unittest.TestCase):
    """Test SelectorRules functionality"""
    
    def setUp(self):
        self.selector_rules = SelectorRules()
    
    def test_get_selector_principles(self):
        """Test getting selector principles"""
        principles = self.selector_rules.get_selector_principles()
        self.assertIsInstance(principles, str)
        self.assertIn("选择器生成原则", principles)
        self.assertIn("优先使用稳定的唯一标识符", principles)
    
    def test_get_precision_guidelines(self):
        """Test getting precision guidelines"""
        guidelines = self.selector_rules.get_precision_guidelines()
        self.assertIsInstance(guidelines, str)
        self.assertIn("确保选择器精确性", guidelines)
        self.assertIn("匹配唯一元素", guidelines)
    
    def test_get_selector_priority_list(self):
        """Test getting selector priority list"""
        priorities = self.selector_rules.get_selector_priority_list()
        self.assertIsInstance(priorities, list)
        self.assertTrue(len(priorities) >= 3)
        
        # Check first priority item structure
        first_priority = priorities[0]
        self.assertIn("priority", first_priority)
        self.assertIn("category", first_priority)
        self.assertIn("types", first_priority)
        self.assertEqual(first_priority["priority"], 1)
    
    def test_get_fragile_selectors(self):
        """Test getting fragile selectors to avoid"""
        fragile = self.selector_rules.get_fragile_selectors()
        self.assertIsInstance(fragile, list)
        self.assertTrue(len(fragile) > 0)
        
        # Check structure of fragile selector items
        for item in fragile:
            self.assertIn("pattern", item)
            self.assertIn("category", item)
            self.assertIn("reason", item)
    
    def test_get_best_practices(self):
        """Test getting selector best practices"""
        practices = self.selector_rules.get_best_practices()
        self.assertIsInstance(practices, list)
        self.assertTrue(len(practices) >= 10)
        
        # Check that all practices are strings
        for practice in practices:
            self.assertIsInstance(practice, str)
    
    def test_validate_selector_precision(self):
        """Test selector precision validation"""
        # Test good selector
        good_result = self.selector_rules.validate_selector_precision("#submit-button")
        self.assertGreater(good_result["score"], 80)
        self.assertEqual(good_result["recommendation"], "good")
        
        # Test fragile selector
        bad_result = self.selector_rules.validate_selector_precision("div:nth-child(3)")
        self.assertLess(bad_result["score"], 80)
        self.assertNotEqual(bad_result["recommendation"], "good")
        self.assertTrue(len(bad_result["issues"]) > 0)
    
    def test_generate_selector_documentation(self):
        """Test generating complete selector documentation"""
        doc = self.selector_rules.generate_selector_documentation()
        self.assertIsInstance(doc, str)
        self.assertIn("CSS选择器生成规则", doc)
        self.assertIn("最佳实践清单", doc)
        self.assertIn("推荐的选择器", doc)


class TestPromptFactory(unittest.TestCase):
    """Test PromptFactory functionality"""
    
    def setUp(self):
        self.system_prompts = SystemPrompts()
        self.user_prompts = UserPrompts()
        self.selector_rules = SelectorRules()
        self.factory = PromptFactory(
            self.system_prompts, 
            self.user_prompts, 
            self.selector_rules
        )
        
        self.sample_page_data = {
            "url": "https://example.com",
            "title": "Test Page",
            "elements": [],
            "functional_areas": []
        }
    
    def test_build_system_prompt(self):
        """Test building system prompt with selector rules"""
        prompt = self.factory.build_system_prompt("default")
        
        # Should contain system prompt and selector rules
        self.assertIn("网页自动化助手", prompt)
        self.assertIn("选择器生成原则", prompt)
        self.assertIn("确保选择器精确性", prompt)
    
    def test_build_user_prompt(self):
        """Test building user prompt"""
        user_text = "点击按钮"
        prompt = self.factory.build_user_prompt(user_text, self.sample_page_data)
        
        self.assertIn("当前页面信息", prompt)
        self.assertIn("点击按钮", prompt)
    
    def test_build_complete_prompt(self):
        """Test building complete prompt"""
        user_text = "点击按钮"
        complete_prompt = self.factory.build_complete_prompt(
            user_text, self.sample_page_data
        )
        
        # Should contain both system and user parts
        self.assertIn("网页自动化助手", complete_prompt)
        self.assertIn("当前页面信息", complete_prompt)
        self.assertIn("点击按钮", complete_prompt)
    
    def test_build_enhanced_prompt(self):
        """Test building enhanced prompt with context"""
        user_text = "搜索产品"
        conversation_history = []
        context_analysis = {
            "search_intent": True,
            "search_keywords": ["产品"]
        }
        
        enhanced_prompt = self.factory.build_enhanced_prompt(
            user_text, self.sample_page_data, conversation_history, context_analysis
        )
        
        self.assertIn("高级的网页自动化助手", enhanced_prompt)
        self.assertIn("搜索意图识别", enhanced_prompt)
        self.assertIn("产品", enhanced_prompt)
    
    def test_validate_prompt_components(self):
        """Test validating prompt components"""
        validation = self.factory.validate_prompt_components()
        
        self.assertIsInstance(validation, dict)
        self.assertTrue(validation["system_prompts"])
        self.assertTrue(validation["user_prompts"])
        self.assertTrue(validation["selector_rules"])
        self.assertTrue(validation["default_system_prompt"])
    
    def test_get_prompt_metadata(self):
        """Test getting prompt metadata"""
        metadata = self.factory.get_prompt_metadata()
        
        self.assertIn("prompt_type", metadata)
        self.assertIn("system_prompt_length", metadata)
        self.assertIn("supported_actions", metadata)
        self.assertTrue(metadata["includes_selector_rules"])


class TestPromptManager(unittest.TestCase):
    """Test PromptManager functionality"""
    
    def setUp(self):
        self.manager = PromptManager()
        self.sample_page_data = {
            "url": "https://example.com",
            "title": "Test Page",
            "elements": [],
            "functional_areas": []
        }
    
    def test_build_system_prompt(self):
        """Test system prompt building through manager"""
        prompt = self.manager.build_system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("网页自动化助手", prompt)
    
    def test_build_user_prompt(self):
        """Test user prompt building through manager"""
        user_text = "测试指令"
        prompt = self.manager.build_user_prompt(user_text, self.sample_page_data)
        self.assertIn("测试指令", prompt)
    
    def test_build_complete_prompt(self):
        """Test complete prompt building through manager"""
        user_text = "测试指令"
        prompt = self.manager.build_complete_prompt(user_text, self.sample_page_data)
        
        # Should be a complete prompt with both system and user parts
        self.assertIn("网页自动化助手", prompt)
        self.assertIn("测试指令", prompt)
        self.assertTrue(len(prompt) > 1000)  # Should be substantial
    
    def test_build_enhanced_prompt(self):
        """Test enhanced prompt building through manager"""
        user_text = "搜索商品"
        conversation_history = []
        context_analysis = {"search_intent": True}
        
        prompt = self.manager.build_enhanced_prompt(
            user_text, self.sample_page_data, conversation_history, context_analysis
        )
        
        self.assertIn("高级的网页自动化助手", prompt)
        self.assertIn("搜索商品", prompt)


class TestPromptSystemIntegration(unittest.TestCase):
    """Integration tests for the complete prompt system"""
    
    def setUp(self):
        self.manager = PromptManager()
    
    def test_end_to_end_prompt_generation(self):
        """Test complete end-to-end prompt generation"""
        # Simulate a realistic scenario
        user_text = "在百度搜索人工智能"
        page_data = {
            "url": "https://www.baidu.com",
            "title": "百度一下，你就知道",
            "elements": [
                {"tag": "input", "name": "wd", "id": "kw"},
                {"tag": "input", "type": "submit", "value": "百度一下"}
            ],
            "functional_areas": [{"area": "search"}]
        }
        conversation_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我是网页自动化助手"}
        ]
        
        # Test default prompt
        default_prompt = self.manager.build_complete_prompt(
            user_text, page_data, conversation_history
        )
        
        self.assertIn("网页自动化助手", default_prompt)
        self.assertIn("在百度搜索人工智能", default_prompt)
        self.assertIn("对话历史", default_prompt)
        self.assertIn("baidu.com", default_prompt)
        
        # Test enhanced prompt
        context_analysis = {
            "search_intent": True,
            "search_keywords": ["人工智能"],
            "interaction_type": "search"
        }
        
        enhanced_prompt = self.manager.build_enhanced_prompt(
            user_text, page_data, conversation_history, context_analysis
        )
        
        self.assertIn("高级的网页自动化助手", enhanced_prompt)
        self.assertIn("搜索意图识别", enhanced_prompt)
        self.assertIn("人工智能", enhanced_prompt)
    
    def test_prompt_consistency(self):
        """Test that prompts are generated consistently"""
        user_text = "测试一致性"
        page_data = {"url": "test.com", "title": "Test", "elements": []}
        
        # Generate same prompt multiple times
        prompt1 = self.manager.build_complete_prompt(user_text, page_data)
        prompt2 = self.manager.build_complete_prompt(user_text, page_data)
        
        self.assertEqual(prompt1, prompt2)
    
    def test_different_prompt_types(self):
        """Test that different prompt types produce different results"""
        user_text = "测试不同类型"
        page_data = {"url": "test.com", "title": "Test", "elements": []}
        
        default_prompt = self.manager.build_system_prompt("default")
        enhanced_prompt = self.manager.build_system_prompt("enhanced")
        
        self.assertNotEqual(default_prompt, enhanced_prompt)
        self.assertIn("专业的网页自动化助手", default_prompt)
        self.assertIn("高级的网页自动化助手", enhanced_prompt)


if __name__ == "__main__":
    unittest.main()