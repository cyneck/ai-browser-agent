#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
端到端集成测试场景

测试完整的用户工作流程，从自然语言输入到浏览器操作执行的全链路功能。
"""

import unittest
import asyncio
import json
import time
import tempfile
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.reasoning.agent import BrowserAgent
from src.api.cli import CLIInterface
from src.api.rest_api import RESTfulAPI
from src.api.web import WebInterface
from src.common.config import load_config


class TestEndToEndScenarios(unittest.TestCase):
    """端到端场景测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.config = load_config()
        cls.test_data_dir = Path(__file__).parent / "test_data"
        cls.test_data_dir.mkdir(exist_ok=True)

    def setUp(self):
        """测试前准备"""
        self.agent = None
        self.temp_files = []

    def tearDown(self):
        """测试后清理"""
        # 清理浏览器代理
        if self.agent:
            try:
                self.agent.cleanup()
            except:
                pass
        
        # 清理临时文件
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    def create_temp_file(self, content="", suffix=".txt"):
        """创建临时文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name

    @patch('src.reasoning.agent.BrowserAgent')
    def test_complete_navigation_workflow(self, mock_browser_agent_class):
        """测试完整的导航工作流程"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.execute = Mock()
        mock_agent.cleanup = Mock()
        
        # 模拟执行结果序列
        execution_results = [
            {
                "success": True,
                "message": "已成功导航到百度首页",
                "screenshot": "mock_screenshot_1",
                "session_state": {"current_url": "https://www.baidu.com", "step": 1}
            },
            {
                "success": True,
                "message": "已在搜索框中输入关键词",
                "screenshot": "mock_screenshot_2",
                "session_state": {"current_url": "https://www.baidu.com", "step": 2, "search_term": "Python"}
            },
            {
                "success": True,
                "message": "已点击搜索按钮，正在加载结果",
                "screenshot": "mock_screenshot_3",
                "session_state": {"current_url": "https://www.baidu.com/s?wd=Python", "step": 3}
            }
        ]
        
        mock_agent.execute.side_effect = execution_results
        mock_browser_agent_class.return_value = mock_agent

        # 创建CLI界面进行测试
        cli = CLIInterface()
        cli.agent = mock_agent

        # 执行完整的导航工作流程
        instructions = [
            "打开百度首页",
            "在搜索框中输入Python",
            "点击搜索按钮"
        ]

        session_state = {}
        for i, instruction in enumerate(instructions):
            result = cli._process_text_with_state(instruction, session_state)
            
            # 验证执行结果
            self.assertTrue(result["success"])
            self.assertEqual(result, execution_results[i])
            
            # 更新会话状态
            if "session_state" in result:
                session_state.update(result["session_state"])

        # 验证最终状态
        self.assertEqual(session_state["step"], 3)
        self.assertEqual(session_state["search_term"], "Python")
        self.assertIn("baidu.com/s?wd=Python", session_state["current_url"])

        # 验证代理方法调用
        mock_agent.initialize.assert_called_once()
        self.assertEqual(mock_agent.execute.call_count, 3)
        mock_agent.cleanup.assert_called_once()

    @patch('src.reasoning.agent.BrowserAgent')
    def test_form_filling_workflow(self, mock_browser_agent_class):
        """测试表单填写工作流程"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.execute = Mock()
        mock_agent.cleanup = Mock()

        # 模拟表单填写结果
        form_results = [
            {
                "success": True,
                "message": "已导航到登录页面",
                "session_state": {"current_url": "https://example.com/login", "form_step": 1}
            },
            {
                "success": True,
                "message": "已填写用户名",
                "session_state": {"form_step": 2, "username_filled": True}
            },
            {
                "success": True,
                "message": "已填写密码",
                "session_state": {"form_step": 3, "password_filled": True}
            },
            {
                "success": True,
                "message": "已提交登录表单",
                "session_state": {"form_step": 4, "login_submitted": True}
            }
        ]

        mock_agent.execute.side_effect = form_results
        mock_browser_agent_class.return_value = mock_agent

        # 创建REST API进行测试
        api = RESTfulAPI(enable_auth=False)
        api.agents["test_session"] = mock_agent
        api.session_states["test_session"] = {}

        # 执行表单填写工作流程
        form_instructions = [
            {"text": "打开登录页面", "session_id": "test_session"},
            {"text": "在用户名框输入testuser", "session_id": "test_session"},
            {"text": "在密码框输入password123", "session_id": "test_session"},
            {"text": "点击登录按钮", "session_id": "test_session"}
        ]

        for i, instruction in enumerate(form_instructions):
            result = api._execute_instruction(
                instruction["text"],
                instruction["session_id"],
                screenshot=False,
                timeout=30
            )
            
            # 验证执行结果
            self.assertTrue(result["success"])
            self.assertEqual(result["message"], form_results[i]["message"])

        # 验证最终状态
        final_state = api.session_states["test_session"]
        self.assertTrue(final_state.get("login_submitted", False))
        self.assertTrue(final_state.get("username_filled", False))
        self.assertTrue(final_state.get("password_filled", False))

    @patch('src.reasoning.agent.BrowserAgent')
    def test_error_recovery_workflow(self, mock_browser_agent_class):
        """测试错误恢复工作流程"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.cleanup = Mock()

        # 模拟执行结果：第一次失败，第二次成功
        def mock_execute(instruction, state):
            if "失败" in instruction:
                raise Exception("模拟执行失败")
            elif "重试" in instruction:
                return {
                    "success": True,
                    "message": "重试执行成功",
                    "session_state": {"retry_success": True}
                }
            else:
                return {
                    "success": True,
                    "message": "正常执行成功"
                }

        mock_agent.execute.side_effect = mock_execute
        mock_browser_agent_class.return_value = mock_agent

        # 创建CLI界面进行测试
        cli = CLIInterface()
        cli.agent = mock_agent

        # 测试错误恢复
        session_state = {}
        
        # 第一次执行失败
        result1 = cli._process_text_with_state("执行会失败的操作", session_state)
        self.assertFalse(result1["success"])
        self.assertIn("执行失败", result1["message"])

        # 重试执行成功
        result2 = cli._process_text_with_state("重试上一个操作", session_state)
        self.assertTrue(result2["success"])
        self.assertEqual(result2["message"], "重试执行成功")

        # 验证状态更新
        self.assertTrue(session_state.get("retry_success", False))

    @patch('src.reasoning.agent.BrowserAgent')
    def test_multi_session_isolation(self, mock_browser_agent_class):
        """测试多会话隔离"""
        # 创建多个模拟代理
        def create_mock_agent():
            mock_agent = Mock()
            mock_agent.initialize = Mock()
            mock_agent.execute = Mock(return_value={
                "success": True,
                "message": "执行成功",
                "session_state": {}
            })
            mock_agent.cleanup = Mock()
            return mock_agent

        mock_browser_agent_class.side_effect = create_mock_agent

        # 创建REST API
        api = RESTfulAPI(enable_auth=False)

        # 创建多个会话
        session_ids = []
        for i in range(3):
            session_id = f"session_{i}"
            api._create_session(session_id)
            session_ids.append(session_id)

        # 在不同会话中执行不同操作
        for i, session_id in enumerate(session_ids):
            instruction = f"执行会话{i}的特定操作"
            result = api._execute_instruction(instruction, session_id)
            
            self.assertTrue(result["success"])
            
            # 设置会话特定状态
            api.session_states[session_id][f"session_{i}_data"] = f"data_{i}"

        # 验证会话隔离
        for i, session_id in enumerate(session_ids):
            state = api.session_states[session_id]
            
            # 每个会话只应该有自己的数据
            self.assertIn(f"session_{i}_data", state)
            self.assertEqual(state[f"session_{i}_data"], f"data_{i}")
            
            # 不应该有其他会话的数据
            for j in range(3):
                if i != j:
                    self.assertNotIn(f"session_{j}_data", state)

        # 清理会话
        for session_id in session_ids:
            api._cleanup_session(session_id)

    def test_data_extraction_workflow(self):
        """测试数据提取工作流程"""
        # 模拟提取的数据
        mock_extracted_data = [
            {
                "title": "Python教程",
                "description": "学习Python编程的完整教程",
                "url": "https://example.com/python-tutorial",
                "price": "免费"
            },
            {
                "title": "JavaScript指南",
                "description": "现代JavaScript开发指南",
                "url": "https://example.com/js-guide",
                "price": "¥99"
            }
        ]

        with patch('src.reasoning.agent.BrowserAgent') as mock_browser_agent_class:
            mock_agent = Mock()
            mock_agent.initialize = Mock()
            mock_agent.execute = Mock(return_value={
                "success": True,
                "message": "数据提取完成",
                "content": mock_extracted_data,
                "content_type": "structured_data"
            })
            mock_agent.cleanup = Mock()
            mock_browser_agent_class.return_value = mock_agent

            # 创建CLI界面
            cli = CLIInterface(output_format="json")
            cli.agent = mock_agent

            # 执行数据提取
            result = cli._process_text("提取页面中的课程信息")

            # 验证提取结果
            self.assertTrue(result["success"])
            self.assertEqual(result["content_type"], "structured_data")
            self.assertEqual(len(result["content"]), 2)
            
            # 验证数据结构
            for item in result["content"]:
                self.assertIn("title", item)
                self.assertIn("description", item)
                self.assertIn("url", item)
                self.assertIn("price", item)

    @patch('src.reasoning.agent.BrowserAgent')
    def test_screenshot_and_debugging_workflow(self, mock_browser_agent_class):
        """测试截图和调试工作流程"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.cleanup = Mock()

        # 模拟截图数据
        mock_screenshot_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "截图已生成",
            "screenshot": mock_screenshot_data,
            "debug_info": {
                "page_title": "测试页面",
                "current_url": "https://example.com",
                "viewport_size": {"width": 1920, "height": 1080}
            }
        })
        mock_browser_agent_class.return_value = mock_agent

        # 创建REST API
        api = RESTfulAPI(enable_auth=False)
        session_id = "debug_session"
        api._create_session(session_id)

        # 执行截图操作
        result = api._execute_instruction(
            "对当前页面进行截图",
            session_id,
            screenshot=True
        )

        # 验证截图结果
        self.assertTrue(result["success"])
        self.assertIn("screenshot", result)
        self.assertEqual(result["screenshot"], mock_screenshot_data)
        self.assertIn("debug_info", result)
        
        # 验证调试信息
        debug_info = result["debug_info"]
        self.assertEqual(debug_info["page_title"], "测试页面")
        self.assertEqual(debug_info["current_url"], "https://example.com")

    def test_performance_monitoring_workflow(self):
        """测试性能监控工作流程"""
        with patch('src.reasoning.agent.BrowserAgent') as mock_browser_agent_class:
            mock_agent = Mock()
            mock_agent.initialize = Mock()
            mock_agent.cleanup = Mock()

            # 模拟性能数据
            performance_data = {
                "execution_time": 2.5,
                "memory_usage": 150.2,
                "cpu_usage": 25.8,
                "network_requests": 12,
                "page_load_time": 1.8
            }

            mock_agent.execute = Mock(return_value={
                "success": True,
                "message": "操作执行完成",
                "performance": performance_data
            })
            mock_browser_agent_class.return_value = mock_agent

            # 创建CLI界面
            cli = CLIInterface()
            cli.agent = mock_agent

            # 记录开始时间
            start_time = time.time()
            
            # 执行操作
            result = cli._process_text("执行性能测试操作")
            
            # 记录结束时间
            end_time = time.time()
            execution_time = end_time - start_time

            # 验证性能数据
            self.assertTrue(result["success"])
            self.assertIn("performance", result)
            
            perf = result["performance"]
            self.assertEqual(perf["execution_time"], 2.5)
            self.assertEqual(perf["memory_usage"], 150.2)
            self.assertEqual(perf["cpu_usage"], 25.8)
            
            # 验证实际执行时间合理
            self.assertLess(execution_time, 1.0)  # 模拟执行应该很快

    @patch('src.reasoning.agent.BrowserAgent')
    def test_batch_operations_workflow(self, mock_browser_agent_class):
        """测试批量操作工作流程"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.cleanup = Mock()

        # 模拟批量操作结果
        batch_results = [
            {"success": True, "message": "操作1完成"},
            {"success": True, "message": "操作2完成"},
            {"success": False, "message": "操作3失败", "error": "元素未找到"},
            {"success": True, "message": "操作4完成"}
        ]

        mock_agent.execute.side_effect = [
            batch_results[0],
            batch_results[1],
            Exception("元素未找到"),
            batch_results[3]
        ]
        mock_browser_agent_class.return_value = mock_agent

        # 创建REST API
        api = RESTfulAPI(enable_auth=False)
        session_id = "batch_session"
        api._create_session(session_id)

        # 批量指令
        batch_instructions = [
            {"text": "执行操作1", "session_id": session_id},
            {"text": "执行操作2", "session_id": session_id},
            {"text": "执行操作3", "session_id": session_id},
            {"text": "执行操作4", "session_id": session_id}
        ]

        # 执行批量操作
        results = []
        for instruction in batch_instructions:
            try:
                result = api._execute_instruction(
                    instruction["text"],
                    instruction["session_id"]
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "message": "执行失败",
                    "error": str(e)
                })

        # 验证批量结果
        self.assertEqual(len(results), 4)
        
        # 验证各个操作结果
        self.assertTrue(results[0]["success"])
        self.assertTrue(results[1]["success"])
        self.assertFalse(results[2]["success"])
        self.assertTrue(results[3]["success"])

        # 验证错误处理
        self.assertIn("error", results[2])
        self.assertIn("元素未找到", results[2]["error"])


class TestIntegrationTestFramework(unittest.TestCase):
    """集成测试框架本身的测试"""

    def setUp(self):
        """测试前准备"""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """测试后清理"""
        # 清理测试数据目录
        import shutil
        if self.test_data_dir.exists():
            try:
                shutil.rmtree(self.test_data_dir)
            except:
                pass

    def test_test_data_management(self):
        """测试测试数据管理"""
        # 创建测试数据文件
        test_file = self.test_data_dir / "test_config.json"
        test_data = {
            "test_urls": ["https://example.com", "https://test.com"],
            "test_credentials": {"username": "testuser", "password": "testpass"},
            "expected_results": {"login_success": True, "page_title": "Test Page"}
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        # 验证文件创建成功
        self.assertTrue(test_file.exists())

        # 读取并验证数据
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data["test_urls"], test_data["test_urls"])
        self.assertEqual(loaded_data["test_credentials"], test_data["test_credentials"])
        self.assertEqual(loaded_data["expected_results"], test_data["expected_results"])

    def test_test_environment_setup(self):
        """测试测试环境设置"""
        # 验证必要的环境变量和配置
        config = load_config()
        
        # 检查关键配置项
        self.assertIsNotNone(config)
        
        # 验证测试目录结构
        project_root = Path(__file__).resolve().parents[2]
        
        required_dirs = [
            project_root / "src",
            project_root / "tests",
            project_root / "tests" / "unit",
            project_root / "tests" / "integration"
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(dir_path.exists(), f"Required directory not found: {dir_path}")

    def test_mock_agent_creation(self):
        """测试模拟代理创建"""
        # 创建标准模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "测试执行成功"
        })
        mock_agent.cleanup = Mock()

        # 验证模拟代理功能
        mock_agent.initialize()
        result = mock_agent.execute("测试指令", {})
        mock_agent.cleanup()

        # 验证调用
        mock_agent.initialize.assert_called_once()
        mock_agent.execute.assert_called_once_with("测试指令", {})
        mock_agent.cleanup.assert_called_once()

        # 验证返回结果
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "测试执行成功")

    def test_test_isolation(self):
        """测试测试隔离性"""
        # 创建两个独立的测试环境
        env1_data = {"session_id": "env1", "data": "environment1"}
        env2_data = {"session_id": "env2", "data": "environment2"}

        # 模拟两个独立的测试执行
        def run_isolated_test(env_data):
            # 每个测试应该有独立的状态
            local_state = env_data.copy()
            local_state["test_executed"] = True
            return local_state

        result1 = run_isolated_test(env1_data)
        result2 = run_isolated_test(env2_data)

        # 验证测试隔离
        self.assertEqual(result1["session_id"], "env1")
        self.assertEqual(result2["session_id"], "env2")
        self.assertEqual(result1["data"], "environment1")
        self.assertEqual(result2["data"], "environment2")
        
        # 验证两个测试都执行了
        self.assertTrue(result1["test_executed"])
        self.assertTrue(result2["test_executed"])

        # 验证原始数据未被修改
        self.assertNotIn("test_executed", env1_data)
        self.assertNotIn("test_executed", env2_data)


if __name__ == "__main__":
    # 设置测试运行器
    unittest.main(verbosity=2, buffer=True)