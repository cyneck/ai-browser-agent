#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RESTful API 单元测试

测试RESTful API的各种功能，包括认证、会话管理、指令执行等。
"""

import unittest
import asyncio
import json
import time
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.api.rest_api import RESTfulAPI


class TestRESTfulAPI(unittest.TestCase):
    """RESTful API测试类"""

    def setUp(self):
        """测试前准备"""
        self.api = RESTfulAPI(enable_auth=False)
        self.client = TestClient(self.api.app)
        
        # 模拟BrowserAgent
        self.mock_agent = Mock()
        self.mock_agent.initialize = Mock()
        self.mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "执行成功",
            "screenshot": None
        })
        self.mock_agent.cleanup = Mock()

    def tearDown(self):
        """测试后清理"""
        # 清理会话
        for session_id in list(self.api.agents.keys()):
            if session_id in self.api.agents:
                del self.api.agents[session_id]
                del self.api.session_states[session_id]
                del self.api.session_info[session_id]

    def test_health_check(self):
        """测试健康检查端点"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

    def test_api_status(self):
        """测试API状态端点"""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("uptime", data)
        self.assertIn("active_sessions", data)
        self.assertIn("total_requests", data)

    @patch('src.api.rest_api.BrowserAgent')
    def test_create_session(self, mock_browser_agent):
        """测试创建会话"""
        mock_browser_agent.return_value = self.mock_agent
        
        response = self.client.post("/api/sessions")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("session_id", data)
        self.assertEqual(data["message"], "会话创建成功")
        
        session_id = data["session_id"]
        self.assertIn(session_id, self.api.agents)
        self.assertIn(session_id, self.api.session_states)
        self.assertIn(session_id, self.api.session_info)

    @patch('src.api.rest_api.BrowserAgent')
    def test_list_sessions(self, mock_browser_agent):
        """测试获取会话列表"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 创建几个会话
        session_ids = []
        for i in range(3):
            response = self.client.post("/api/sessions")
            session_id = response.json()["session_id"]
            session_ids.append(session_id)
        
        # 获取会话列表
        response = self.client.get("/api/sessions")
        self.assertEqual(response.status_code, 200)
        
        sessions = response.json()
        self.assertEqual(len(sessions), 3)
        
        for session in sessions:
            self.assertIn("session_id", session)
            self.assertIn("created_at", session)
            self.assertIn("last_activity", session)
            self.assertIn("message_count", session)
            self.assertIn("status", session)

    @patch('src.api.rest_api.BrowserAgent')
    def test_get_session(self, mock_browser_agent):
        """测试获取单个会话信息"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]
        
        # 获取会话信息
        response = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["session_id"], session_id)
        self.assertIn("created_at", data)
        self.assertIn("last_activity", data)
        self.assertEqual(data["message_count"], 0)
        self.assertEqual(data["status"], "active")

    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        response = self.client.get("/api/sessions/nonexistent")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "会话不存在")

    @patch('src.api.rest_api.BrowserAgent')
    def test_delete_session(self, mock_browser_agent):
        """测试删除会话"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]
        
        # 删除会话
        response = self.client.delete(f"/api/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("已删除", data["message"])
        
        # 验证会话已删除
        self.assertNotIn(session_id, self.api.agents)
        self.assertNotIn(session_id, self.api.session_states)
        self.assertNotIn(session_id, self.api.session_info)

    @patch('src.api.rest_api.BrowserAgent')
    def test_execute_instruction(self, mock_browser_agent):
        """测试执行指令"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 执行指令
        instruction_data = {
            "text": "打开百度",
            "screenshot": False,
            "timeout": 30
        }
        
        response = self.client.post("/api/execute", json=instruction_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "执行成功")
        self.assertIn("session_id", data)
        self.assertIn("execution_time", data)
        self.assertIn("timestamp", data)

    @patch('src.api.rest_api.BrowserAgent')
    def test_execute_instruction_with_session(self, mock_browser_agent):
        """测试在指定会话中执行指令"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]
        
        # 在指定会话中执行指令
        instruction_data = {
            "text": "搜索Python",
            "session_id": session_id,
            "screenshot": True
        }
        
        response = self.client.post("/api/execute", json=instruction_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["session_id"], session_id)
        
        # 验证会话信息已更新
        session_info = self.api.session_info[session_id]
        self.assertEqual(session_info["message_count"], 1)

    @patch('src.api.rest_api.BrowserAgent')
    def test_execute_batch_instructions(self, mock_browser_agent):
        """测试批量执行指令"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]
        
        # 批量指令
        instructions = [
            {"text": "打开百度", "session_id": session_id},
            {"text": "搜索Python", "session_id": session_id},
            {"text": "点击第一个结果", "session_id": session_id}
        ]
        
        response = self.client.post("/api/execute/batch", json=instructions)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["results"]), 3)
        
        for result in data["results"]:
            self.assertTrue(result["success"])
            self.assertEqual(result["session_id"], session_id)

    def test_batch_instructions_limit(self):
        """测试批量指令数量限制"""
        # 创建超过限制的指令列表
        instructions = [{"text": f"指令{i}"} for i in range(11)]
        
        response = self.client.post("/api/execute/batch", json=instructions)
        self.assertEqual(response.status_code, 400)
        self.assertIn("最多支持10条指令", response.json()["detail"])

    def test_invalid_instruction_data(self):
        """测试无效的指令数据"""
        # 空指令文本
        response = self.client.post("/api/execute", json={"text": ""})
        self.assertEqual(response.status_code, 422)
        
        # 超长指令文本
        long_text = "a" * 1001
        response = self.client.post("/api/execute", json={"text": long_text})
        self.assertEqual(response.status_code, 422)

    @patch('src.api.rest_api.BrowserAgent')
    def test_take_screenshot(self, mock_browser_agent):
        """测试截图功能"""
        mock_browser_agent.return_value = self.mock_agent
        self.mock_agent.execute.return_value = {
            "success": True,
            "screenshot": "base64_screenshot_data"
        }
        
        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]
        
        # 截图
        response = self.client.post(f"/api/sessions/{session_id}/screenshot")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["screenshot"], "base64_screenshot_data")

    @patch('src.api.rest_api.BrowserAgent')
    def test_session_state_management(self, mock_browser_agent):
        """测试会话状态管理"""
        mock_browser_agent.return_value = self.mock_agent
        
        # 创建会话
        response = self.client.post("/api/sessions")
        session_id = response.json()["session_id"]
        
        # 获取初始状态
        response = self.client.get(f"/api/sessions/{session_id}/state")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(data["state"], {})
        
        # 更新状态
        new_state = {"current_url": "https://example.com", "page_title": "Example"}
        response = self.client.put(f"/api/sessions/{session_id}/state", json=new_state)
        self.assertEqual(response.status_code, 200)
        
        # 验证状态已更新
        response = self.client.get(f"/api/sessions/{session_id}/state")
        data = response.json()
        self.assertEqual(data["state"]["current_url"], "https://example.com")
        self.assertEqual(data["state"]["page_title"], "Example")

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.Process')
    def test_get_metrics(self, mock_process, mock_disk, mock_memory, mock_cpu):
        """测试获取系统指标"""
        # 模拟系统指标
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(total=8000000000, available=4000000000, percent=50.0)
        mock_disk.return_value = Mock(total=1000000000000, free=500000000000, percent=50.0)
        
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=100000000, vms=200000000)
        mock_process_instance.cpu_percent.return_value = 15.0
        mock_process_instance.num_threads.return_value = 10
        mock_process_instance.create_time.return_value = time.time() - 3600
        mock_process.return_value = mock_process_instance
        
        response = self.client.get("/api/metrics")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("system", data)
        self.assertIn("process", data)
        self.assertIn("application", data)
        self.assertEqual(data["system"]["cpu_percent"], 25.5)
        self.assertEqual(data["system"]["memory_percent"], 50.0)

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_get_logs(self, mock_exists, mock_open):
        """测试获取日志"""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.readlines.return_value = [
            "2024-01-01 10:00:00 INFO Test log line 1\n",
            "2024-01-01 10:01:00 ERROR Test error line\n",
            "2024-01-01 10:02:00 INFO Test log line 2\n"
        ]
        
        response = self.client.get("/api/logs?lines=10&level=INFO")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("logs", data)
        self.assertEqual(data["log_level"], "INFO")
        self.assertGreater(len(data["logs"]), 0)


class TestRESTfulAPIWithAuth(unittest.TestCase):
    """带认证的RESTful API测试类"""

    def setUp(self):
        """测试前准备"""
        self.api = RESTfulAPI(enable_auth=True)
        self.client = TestClient(self.api.app)

    def test_login_success(self):
        """测试成功登录"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.client.post("/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["expires_in"], 1800)

    def test_login_failure(self):
        """测试登录失败"""
        login_data = {
            "username": "admin",
            "password": "wrong_password"
        }
        
        response = self.client.post("/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 401)
        self.assertIn("用户名或密码错误", response.json()["detail"])

    def test_protected_endpoint_without_token(self):
        """测试未提供令牌访问受保护端点"""
        response = self.client.get("/api/sessions")
        self.assertEqual(response.status_code, 403)

    def test_protected_endpoint_with_invalid_token(self):
        """测试使用无效令牌访问受保护端点"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/api/sessions", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_with_valid_token(self):
        """测试使用有效令牌访问受保护端点"""
        # 先登录获取令牌
        login_data = {"username": "admin", "password": "admin123"}
        login_response = self.client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # 使用令牌访问受保护端点
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/sessions", headers=headers)
        self.assertEqual(response.status_code, 200)


class TestRESTfulAPIRateLimit(unittest.TestCase):
    """速率限制测试类"""

    def setUp(self):
        """测试前准备"""
        self.api = RESTfulAPI(enable_auth=False, rate_limit=5)  # 设置较低的限制便于测试
        self.client = TestClient(self.api.app)

    def test_rate_limit_enforcement(self):
        """测试速率限制执行"""
        # 快速发送多个请求
        responses = []
        for i in range(7):  # 超过限制的请求数
            response = self.client.get("/api/status")
            responses.append(response)
        
        # 前5个请求应该成功
        for i in range(5):
            self.assertEqual(responses[i].status_code, 200)
        
        # 后续请求应该被限制
        for i in range(5, 7):
            self.assertEqual(responses[i].status_code, 429)
            self.assertIn("请求过于频繁", responses[i].json()["detail"])

    def test_rate_limit_reset(self):
        """测试速率限制重置"""
        # 发送达到限制的请求
        for i in range(5):
            response = self.client.get("/api/status")
            self.assertEqual(response.status_code, 200)
        
        # 下一个请求应该被限制
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 429)
        
        # 等待一段时间后，限制应该重置
        # 注意：在实际测试中，这里可能需要模拟时间流逝
        time.sleep(1)
        
        # 模拟时间流逝的方法：直接清理请求计数
        self.api.request_counts.clear()
        
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()