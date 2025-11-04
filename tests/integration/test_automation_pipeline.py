#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动化测试流程

实现完整的自动化测试管道，包括测试计划执行、结果收集、报告生成等。
"""

import unittest
import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from tests.integration.test_framework import (
    IntegrationTestFramework, TestScenario, TestDataManager, 
    AutomatedTestRunner, create_test_framework
)
from src.reasoning.agent import BrowserAgent
from src.api.cli import CLIInterface
from src.api.rest_api import RESTfulAPI
from src.common.config import load_config


class TestPipeline:
    """测试管道类"""

    def __init__(self, name: str, parallel_workers: int = 3):
        """初始化测试管道
        
        Args:
            name: 管道名称
            parallel_workers: 并行工作线程数
        """
        self.name = name
        self.parallel_workers = parallel_workers
        self.test_suites: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def add_test_suite(self, suite_name: str, scenarios: List[TestScenario], 
                      config: Optional[Dict[str, Any]] = None):
        """添加测试套件"""
        self.test_suites.append({
            "name": suite_name,
            "scenarios": scenarios,
            "config": config or {},
            "status": "pending"
        })

    def run_pipeline(self) -> Dict[str, Any]:
        """运行测试管道"""
        self.start_time = datetime.now()
        
        try:
            if self.parallel_workers > 1:
                return self._run_parallel()
            else:
                return self._run_sequential()
        finally:
            self.end_time = datetime.now()

    def _run_sequential(self) -> Dict[str, Any]:
        """顺序执行测试套件"""
        for suite in self.test_suites:
            suite_result = self._run_test_suite(suite)
            self.results.append(suite_result)
            suite["status"] = "completed" if suite_result["success"] else "failed"
        
        return self._generate_pipeline_report()

    def _run_parallel(self) -> Dict[str, Any]:
        """并行执行测试套件"""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # 提交所有测试套件任务
            future_to_suite = {
                executor.submit(self._run_test_suite, suite): suite 
                for suite in self.test_suites
            }
            
            # 收集结果
            for future in as_completed(future_to_suite):
                suite = future_to_suite[future]
                try:
                    suite_result = future.result()
                    self.results.append(suite_result)
                    suite["status"] = "completed" if suite_result["success"] else "failed"
                except Exception as e:
                    suite["status"] = "error"
                    self.results.append({
                        "suite_name": suite["name"],
                        "success": False,
                        "error": str(e),
                        "scenarios": []
                    })
        
        return self._generate_pipeline_report()

    def _run_test_suite(self, suite: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试套件"""
        suite_name = suite["name"]
        scenarios = suite["scenarios"]
        
        framework = create_test_framework()
        
        with framework.test_context(f"pipeline_{self.name}_{suite_name}") as ctx:
            # 添加场景到框架
            for scenario in scenarios:
                ctx.add_scenario(scenario)
            
            # 运行测试
            results = ctx.run_all_scenarios()
            
            return {
                "suite_name": suite_name,
                "success": results["summary"]["failed_scenarios"] == 0,
                "summary": results["summary"],
                "scenarios": results["scenarios"],
                "timestamp": results["timestamp"]
            }

    def _generate_pipeline_report(self) -> Dict[str, Any]:
        """生成管道报告"""
        total_suites = len(self.test_suites)
        successful_suites = sum(1 for result in self.results if result.get("success", False))
        
        total_scenarios = sum(
            result["summary"]["total_scenarios"] 
            for result in self.results 
            if "summary" in result
        )
        successful_scenarios = sum(
            result["summary"]["successful_scenarios"] 
            for result in self.results 
            if "summary" in result
        )
        
        execution_time = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        return {
            "pipeline_name": self.name,
            "execution_time": execution_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "summary": {
                "total_suites": total_suites,
                "successful_suites": successful_suites,
                "failed_suites": total_suites - successful_suites,
                "suite_success_rate": successful_suites / total_suites if total_suites > 0 else 0,
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "failed_scenarios": total_scenarios - successful_scenarios,
                "scenario_success_rate": successful_scenarios / total_scenarios if total_scenarios > 0 else 0
            },
            "suites": self.results
        }


class ContinuousIntegrationRunner:
    """持续集成测试运行器"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化CI运行器"""
        self.config = self._load_config(config_file)
        self.pipelines: List[TestPipeline] = []
        self.reports_dir = Path("test_reports")
        self.reports_dir.mkdir(exist_ok=True)

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """加载配置文件"""
        if config_file and Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认配置
        return {
            "parallel_workers": 3,
            "timeout": 300,
            "retry_failed": True,
            "generate_html_report": True,
            "send_notifications": False
        }

    def create_standard_pipelines(self):
        """创建标准测试管道"""
        # 基础功能测试管道
        basic_pipeline = TestPipeline("basic_functionality", self.config["parallel_workers"])
        basic_scenarios = [
            TestScenario(
                name="browser_initialization",
                description="浏览器初始化测试",
                instructions=["初始化浏览器", "检查浏览器状态"],
                expected_results=[{"success": True}, {"success": True}]
            ),
            TestScenario(
                name="page_navigation",
                description="页面导航测试",
                instructions=["打开 https://httpbin.org/html", "等待页面加载"],
                expected_results=[{"success": True}, {"success": True}]
            ),
            TestScenario(
                name="element_interaction",
                description="元素交互测试",
                instructions=["点击页面中的链接", "返回上一页"],
                expected_results=[{"success": True}, {"success": True}]
            )
        ]
        basic_pipeline.add_test_suite("basic_operations", basic_scenarios)
        self.pipelines.append(basic_pipeline)

        # API接口测试管道
        api_pipeline = TestPipeline("api_interface", self.config["parallel_workers"])
        api_scenarios = [
            TestScenario(
                name="cli_interface",
                description="CLI接口测试",
                instructions=["测试CLI初始化", "执行简单指令"],
                expected_results=[{"success": True}, {"success": True}]
            ),
            TestScenario(
                name="rest_api",
                description="REST API测试",
                instructions=["创建API会话", "执行API请求"],
                expected_results=[{"success": True}, {"success": True}]
            )
        ]
        api_pipeline.add_test_suite("interface_tests", api_scenarios)
        self.pipelines.append(api_pipeline)

        # 错误处理测试管道
        error_pipeline = TestPipeline("error_handling", self.config["parallel_workers"])
        error_scenarios = [
            TestScenario(
                name="network_errors",
                description="网络错误处理测试",
                instructions=["访问不存在的网站", "处理超时错误"],
                expected_results=[{"success": False}, {"success": False}]
            ),
            TestScenario(
                name="element_errors",
                description="元素错误处理测试",
                instructions=["点击不存在的元素", "在不存在的输入框输入"],
                expected_results=[{"success": False}, {"success": False}]
            )
        ]
        error_pipeline.add_test_suite("error_scenarios", error_scenarios)
        self.pipelines.append(error_pipeline)

        # 性能测试管道
        performance_pipeline = TestPipeline("performance", 1)  # 性能测试使用单线程
        performance_scenarios = [
            TestScenario(
                name="load_time",
                description="页面加载时间测试",
                instructions=["测量页面加载时间", "验证性能指标"],
                expected_results=[{"success": True}, {"success": True}],
                timeout=30
            ),
            TestScenario(
                name="memory_usage",
                description="内存使用测试",
                instructions=["监控内存使用", "检查内存泄漏"],
                expected_results=[{"success": True}, {"success": True}],
                timeout=60
            )
        ]
        performance_pipeline.add_test_suite("performance_tests", performance_scenarios)
        self.pipelines.append(performance_pipeline)

    def run_all_pipelines(self) -> Dict[str, Any]:
        """运行所有测试管道"""
        start_time = datetime.now()
        pipeline_results = []
        
        for pipeline in self.pipelines:
            print(f"运行测试管道: {pipeline.name}")
            result = pipeline.run_pipeline()
            pipeline_results.append(result)
            
            # 打印管道结果摘要
            summary = result["summary"]
            print(f"  套件: {summary['successful_suites']}/{summary['total_suites']} 成功")
            print(f"  场景: {summary['successful_scenarios']}/{summary['total_scenarios']} 成功")
            print(f"  执行时间: {result['execution_time']:.2f}秒")
            print()
        
        end_time = datetime.now()
        
        # 生成总体报告
        overall_report = self._generate_overall_report(pipeline_results, start_time, end_time)
        
        # 保存报告
        self._save_reports(overall_report, pipeline_results)
        
        return overall_report

    def _generate_overall_report(self, pipeline_results: List[Dict[str, Any]], 
                               start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """生成总体报告"""
        total_pipelines = len(pipeline_results)
        successful_pipelines = sum(
            1 for result in pipeline_results 
            if result["summary"]["failed_suites"] == 0
        )
        
        total_suites = sum(result["summary"]["total_suites"] for result in pipeline_results)
        successful_suites = sum(result["summary"]["successful_suites"] for result in pipeline_results)
        
        total_scenarios = sum(result["summary"]["total_scenarios"] for result in pipeline_results)
        successful_scenarios = sum(result["summary"]["successful_scenarios"] for result in pipeline_results)
        
        return {
            "report_type": "ci_overall_report",
            "timestamp": datetime.now().isoformat(),
            "execution_time": (end_time - start_time).total_seconds(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "summary": {
                "total_pipelines": total_pipelines,
                "successful_pipelines": successful_pipelines,
                "failed_pipelines": total_pipelines - successful_pipelines,
                "pipeline_success_rate": successful_pipelines / total_pipelines if total_pipelines > 0 else 0,
                "total_suites": total_suites,
                "successful_suites": successful_suites,
                "failed_suites": total_suites - successful_suites,
                "suite_success_rate": successful_suites / total_suites if total_suites > 0 else 0,
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "failed_scenarios": total_scenarios - successful_scenarios,
                "scenario_success_rate": successful_scenarios / total_scenarios if total_scenarios > 0 else 0
            },
            "pipelines": pipeline_results
        }

    def _save_reports(self, overall_report: Dict[str, Any], pipeline_results: List[Dict[str, Any]]):
        """保存测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON报告
        json_report_file = self.reports_dir / f"ci_report_{timestamp}.json"
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(overall_report, f, ensure_ascii=False, indent=2)
        
        # 生成HTML报告
        if self.config.get("generate_html_report", True):
            html_report_file = self.reports_dir / f"ci_report_{timestamp}.html"
            self._generate_html_report(overall_report, html_report_file)
        
        print(f"测试报告已保存:")
        print(f"  JSON: {json_report_file}")
        if self.config.get("generate_html_report", True):
            print(f"  HTML: {html_report_file}")

    def _generate_html_report(self, report: Dict[str, Any], output_file: Path):
        """生成HTML测试报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI浏览器代理 - 集成测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #6c757d; margin-top: 5px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .pipeline {{ margin-bottom: 30px; border: 1px solid #dee2e6; border-radius: 6px; }}
        .pipeline-header {{ background: #e9ecef; padding: 15px; font-weight: bold; }}
        .pipeline-content {{ padding: 15px; }}
        .suite {{ margin-bottom: 20px; }}
        .suite-header {{ font-weight: bold; margin-bottom: 10px; }}
        .scenario {{ margin-left: 20px; margin-bottom: 10px; }}
        .status-success {{ color: #28a745; }}
        .status-failure {{ color: #dc3545; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: #28a745; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI浏览器代理 - 集成测试报告</h1>
            <p>生成时间: {report['timestamp']}</p>
            <p>执行时间: {report['execution_time']:.2f}秒</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value {'success' if report['summary']['pipeline_success_rate'] == 1.0 else 'failure'}">{report['summary']['successful_pipelines']}/{report['summary']['total_pipelines']}</div>
                <div class="metric-label">管道成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {report['summary']['pipeline_success_rate'] * 100}%"></div>
                </div>
            </div>
            <div class="metric">
                <div class="metric-value {'success' if report['summary']['suite_success_rate'] == 1.0 else 'failure'}">{report['summary']['successful_suites']}/{report['summary']['total_suites']}</div>
                <div class="metric-label">测试套件成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {report['summary']['suite_success_rate'] * 100}%"></div>
                </div>
            </div>
            <div class="metric">
                <div class="metric-value {'success' if report['summary']['scenario_success_rate'] == 1.0 else 'failure'}">{report['summary']['successful_scenarios']}/{report['summary']['total_scenarios']}</div>
                <div class="metric-label">测试场景成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {report['summary']['scenario_success_rate'] * 100}%"></div>
                </div>
            </div>
        </div>
        
        <h2>管道详情</h2>
"""
        
        # 添加每个管道的详细信息
        for pipeline in report['pipelines']:
            pipeline_status = "success" if pipeline['summary']['failed_suites'] == 0 else "failure"
            html_content += f"""
        <div class="pipeline">
            <div class="pipeline-header status-{pipeline_status}">
                📊 {pipeline['pipeline_name']} 
                ({pipeline['summary']['successful_suites']}/{pipeline['summary']['total_suites']} 套件成功, 
                 {pipeline['summary']['successful_scenarios']}/{pipeline['summary']['total_scenarios']} 场景成功)
            </div>
            <div class="pipeline-content">
"""
            
            # 添加套件信息
            for suite in pipeline['suites']:
                suite_status = "success" if suite.get('success', False) else "failure"
                html_content += f"""
                <div class="suite">
                    <div class="suite-header status-{suite_status}">
                        📁 {suite['suite_name']} 
                        ({suite.get('summary', {}).get('successful_scenarios', 0)}/{suite.get('summary', {}).get('total_scenarios', 0)} 场景成功)
                    </div>
"""
                
                # 添加场景信息
                if 'scenarios' in suite:
                    for scenario in suite['scenarios']:
                        scenario_status = "success" if scenario.get('success', False) else "failure"
                        html_content += f"""
                    <div class="scenario status-{scenario_status}">
                        {'✅' if scenario.get('success', False) else '❌'} {scenario.get('scenario_name', 'Unknown')}: {scenario.get('description', '')}
                    </div>
"""
                
                html_content += "</div>"
            
            html_content += """
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


class TestAutomationPipeline(unittest.TestCase):
    """测试自动化管道的单元测试"""

    def setUp(self):
        """测试前准备"""
        self.ci_runner = ContinuousIntegrationRunner()

    def test_pipeline_creation(self):
        """测试管道创建"""
        pipeline = TestPipeline("test_pipeline", 2)
        self.assertEqual(pipeline.name, "test_pipeline")
        self.assertEqual(pipeline.parallel_workers, 2)
        self.assertEqual(len(pipeline.test_suites), 0)

    def test_test_suite_addition(self):
        """测试添加测试套件"""
        pipeline = TestPipeline("test_pipeline")
        scenarios = [
            TestScenario(
                name="test_scenario",
                description="测试场景",
                instructions=["测试指令"],
                expected_results=[{"success": True}]
            )
        ]
        
        pipeline.add_test_suite("test_suite", scenarios)
        self.assertEqual(len(pipeline.test_suites), 1)
        self.assertEqual(pipeline.test_suites[0]["name"], "test_suite")

    def test_ci_runner_initialization(self):
        """测试CI运行器初始化"""
        self.assertIsNotNone(self.ci_runner.config)
        self.assertTrue(self.ci_runner.reports_dir.exists())

    def test_standard_pipelines_creation(self):
        """测试标准管道创建"""
        self.ci_runner.create_standard_pipelines()
        self.assertGreater(len(self.ci_runner.pipelines), 0)
        
        # 验证管道名称
        pipeline_names = [p.name for p in self.ci_runner.pipelines]
        expected_names = ["basic_functionality", "api_interface", "error_handling", "performance"]
        for name in expected_names:
            self.assertIn(name, pipeline_names)

    def test_report_generation(self):
        """测试报告生成"""
        # 创建模拟管道结果
        mock_results = [{
            "pipeline_name": "test_pipeline",
            "execution_time": 10.0,
            "summary": {
                "total_suites": 1,
                "successful_suites": 1,
                "failed_suites": 0,
                "total_scenarios": 2,
                "successful_scenarios": 2,
                "failed_scenarios": 0
            }
        }]
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        
        report = self.ci_runner._generate_overall_report(mock_results, start_time, end_time)
        
        self.assertEqual(report["summary"]["total_pipelines"], 1)
        self.assertEqual(report["summary"]["successful_pipelines"], 1)
        self.assertEqual(report["summary"]["pipeline_success_rate"], 1.0)


if __name__ == "__main__":
    # 运行CI测试
    print("启动持续集成测试...")
    
    ci_runner = ContinuousIntegrationRunner()
    ci_runner.create_standard_pipelines()
    
    overall_report = ci_runner.run_all_pipelines()
    
    print("\n" + "=" * 80)
    print("持续集成测试完成")
    print("=" * 80)
    
    summary = overall_report["summary"]
    print(f"总体结果:")
    print(f"  管道: {summary['successful_pipelines']}/{summary['total_pipelines']} 成功 ({summary['pipeline_success_rate']:.2%})")
    print(f"  套件: {summary['successful_suites']}/{summary['total_suites']} 成功 ({summary['suite_success_rate']:.2%})")
    print(f"  场景: {summary['successful_scenarios']}/{summary['total_scenarios']} 成功 ({summary['scenario_success_rate']:.2%})")
    print(f"  总执行时间: {overall_report['execution_time']:.2f}秒")
    
    if summary['failed_pipelines'] > 0:
        print(f"\n⚠️  有 {summary['failed_pipelines']} 个管道失败，请检查详细报告")
    else:
        print(f"\n✅ 所有测试管道都成功完成！")