#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试运行器

提供统一的集成测试执行入口，支持不同的测试模式和配置选项。
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from tests.integration.test_framework import create_test_framework, run_standard_tests
from tests.integration.test_automation_pipeline import ContinuousIntegrationRunner
from tests.integration.test_data_management import TestDataManager


class IntegrationTestRunner:
    """集成测试运行器主类"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化测试运行器"""
        self.config = self._load_config(config_file)
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        self.ci_runner = ContinuousIntegrationRunner(config_file)

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """加载配置文件"""
        if config_file and Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认配置
        return {
            "test_modes": ["unit", "integration", "e2e"],
            "parallel_execution": True,
            "max_workers": 4,
            "timeout": 300,
            "retry_failed": True,
            "generate_reports": True,
            "cleanup_after_test": True,
            "verbose": True
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有类型的测试"""
        print("🚀 启动完整集成测试套件...")
        start_time = datetime.now()
        
        results = {
            "start_time": start_time.isoformat(),
            "test_results": {},
            "summary": {},
            "errors": []
        }
        
        try:
            # 1. 运行标准集成测试
            if "integration" in self.config["test_modes"]:
                print("\n📋 运行标准集成测试...")
                integration_results = self._run_standard_integration_tests()
                results["test_results"]["integration"] = integration_results
            
            # 2. 运行端到端测试
            if "e2e" in self.config["test_modes"]:
                print("\n🔄 运行端到端测试...")
                e2e_results = self._run_end_to_end_tests()
                results["test_results"]["e2e"] = e2e_results
            
            # 3. 运行CI管道测试
            print("\n⚙️ 运行CI管道测试...")
            ci_results = self._run_ci_pipeline_tests()
            results["test_results"]["ci_pipeline"] = ci_results
            
            # 4. 生成综合报告
            results["summary"] = self._generate_comprehensive_summary(results["test_results"])
            
        except Exception as e:
            results["errors"].append(str(e))
            print(f"❌ 测试执行过程中发生错误: {e}")
        
        finally:
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["total_execution_time"] = (end_time - start_time).total_seconds()
            
            # 保存结果
            self._save_test_results(results)
            
            # 清理测试数据
            if self.config.get("cleanup_after_test", True):
                self._cleanup_test_environment()
        
        return results

    def _run_standard_integration_tests(self) -> Dict[str, Any]:
        """运行标准集成测试"""
        try:
            results = run_standard_tests("integration_test_suite")
            return {
                "success": True,
                "results": results,
                "test_type": "standard_integration"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "test_type": "standard_integration"
            }

    def _run_end_to_end_tests(self) -> Dict[str, Any]:
        """运行端到端测试"""
        try:
            # 导入端到端测试模块
            from tests.integration.test_end_to_end_scenarios import TestEndToEndScenarios
            
            # 创建测试套件
            import unittest
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestEndToEndScenarios)
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            result = runner.run(suite)
            
            return {
                "success": result.wasSuccessful(),
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
                "test_type": "end_to_end"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "test_type": "end_to_end"
            }

    def _run_ci_pipeline_tests(self) -> Dict[str, Any]:
        """运行CI管道测试"""
        try:
            self.ci_runner.create_standard_pipelines()
            results = self.ci_runner.run_all_pipelines()
            
            return {
                "success": results["summary"]["failed_pipelines"] == 0,
                "results": results,
                "test_type": "ci_pipeline"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "test_type": "ci_pipeline"
            }

    def _generate_comprehensive_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合测试摘要"""
        summary = {
            "total_test_types": len(test_results),
            "successful_test_types": 0,
            "failed_test_types": 0,
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "overall_success_rate": 0.0
        }
        
        for test_type, result in test_results.items():
            if result.get("success", False):
                summary["successful_test_types"] += 1
            else:
                summary["failed_test_types"] += 1
            
            # 统计具体测试数量
            if test_type == "integration":
                if "results" in result and "summary" in result["results"]:
                    int_summary = result["results"]["summary"]
                    summary["total_tests"] += int_summary.get("total_scenarios", 0)
                    summary["successful_tests"] += int_summary.get("successful_scenarios", 0)
            
            elif test_type == "e2e":
                summary["total_tests"] += result.get("tests_run", 0)
                summary["successful_tests"] += (result.get("tests_run", 0) - 
                                              result.get("failures", 0) - 
                                              result.get("errors", 0))
            
            elif test_type == "ci_pipeline":
                if "results" in result and "summary" in result["results"]:
                    ci_summary = result["results"]["summary"]
                    summary["total_tests"] += ci_summary.get("total_scenarios", 0)
                    summary["successful_tests"] += ci_summary.get("successful_scenarios", 0)
        
        # 计算总体成功率
        if summary["total_tests"] > 0:
            summary["overall_success_rate"] = summary["successful_tests"] / summary["total_tests"]
        
        return summary

    def _save_test_results(self, results: Dict[str, Any]):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON结果
        json_file = self.results_dir / f"integration_test_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 生成HTML报告
        if self.config.get("generate_reports", True):
            html_file = self.results_dir / f"integration_test_report_{timestamp}.html"
            self._generate_html_report(results, html_file)
        
        print(f"\n📊 测试结果已保存:")
        print(f"   JSON: {json_file}")
        if self.config.get("generate_reports", True):
            print(f"   HTML: {html_file}")

    def _generate_html_report(self, results: Dict[str, Any], output_file: Path):
        """生成HTML测试报告"""
        summary = results.get("summary", {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI浏览器代理 - 集成测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }}
        .metric {{ background: white; padding: 25px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }}
        .metric-label {{ color: #6c757d; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
        .content {{ padding: 30px; }}
        .test-section {{ margin-bottom: 40px; }}
        .test-section h2 {{ color: #333; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }}
        .test-result {{ background: #f8f9fa; border-left: 4px solid #dee2e6; padding: 20px; margin: 15px 0; border-radius: 0 8px 8px 0; }}
        .test-result.success {{ border-left-color: #28a745; }}
        .test-result.failure {{ border-left-color: #dc3545; }}
        .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-failure {{ background: #f8d7da; color: #721c24; }}
        .progress-bar {{ width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s ease; }}
        .details {{ margin-top: 15px; font-size: 0.9em; color: #6c757d; }}
        .error-message {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px; margin-top: 10px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI浏览器代理集成测试报告</h1>
            <p>生成时间: {results.get('start_time', 'Unknown')}</p>
            <p>总执行时间: {results.get('total_execution_time', 0):.2f}秒</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value {'success' if summary.get('overall_success_rate', 0) >= 0.9 else 'failure' if summary.get('overall_success_rate', 0) < 0.7 else 'warning'}">{summary.get('overall_success_rate', 0):.1%}</div>
                <div class="metric-label">总体成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {summary.get('overall_success_rate', 0) * 100}%"></div>
                </div>
            </div>
            <div class="metric">
                <div class="metric-value info">{summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}</div>
                <div class="metric-label">测试通过数</div>
            </div>
            <div class="metric">
                <div class="metric-value {'success' if summary.get('successful_test_types', 0) == summary.get('total_test_types', 0) else 'failure'}">{summary.get('successful_test_types', 0)}/{summary.get('total_test_types', 0)}</div>
                <div class="metric-label">测试类型通过</div>
            </div>
            <div class="metric">
                <div class="metric-value {'failure' if summary.get('failed_tests', 0) > 0 else 'success'}">{summary.get('failed_tests', 0)}</div>
                <div class="metric-label">失败测试数</div>
            </div>
        </div>
        
        <div class="content">
            <h2>📋 测试详情</h2>
"""
        
        # 添加各个测试类型的详细结果
        test_results = results.get("test_results", {})
        
        for test_type, result in test_results.items():
            success = result.get("success", False)
            status_class = "success" if success else "failure"
            status_text = "通过" if success else "失败"
            
            html_content += f"""
            <div class="test-section">
                <div class="test-result {status_class}">
                    <h3>
                        {'✅' if success else '❌'} {test_type.upper()} 测试
                        <span class="status-badge status-{status_class}">{status_text}</span>
                    </h3>
"""
            
            if success and "results" in result:
                # 显示成功结果的详细信息
                if test_type == "integration":
                    int_results = result["results"]
                    if "summary" in int_results:
                        int_summary = int_results["summary"]
                        html_content += f"""
                    <div class="details">
                        <p><strong>场景统计:</strong> {int_summary.get('successful_scenarios', 0)}/{int_summary.get('total_scenarios', 0)} 成功</p>
                        <p><strong>步骤统计:</strong> {int_summary.get('successful_steps', 0)}/{int_summary.get('total_steps', 0)} 成功</p>
                        <p><strong>执行时间:</strong> {int_summary.get('total_execution_time', 0):.2f}秒</p>
                    </div>
"""
                
                elif test_type == "e2e":
                    html_content += f"""
                    <div class="details">
                        <p><strong>测试运行:</strong> {result.get('tests_run', 0)} 个</p>
                        <p><strong>失败:</strong> {result.get('failures', 0)} 个</p>
                        <p><strong>错误:</strong> {result.get('errors', 0)} 个</p>
                        <p><strong>跳过:</strong> {result.get('skipped', 0)} 个</p>
                    </div>
"""
                
                elif test_type == "ci_pipeline":
                    ci_results = result["results"]
                    if "summary" in ci_results:
                        ci_summary = ci_results["summary"]
                        html_content += f"""
                    <div class="details">
                        <p><strong>管道:</strong> {ci_summary.get('successful_pipelines', 0)}/{ci_summary.get('total_pipelines', 0)} 成功</p>
                        <p><strong>套件:</strong> {ci_summary.get('successful_suites', 0)}/{ci_summary.get('total_suites', 0)} 成功</p>
                        <p><strong>场景:</strong> {ci_summary.get('successful_scenarios', 0)}/{ci_summary.get('total_scenarios', 0)} 成功</p>
                    </div>
"""
            
            elif not success and "error" in result:
                # 显示错误信息
                html_content += f"""
                    <div class="error-message">
                        <strong>错误信息:</strong><br>
                        {result['error']}
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        # 添加错误汇总
        if results.get("errors"):
            html_content += """
            <div class="test-section">
                <h2>⚠️ 错误汇总</h2>
"""
            for error in results["errors"]:
                html_content += f"""
                <div class="error-message">{error}</div>
"""
            html_content += "</div>"
        
        html_content += """
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _cleanup_test_environment(self):
        """清理测试环境"""
        print("\n🧹 清理测试环境...")
        
        try:
            # 清理临时测试数据
            test_data_dir = Path(__file__).parent / "test_data"
            if test_data_dir.exists():
                import shutil
                shutil.rmtree(test_data_dir)
            
            # 清理临时文件
            temp_files = list(Path.cwd().glob("*.tmp"))
            for temp_file in temp_files:
                temp_file.unlink()
            
            print("✅ 测试环境清理完成")
            
        except Exception as e:
            print(f"⚠️ 清理过程中发生错误: {e}")

    def run_specific_test_type(self, test_type: str) -> Dict[str, Any]:
        """运行特定类型的测试"""
        print(f"🎯 运行 {test_type} 测试...")
        
        if test_type == "integration":
            return self._run_standard_integration_tests()
        elif test_type == "e2e":
            return self._run_end_to_end_tests()
        elif test_type == "ci":
            return self._run_ci_pipeline_tests()
        else:
            return {
                "success": False,
                "error": f"未知的测试类型: {test_type}",
                "test_type": test_type
            }

    def get_test_status(self) -> Dict[str, Any]:
        """获取测试状态信息"""
        return {
            "config": self.config,
            "results_dir": str(self.results_dir),
            "available_test_types": ["integration", "e2e", "ci"],
            "last_run": self._get_last_test_run_info()
        }

    def _get_last_test_run_info(self) -> Optional[Dict[str, Any]]:
        """获取最后一次测试运行信息"""
        try:
            result_files = list(self.results_dir.glob("integration_test_results_*.json"))
            if not result_files:
                return None
            
            # 获取最新的结果文件
            latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "file": str(latest_file),
                "timestamp": data.get("start_time"),
                "success_rate": data.get("summary", {}).get("overall_success_rate", 0),
                "total_tests": data.get("summary", {}).get("total_tests", 0)
            }
        except Exception:
            return None


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description="AI浏览器代理集成测试运行器")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--type", choices=["all", "integration", "e2e", "ci"], 
                       default="all", help="要运行的测试类型")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--no-cleanup", action="store_true", help="测试后不清理环境")
    parser.add_argument("--status", action="store_true", help="显示测试状态信息")
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = IntegrationTestRunner(args.config)
    
    # 更新配置
    if args.verbose:
        runner.config["verbose"] = True
    if args.no_cleanup:
        runner.config["cleanup_after_test"] = False
    
    # 执行相应操作
    if args.status:
        status = runner.get_test_status()
        print("📊 测试状态信息:")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    
    # 运行测试
    if args.type == "all":
        results = runner.run_all_tests()
    else:
        results = runner.run_specific_test_type(args.type)
    
    # 输出结果摘要
    print("\n" + "=" * 80)
    print("🎉 集成测试完成")
    print("=" * 80)
    
    if args.type == "all" and "summary" in results:
        summary = results["summary"]
        print(f"📈 总体结果:")
        print(f"   成功率: {summary.get('overall_success_rate', 0):.2%}")
        print(f"   测试数: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}")
        print(f"   类型: {summary.get('successful_test_types', 0)}/{summary.get('total_test_types', 0)}")
        print(f"   执行时间: {results.get('total_execution_time', 0):.2f}秒")
        
        if summary.get('overall_success_rate', 0) >= 0.9:
            print("✅ 测试全部通过！")
        elif summary.get('overall_success_rate', 0) >= 0.7:
            print("⚠️ 部分测试失败，请检查详细报告")
        else:
            print("❌ 大量测试失败，需要立即修复")
    else:
        success = results.get("success", False)
        print(f"📋 {args.type.upper()} 测试结果: {'✅ 成功' if success else '❌ 失败'}")
        if not success and "error" in results:
            print(f"   错误: {results['error']}")


if __name__ == "__main__":
    main()