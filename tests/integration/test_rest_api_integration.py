#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RESTful API 集成测试

测试RESTful API与实际浏览器代理的集成功能。
"""

import unittest
import asyncio
import json
import time
import threading
import sys
import os
from unittest.mock import Mock, patch
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.api.rest_api import RESTfulAPI
from src.reasoning.agent import BrowserAgent


class TestRESTfulAPIIntegration(unittest.TestCase):
    """RESTful API集成测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.api = RESTfulAPI(enable_auth=False)
        cls.client = TestClient(cls.api.app)

    def setUp(self):
        """测试前准备"""
        # 清理之前的会话
        for session_id in list(self.api.agents.keys()):
            try:
                self.api.agents[session_id].cleanup()
            except:
                pass
            del self.api.agents[session_id]
            del self.api.session_states[session_id]
            del self.api.session_info[session_id]

    def tearDown(self):
        """测试后清理"""
        # 清理会话
        for session_id in list(self.api.agents.keys()):
            try:
                self.api.agents[session_id].cleanup()
            except:
                pass
            del self.api.agents[session_id]
            del self.api.session_states[session_id]
            del self.api.session_info[session_id]

    @patch('src.reasoning.agent.BrowserAgent')
    def test_full_workflow_with_mock_agent(self, mock_browser_agent_class):
        """测试完整工作流程（使用模拟代理）"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "页面已打开",
            "screenshot": "mock_screenshot_data",
            "session_state": {"current_url": "https://example.com"}
        })
        mock_agent.cleanup = Mock()
        mock_browser_agent_class.return_value = mock_agent

        # 1. 创建会话
        response = self.client.post("/api/sessions")
        self.assertEqual(response.status_code, 200)
        session_id = response.json()["session_id"]

        # 2. 执行指令
        instruction_data = {
            "text": "打开example.com",
            "session_id": session_id,
            "screenshot": True
        }
        response = self.client.post("/api/execute", json=instruction_data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "页面已打开")
        self.assertEqual(result["screenshot"], "mock_screenshot_data")

        # 3. 检查会话状态
        response = self.client.get(f"/api/sessions/{session_id}/state")
        self.assertEqual(response.status_code, 200)
        state = response.json()["state"]
        self.assertEqual(state["current_url"], "https://example.com")

        # 4. 获取会话信息
        response = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)
        session_info = response.json()
        self.assertEqual(session_info["message_count"], 1)

        # 5. 删除会话
        response = self.client.delete(f"/api/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)

        # 验证代理方法被正确调用
        mock_agent.initialize.assert_called_once()
        mock_agent.execute.assert_called_once()
        mock_agent.cleanup.assert_called_once()

    @patch('src.reasoning.agent.BrowserAgent')
    def test_multiple_sessions_isolation(self, mock_browser_agent_class):
        """测试多会话隔离"""
        # 设置模拟代理
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

        # 创建多个会话
        session_ids = []
        for i in range(3):
            response = self.client.post("/api/sessions")
            self.assertEqual(response.status_code, 200)
            session_ids.append(response.json()["session_id"])

        # 在不同会话中执行不同指令
        for i, session_id in enumerate(session_ids):
            instruction_data = {
                "text": f"执行任务{i+1}",
                "session_id": session_id
            }
            response = self.client.post("/api/execute", json=instruction_data)
            self.assertEqual(response.status_code, 200)

        # 验证会话状态独立
        response = self.client.get("/api/sessions")
        self.assertEqual(response.status_code, 200)
        sessions = response.json()
        self.assertEqual(len(sessions), 3)

        for session in sessions:
            self.assertEqual(session["message_count"], 1)
            self.assertEqual(session["status"], "active")

        # 清理会话
        for session_id in session_ids:
            response = self.client.delete(f"/api/sessions/{session_id}")
            self.assertEqual(response.status_code, 200)

    @patch('src.reasoning.agent.BrowserAgent')
    def test_error_handling_in_execution(self, mock_browser_agent_class):
        """测试执行过程中的错误处理"""
        # 设置模拟代理抛出异常
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.execute = Mock(side_effect=Exception("模拟执行错误"))
        mock_agent.cleanup = Mock()
        mock_browser_agent_class.return_value = mock_agent

        # 执行指令
        instruction_data = {
            "text": "执行会失败的指令"
        }
        response = self.client.post("/api/execute", json=instruction_data)
        self.assertEqual(response.status_code, 200)  # API应该返回200，但success为False

        result = response.json()
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "执行失败")
        self.assertIn("模拟执行错误", result["error"])

    @patch('src.reasoning.agent.BrowserAgent')
    def test_batch_execution_with_mixed_results(self, mock_browser_agent_class):
        """测试批量执行混合结果"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        
        # 模拟部分成功、部分失败的执行结果
        def mock_execute(instruction, state):
            if "成功" in instruction:
                return {"success": True, "message": "执行成功"}
            else:
                raise Exception("执行失败")
        
        mock_agent.execute = Mock(side_effect=mock_execute)
        mock_agent.cleanup = Mock()
        mock_browser_agent_class.return_value = mock_agent

        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]

        # 批量指令（混合成功和失败）
        instructions = [
            {"text": "成功指令1", "session_id": session_id},
            {"text": "失败指令", "session_id": session_id},
            {"text": "成功指令2", "session_id": session_id}
        ]

        response = self.client.post("/api/execute/batch", json=instructions)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total"], 3)
        results = data["results"]

        # 验证结果
        self.assertTrue(results[0]["success"])
        self.assertFalse(results[1]["success"])
        self.assertTrue(results[2]["success"])

    def test_api_documentation_endpoints(self):
        """测试API文档端点"""
        # 测试OpenAPI规范
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        
        openapi_spec = response.json()
        self.assertEqual(openapi_spec["info"]["title"], "AI浏览器代理 API")
        self.assertEqual(openapi_spec["info"]["version"], "1.0.0")

        # 验证主要端点存在
        paths = openapi_spec["paths"]
        self.assertIn("/api/status", paths)
        self.assertIn("/api/sessions", paths)
        self.assertIn("/api/execute", paths)
        self.assertIn("/api/execute/batch", paths)

    def test_cors_headers(self):
        """测试CORS头部"""
        response = self.client.options("/api/status")
        self.assertEqual(response.status_code, 200)
        
        # 检查CORS头部
        headers = response.headers
        self.assertIn("access-control-allow-origin", headers)
        self.assertIn("access-control-allow-methods", headers)
        self.assertIn("access-control-allow-headers", headers)

    @patch('src.reasoning.agent.BrowserAgent')
    def test_session_state_persistence(self, mock_browser_agent_class):
        """测试会话状态持久化"""
        # 设置模拟代理
        mock_agent = Mock()
        mock_agent.initialize = Mock()
        mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "执行成功",
            "session_state": {"step": 1, "data": "test"}
        })
        mock_agent.cleanup = Mock()
        mock_browser_agent_class.return_value = mock_agent

        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]

        # 执行指令更新状态
        instruction_data = {
            "text": "更新状态",
            "session_id": session_id
        }
        response = self.client.post("/api/execute", json=instruction_data)
        self.assertEqual(response.status_code, 200)

        # 验证状态已更新
        response = self.client.get(f"/api/sessions/{session_id}/state")
        state = response.json()["state"]
        self.assertEqual(state["step"], 1)
        self.assertEqual(state["data"], "test")

        # 手动更新状态
        new_state = {"step": 2, "additional": "info"}
        response = self.client.put(f"/api/sessions/{session_id}/state", json=new_state)
        self.assertEqual(response.status_code, 200)

        # 验证状态合并
        response = self.client.get(f"/api/sessions/{session_id}/state")
        state = response.json()["state"]
        self.assertEqual(state["step"], 2)  # 更新的值
        self.assertEqual(state["data"], "test")  # 保留的值
        self.assertEqual(state["additional"], "info")  # 新增的值

    def test_request_validation(self):
        """测试请求验证"""
        # 测试无效的指令请求
        invalid_requests = [
            {},  # 缺少text字段
            {"text": ""},  # 空text
            {"text": "a" * 1001},  # 超长text
            {"text": "valid", "timeout": -1},  # 无效timeout
            {"text": "valid", "timeout": 301},  # 超时timeout
        ]

        for invalid_request in invalid_requests:
            response = self.client.post("/api/execute", json=invalid_request)
            self.assertEqual(response.status_code, 422)

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.Process')
    def test_metrics_endpoint_integration(self, mock_process, mock_disk, mock_memory, mock_cpu):
        """测试指标端点集成"""
        # 模拟系统指标
        mock_cpu.return_value = 30.0
        mock_memory.return_value = Mock(total=16000000000, available=8000000000, percent=50.0)
        mock_disk.return_value = Mock(total=2000000000000, free=1000000000000, percent=50.0)
        
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=200000000, vms=400000000)
        mock_process_instance.cpu_percent.return_value = 20.0
        mock_process_instance.num_threads.return_value = 15
        mock_process_instance.create_time.return_value = time.time() - 7200
        mock_process.return_value = mock_process_instance

        response = self.client.get("/api/metrics")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        
        # 验证系统指标
        self.assertEqual(data["system"]["cpu_percent"], 30.0)
        self.assertEqual(data["system"]["memory_percent"], 50.0)
        
        # 验证进程指标
        self.assertEqual(data["process"]["cpu_percent"], 20.0)
        self.assertEqual(data["process"]["num_threads"], 15)
        
        # 验证应用指标
        self.assertIn("active_sessions", data["application"])
        self.assertIn("total_requests", data["application"])
        self.assertIn("uptime", data["application"])

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_logs_endpoint_integration(self, mock_exists, mock_open):
        """测试日志端点集成"""
        # 模拟日志文件
        mock_exists.return_value = True
        sample_logs = [
            "2024-01-01 10:00:00 INFO 应用启动\n",
            "2024-01-01 10:01:00 DEBUG 调试信息\n",
            "2024-01-01 10:02:00 ERROR 错误信息\n",
            "2024-01-01 10:03:00 INFO 正常操作\n",
            "2024-01-01 10:04:00 WARNING 警告信息\n"
        ]
        mock_open.return_value.__enter__.return_value.readlines.return_value = sample_logs

        # 测试获取所有日志
        response = self.client.get("/api/logs?level=ALL&lines=10")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["logs"]), 5)
        self.assertEqual(data["log_level"], "ALL")

        # 测试过滤INFO级别日志
        response = self.client.get("/api/logs?level=INFO&lines=10")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["logs"]), 2)  # 只有2条INFO日志
        self.assertEqual(data["log_level"], "INFO")

    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import concurrent.futures
        
        def make_request():
            response = self.client.get("/api/status")
            return response.status_code

        # 并发发送多个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 所有请求都应该成功
        for status_code in results:
            self.assertEqual(status_code, 200)


class TestRESTfulAPILiveServer(unittest.TestCase):
    """使用实际服务器的API测试"""

    @classmethod
    def setUpClass(cls):
        """启动测试服务器"""
        cls.api = RESTfulAPI(enable_auth=False)
        cls.server_thread = None
        cls.base_url = "http://127.0.0.1:8001"  # 使用不同端口避免冲突

    def setUp(self):
        """测试前准备"""
        # 注意：这里不启动实际服务器，因为在单元测试环境中可能有问题
        # 如果需要测试实际服务器，可以在集成测试环境中单独运行
        pass

    def test_server_startup_and_shutdown(self):
        """测试服务器启动和关闭"""
        # 这个测试在实际环境中运行
        # 这里只是验证API对象可以正确创建
        api = RESTfulAPI(enable_auth=False)
        self.assertIsNotNone(api.app)
        self.assertEqual(api.enable_auth, False)
        self.assertEqual(api.rate_limit, 60)  # 默认值


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)