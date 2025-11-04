#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试框架核心模块

提供集成测试的基础设施，包括测试环境管理、数据管理、自动化测试流程等。
"""

import unittest
import asyncio
import json
import time
import tempfile
import shutil
import sys
import os
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.reasoning.agent import BrowserAgent
from src.api.cli import CLIInterface
from src.api.rest_api import RESTfulAPI
from src.api.web import WebInterface
from src.common.config import load_config


@dataclass
class TestScenario:
    """测试场景定义"""
    name: str
    description: str
    instructions: List[str]
    expected_results: List[Dict[str, Any]]
    setup_data: Optional[Dict[str, Any]] = None
    cleanup_data: Optional[Dict[str, Any]] = None
    timeout: int = 60
    retry_count: int = 1


@dataclass
class TestEnvironment:
    """测试环境配置"""
    name: str
    config: Dict[str, Any]
    mock_data: Dict[str, Any]
    temp_files: List[str]
    temp_dirs: List[str]


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
        self.mock_agents.append(mock_agent)
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
        
        # 清理模拟代理
        for mock_agent in self.mock_agents:
            try:
                mock_agent.cleanup()
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
        self.mock_agents.clear()


class TestEnvironmentManager:
    """测试环境管理器"""

    def __init__(self):
        """初始化测试环境管理器"""
        self.environments: Dict[str, TestEnvironment] = {}
        self.current_environment: Optional[str] = None

    def create_environment(self, name: str, config: Dict[str, Any]) -> TestEnvironment:
        """创建测试环境"""
        env = TestEnvironment(
            name=name,
            config=config,
            mock_data={},
            temp_files=[],
            temp_dirs=[]
        )
        self.environments[name] = env
        return env

    def get_environment(self, name: str) -> Optional[TestEnvironment]:
        """获取测试环境"""
        return self.environments.get(name)

    def set_current_environment(self, name: str):
        """设置当前测试环境"""
        if name in self.environments:
            self.current_environment = name
        else:
            raise ValueError(f"环境 {name} 不存在")

    def cleanup_environment(self, name: str):
        """清理测试环境"""
        if name in self.environments:
            env = self.environments[name]
            
            # 清理临时文件
            for temp_file in env.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
            
            # 清理临时目录
            for temp_dir in env.temp_dirs:
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                except Exception:
                    pass
            
            del self.environments[name]

    def cleanup_all(self):
        """清理所有测试环境"""
        for name in list(self.environments.keys()):
            self.cleanup_environment(name)


class AutomatedTestRunner:
    """自动化测试运行器"""

    def __init__(self, data_manager: TestDataManager):
        """初始化测试运行器"""
        self.data_manager = data_manager
        self.test_results: List[Dict[str, Any]] = []
        self.current_scenario: Optional[TestScenario] = None

    def run_scenario(self, scenario: TestScenario) -> Dict[str, Any]:
        """运行测试场景"""
        self.current_scenario = scenario
        start_time = datetime.now()
        
        scenario_result = {
            "scenario_name": scenario.name,
            "description": scenario.description,
            "start_time": start_time.isoformat(),
            "success": False,
            "steps": [],
            "error": None,
            "execution_time": 0
        }
        
        try:
            # 执行设置步骤
            if scenario.setup_data:
                self._execute_setup(scenario.setup_data)
            
            # 执行测试步骤
            for i, instruction in enumerate(scenario.instructions):
                step_result = self._execute_step(instruction, scenario.expected_results[i] if i < len(scenario.expected_results) else {})
                scenario_result["steps"].append(step_result)
                
                # 如果步骤失败且不允许继续，则停止
                if not step_result["success"] and not step_result.get("continue_on_failure", False):
                    break
            
            # 检查整体成功状态
            scenario_result["success"] = all(step["success"] for step in scenario_result["steps"])
            
        except Exception as e:
            scenario_result["error"] = str(e)
            scenario_result["success"] = False
        
        finally:
            # 执行清理步骤
            if scenario.cleanup_data:
                self._execute_cleanup(scenario.cleanup_data)
            
            end_time = datetime.now()
            scenario_result["end_time"] = end_time.isoformat()
            scenario_result["execution_time"] = (end_time - start_time).total_seconds()
        
        self.test_results.append(scenario_result)
        return scenario_result

    def _execute_setup(self, setup_data: Dict[str, Any]):
        """执行设置步骤"""
        # 创建必要的测试数据文件
        if "test_files" in setup_data:
            for file_config in setup_data["test_files"]:
                content = file_config.get("content", "")
                suffix = file_config.get("suffix", ".txt")
                self.data_manager.create_temp_file(content, suffix)
        
        # 设置环境变量
        if "env_vars" in setup_data:
            for key, value in setup_data["env_vars"].items():
                os.environ[key] = str(value)

    def _execute_step(self, instruction: str, expected_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试步骤"""
        step_start = datetime.now()
        
        step_result = {
            "instruction": instruction,
            "expected": expected_result,
            "actual": {},
            "success": False,
            "error": None,
            "execution_time": 0
        }
        
        try:
            # 创建模拟代理并执行指令
            mock_agent = self.data_manager.create_mock_agent()
            result = mock_agent.execute(instruction, {})
            
            step_result["actual"] = result
            
            # 验证结果
            step_result["success"] = self._validate_result(result, expected_result)
            
        except Exception as e:
            step_result["error"] = str(e)
            step_result["success"] = False
        
        finally:
            step_end = datetime.now()
            step_result["execution_time"] = (step_end - step_start).total_seconds()
        
        return step_result

    def _validate_result(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """验证执行结果"""
        if not expected:
            return True  # 如果没有期望结果，则认为成功
        
        # 检查成功状态
        if "success" in expected:
            if actual.get("success") != expected["success"]:
                return False
        
        # 检查消息内容
        if "message_contains" in expected:
            message = actual.get("message", "")
            if expected["message_contains"] not in message:
                return False
        
        # 检查内容类型
        if "content_type" in expected:
            if not actual.get("content"):
                return False
            
            content = actual["content"]
            expected_type = expected["content_type"]
            
            if expected_type == "list" and not isinstance(content, list):
                return False
            elif expected_type == "dict" and not isinstance(content, dict):
                return False
            elif expected_type == "string" and not isinstance(content, str):
                return False
        
        return True

    def _execute_cleanup(self, cleanup_data: Dict[str, Any]):
        """执行清理步骤"""
        # 清理环境变量
        if "env_vars" in cleanup_data:
            for key in cleanup_data["env_vars"]:
                if key in os.environ:
                    del os.environ[key]

    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        total_scenarios = len(self.test_results)
        successful_scenarios = sum(1 for result in self.test_results if result["success"])
        
        total_steps = sum(len(result["steps"]) for result in self.test_results)
        successful_steps = sum(
            sum(1 for step in result["steps"] if step["success"])
            for result in self.test_results
        )
        
        total_time = sum(result["execution_time"] for result in self.test_results)
        
        return {
            "total_scenarios": total_scenarios,
            "successful_scenarios": successful_scenarios,
            "failed_scenarios": total_scenarios - successful_scenarios,
            "scenario_success_rate": successful_scenarios / total_scenarios if total_scenarios > 0 else 0,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": total_steps - successful_steps,
            "step_success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "total_execution_time": total_time,
            "average_scenario_time": total_time / total_scenarios if total_scenarios > 0 else 0
        }


class IntegrationTestFramework:
    """集成测试框架主类"""

    def __init__(self):
        """初始化集成测试框架"""
        self.data_manager: Optional[TestDataManager] = None
        self.env_manager = TestEnvironmentManager()
        self.test_runner: Optional[AutomatedTestRunner] = None
        self.scenarios: List[TestScenario] = []

    @contextmanager
    def test_context(self, test_name: str):
        """测试上下文管理器"""
        self.data_manager = TestDataManager(test_name)
        self.test_runner = AutomatedTestRunner(self.data_manager)
        
        try:
            yield self
        finally:
            if self.data_manager:
                self.data_manager.cleanup()
            self.env_manager.cleanup_all()

    def add_scenario(self, scenario: TestScenario):
        """添加测试场景"""
        self.scenarios.append(scenario)

    def run_all_scenarios(self) -> Dict[str, Any]:
        """运行所有测试场景"""
        if not self.test_runner:
            raise RuntimeError("测试运行器未初始化，请使用test_context")
        
        results = []
        for scenario in self.scenarios:
            result = self.test_runner.run_scenario(scenario)
            results.append(result)
        
        summary = self.test_runner.get_test_summary()
        
        return {
            "summary": summary,
            "scenarios": results,
            "timestamp": datetime.now().isoformat()
        }

    def create_standard_scenarios(self) -> List[TestScenario]:
        """创建标准测试场景"""
        scenarios = [
            TestScenario(
                name="basic_navigation",
                description="基本导航测试",
                instructions=[
                    "打开 https://example.com",
                    "等待页面加载完成",
                    "截图"
                ],
                expected_results=[
                    {"success": True, "message_contains": "导航"},
                    {"success": True},
                    {"success": True, "message_contains": "截图"}
                ]
            ),
            TestScenario(
                name="form_interaction",
                description="表单交互测试",
                instructions=[
                    "打开 https://form.example.com",
                    "在姓名框输入 测试用户",
                    "在邮箱框输入 test@example.com",
                    "点击提交按钮"
                ],
                expected_results=[
                    {"success": True},
                    {"success": True, "message_contains": "输入"},
                    {"success": True, "message_contains": "输入"},
                    {"success": True, "message_contains": "点击"}
                ]
            ),
            TestScenario(
                name="search_workflow",
                description="搜索工作流测试",
                instructions=[
                    "打开 https://search.example.com",
                    "在搜索框输入 Python教程",
                    "点击搜索按钮",
                    "提取搜索结果"
                ],
                expected_results=[
                    {"success": True},
                    {"success": True},
                    {"success": True},
                    {"success": True, "content_type": "list"}
                ]
            ),
            TestScenario(
                name="error_handling",
                description="错误处理测试",
                instructions=[
                    "点击不存在的元素",
                    "导航到无效URL",
                    "在不存在的输入框输入文本"
                ],
                expected_results=[
                    {"success": False},
                    {"success": False},
                    {"success": False}
                ]
            ),
            TestScenario(
                name="multi_step_workflow",
                description="多步骤工作流测试",
                instructions=[
                    "打开 https://example.com",
                    "点击登录链接",
                    "输入用户名 testuser",
                    "输入密码 password123",
                    "点击登录按钮",
                    "验证登录成功",
                    "截图保存状态"
                ],
                expected_results=[
                    {"success": True},
                    {"success": True},
                    {"success": True},
                    {"success": True},
                    {"success": True},
                    {"success": True},
                    {"success": True}
                ]
            )
        ]
        
        for scenario in scenarios:
            self.add_scenario(scenario)
        
        return scenarios


# 便利函数
def create_test_framework() -> IntegrationTestFramework:
    """创建集成测试框架实例"""
    return IntegrationTestFramework()


def run_standard_tests(test_name: str = "standard_integration_tests") -> Dict[str, Any]:
    """运行标准集成测试"""
    framework = create_test_framework()
    
    with framework.test_context(test_name) as ctx:
        # 创建标准测试场景
        ctx.create_standard_scenarios()
        
        # 运行所有测试
        results = ctx.run_all_scenarios()
        
        return results


if __name__ == "__main__":
    # 运行标准测试
    results = run_standard_tests()
    
    print("=" * 60)
    print("集成测试框架 - 标准测试结果")
    print("=" * 60)
    
    summary = results["summary"]
    print(f"总场景数: {summary['total_scenarios']}")
    print(f"成功场景: {summary['successful_scenarios']}")
    print(f"失败场景: {summary['failed_scenarios']}")
    print(f"场景成功率: {summary['scenario_success_rate']:.2%}")
    print(f"总步骤数: {summary['total_steps']}")
    print(f"成功步骤: {summary['successful_steps']}")
    print(f"步骤成功率: {summary['step_success_rate']:.2%}")
    print(f"总执行时间: {summary['total_execution_time']:.2f}秒")
    
    print("\n" + "=" * 60)
    print("详细结果:")
    for scenario in results["scenarios"]:
        status = "✅" if scenario["success"] else "❌"
        print(f"{status} {scenario['scenario_name']}: {scenario['description']}")
        if not scenario["success"] and scenario.get("error"):
            print(f"   错误: {scenario['error']}")