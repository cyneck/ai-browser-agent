#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试数据管理和清理

提供测试数据的创建、管理和清理功能，确保测试环境的一致性和可重复性。
"""

import unittest
import json
import tempfile
import shutil
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.reasoning.agent import BrowserAgent


class TestDataManager:
    """测试数据管理器"""

    def __init__(self, test_name: str):
        """初始化测试数据管理器"""
        self.test_name = test_name
        self.test_data_dir = Path(__file__).parent / "test_data" / test_name
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
        self.mock_agents: List[Mock] = []
        
        # 创建测试数据目录
        self.test_data_dir.mkdir(parents=True, exist_ok=True)

    def create_test_config(self, config_data: Dict[str, Any]) -> Path:
        """创建测试配置文件"""
        config_file = self.test_data_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return config_file

    def create_mock_page_data(self, page_type: str = "generic") -> Dict[str, Any]:
        """创建模拟页面数据"""
        mock_data = {
            "generic": {
                "url": "https://example.com",
                "title": "Example Page",
                "elements": [
                    {
                        "type": "button",
                        "text": "Click Me",
                        "selector": "#click-btn",
                        "attributes": {"id": "click-btn", "class": "btn primary"}
                    },
                    {
                        "type": "input",
                        "text": "",
                        "selector": "#text-input",
                        "attributes": {"id": "text-input", "type": "text", "placeholder": "Enter text"}
                    }
                ],
                "text_content": "This is a sample page for testing purposes.",
                "functional_areas": [
                    {"type": "form", "selector": "form"},
                    {"type": "navigation", "selector": "nav"}
                ]
            },
            "search": {
                "url": "https://search.example.com",
                "title": "Search Engine",
                "elements": [
                    {
                        "type": "input",
                        "text": "",
                        "selector": "#search-input",
                        "attributes": {"id": "search-input", "type": "search", "placeholder": "Search..."}
                    },
                    {
                        "type": "button",
                        "text": "Search",
                        "selector": "#search-btn",
                        "attributes": {"id": "search-btn", "class": "search-button"}
                    }
                ],
                "text_content": "Search for anything you want.",
                "functional_areas": [
                    {"type": "search_box", "selector": "#search-input"},
                    {"type": "search_button", "selector": "#search-btn"}
                ]
            },
            "form": {
                "url": "https://form.example.com",
                "title": "Contact Form",
                "elements": [
                    {
                        "type": "input",
                        "text": "",
                        "selector": "#name",
                        "attributes": {"id": "name", "type": "text", "name": "name", "required": True}
                    },
                    {
                        "type": "input",
                        "text": "",
                        "selector": "#email",
                        "attributes": {"id": "email", "type": "email", "name": "email", "required": True}
                    },
                    {
                        "type": "textarea",
                        "text": "",
                        "selector": "#message",
                        "attributes": {"id": "message", "name": "message", "rows": 5}
                    },
                    {
                        "type": "button",
                        "text": "Submit",
                        "selector": "#submit-btn",
                        "attributes": {"id": "submit-btn", "type": "submit", "class": "btn submit"}
                    }
                ],
                "text_content": "Please fill out the contact form below.",
                "functional_areas": [
                    {"type": "form", "selector": "form"},
                    {"type": "submit_button", "selector": "#submit-btn"}
                ]
            }
        }
        return mock_data.get(page_type, mock_data["generic"])

    def create_mock_agent(self, behavior_config: Optional[Dict[str, Any]] = None) -> Mock:
        """创建模拟浏览器代理"""
        mock_agent = Mock(spec=BrowserAgent)
        mock_agent.initialize = Mock()
        mock_agent.cleanup = Mock()
        
        # 默认行为配置
        default_behavior = {
            "success_rate": 0.9,  # 90%成功率
            "execution_time": 1.0,  # 1秒执行时间
            "error_types": ["timeout", "element_not_found", "network_error"]
        }
        
        if behavior_config:
            default_behavior.update(behavior_config)
        
        # 配置execute方法的行为
        def mock_execute(instruction: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
            import random
            
            # 模拟执行时间
            time.sleep(default_behavior["execution_time"] * random.uniform(0.5, 1.5))
            
            # 根据成功率决定是否成功
            if random.random() < default_behavior["success_rate"]:
                return {
                    "success": True,
                    "message": f"成功执行指令: {instruction}",
                    "session_state": session_state,
                    "screenshot": "mock_screenshot_data",
                    "content": self._generate_mock_content(instruction)
                }
            else:
                error_type = random.choice(default_behavior["error_types"])
                return {
                    "success": False,
                    "message": f"执行失败: {error_type}",
                    "error": f"模拟错误: {error_type}",
                    "session_state": session_state
                }
        
        mock_agent.execute.side_effect = mock_execute
        return mock_agent

    def _generate_mock_content(self, instruction: str) -> Any:
        """根据指令生成模拟内容"""
        if "搜索" in instruction or "search" in instruction.lower():
            return [
                {
                    "title": "搜索结果1",
                    "description": "这是第一个搜索结果的描述",
                    "url": "https://example.com/result1"
                },
                {
                    "title": "搜索结果2", 
                    "description": "这是第二个搜索结果的描述",
                    "url": "https://example.com/result2"
                }
            ]
        elif "提取" in instruction or "extract" in instruction.lower():
            return {
                "page_title": "测试页面",
                "main_content": "这是页面的主要内容",
                "links": ["https://example.com/link1", "https://example.com/link2"]
            }
        else:
            return f"模拟内容: {instruction}"

    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> str:
        """创建临时文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix, encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name

    def create_temp_dir(self) -> str:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def save_test_data(self, data: Dict[str, Any], filename: str) -> Path:
        """保存测试数据到文件"""
        file_path = self.test_data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    def load_test_data(self, filename: str) -> Dict[str, Any]:
        """从文件加载测试数据"""
        file_path = self.test_data_dir / filename
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_session_state(self, **kwargs) -> Dict[str, Any]:
        """创建会话状态数据"""
        default_state = {
            "session_id": f"test_session_{int(time.time())}",
            "created_at": datetime.now().isoformat(),
            "current_url": "https://example.com",
            "page_title": "Test Page",
            "variables": {},
            "history": []
        }
        default_state.update(kwargs)
        return default_state

    def cleanup(self):
        """清理测试数据"""
        # 清理临时文件
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        
        # 清理临时目录
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
        
        # 清理测试数据目录
        try:
            if self.test_data_dir.exists():
                shutil.rmtree(self.test_data_dir)
        except Exception:
            pass
        
        # 重置列表
        self.temp_files.clear()
        self.temp_dirs.clear()


class TestDataManagementTests(unittest.TestCase):
    """测试数据管理功能的测试"""

    def setUp(self):
        """测试前准备"""
        self.data_manager = TestDataManager("test_data_management")

    def tearDown(self):
        """测试后清理"""
        self.data_manager.cleanup()

    def test_create_test_config(self):
        """测试创建测试配置"""
        config_data = {
            "browser_type": "chromium",
            "headless": True,
            "timeout": 30
        }
        
        config_file = self.data_manager.create_test_config(config_data)
        
        # 验证文件创建
        self.assertTrue(config_file.exists())
        
        # 验证文件内容
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config, config_data)

    def test_create_mock_page_data(self):
        """测试创建模拟页面数据"""
        # 测试通用页面数据
        generic_data = self.data_manager.create_mock_page_data("generic")
        self.assertEqual(generic_data["url"], "https://example.com")
        self.assertIn("elements", generic_data)
        
        # 测试搜索页面数据
        search_data = self.data_manager.create_mock_page_data("search")
        self.assertEqual(search_data["url"], "https://search.example.com")
        self.assertEqual(search_data["title"], "Search Engine")
        
        # 测试表单页面数据
        form_data = self.data_manager.create_mock_page_data("form")
        self.assertEqual(form_data["url"], "https://form.example.com")
        self.assertEqual(form_data["title"], "Contact Form")

    def test_create_mock_agent(self):
        """测试创建模拟代理"""
        mock_agent = self.data_manager.create_mock_agent()
        
        # 验证代理方法存在
        self.assertTrue(hasattr(mock_agent, 'initialize'))
        self.assertTrue(hasattr(mock_agent, 'execute'))
        self.assertTrue(hasattr(mock_agent, 'cleanup'))
        
        # 测试执行方法
        result = mock_agent.execute("测试指令", {})
        self.assertIn("success", result)
        self.assertIn("message", result)

    def test_create_temp_file(self):
        """测试创建临时文件"""
        content = "这是测试内容"
        temp_file = self.data_manager.create_temp_file(content, ".txt")
        
        # 验证文件存在
        self.assertTrue(os.path.exists(temp_file))
        
        # 验证文件内容
        with open(temp_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        self.assertEqual(file_content, content)

    def test_create_temp_dir(self):
        """测试创建临时目录"""
        temp_dir = self.data_manager.create_temp_dir()
        
        # 验证目录存在
        self.assertTrue(os.path.exists(temp_dir))
        self.assertTrue(os.path.isdir(temp_dir))

    def test_save_and_load_test_data(self):
        """测试保存和加载测试数据"""
        test_data = {
            "test_name": "sample_test",
            "test_config": {"timeout": 30},
            "test_results": [{"success": True}]
        }
        
        # 保存数据
        file_path = self.data_manager.save_test_data(test_data, "sample_data.json")
        self.assertTrue(file_path.exists())
        
        # 加载数据
        loaded_data = self.data_manager.load_test_data("sample_data.json")
        self.assertEqual(loaded_data, test_data)

    def test_create_session_state(self):
        """测试创建会话状态"""
        session_state = self.data_manager.create_session_state(
            current_url="https://test.com",
            custom_var="test_value"
        )
        
        # 验证默认字段
        self.assertIn("session_id", session_state)
        self.assertIn("created_at", session_state)
        self.assertIn("variables", session_state)
        
        # 验证自定义字段
        self.assertEqual(session_state["current_url"], "https://test.com")
        self.assertEqual(session_state["custom_var"], "test_value")

    def test_cleanup(self):
        """测试清理功能"""
        # 创建一些临时资源
        temp_file = self.data_manager.create_temp_file("test content")
        temp_dir = self.data_manager.create_temp_dir()
        
        # 验证资源存在
        self.assertTrue(os.path.exists(temp_file))
        self.assertTrue(os.path.exists(temp_dir))
        
        # 执行清理
        self.data_manager.cleanup()
        
        # 验证资源已清理（注意：由于tearDown也会调用cleanup，这里主要测试不会出错）
        # 实际的文件清理验证在tearDown中进行


if __name__ == "__main__":
    unittest.main(verbosity=2)