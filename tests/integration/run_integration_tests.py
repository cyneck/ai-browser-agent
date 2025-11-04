#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试执行脚本

统一的集成测试执行入口，支持多种测试模式和配置选项。
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from tests.integration.test_runner import IntegrationTestRunner
from tests.integration.test_comprehensive_scenarios import run_comprehensive_tests
from tests.integration.test_automation_pipeline import ContinuousIntegrationRunner


def print_banner():
    """打印测试横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AI浏览器代理 - 集成测试框架                                ║
║                                                                              ║
║  🤖 自动化测试 | 📊 性能监控 | 🔍 错误检测 | 📈 质量保证                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_quick_test():
    """运行快速测试"""
    print("⚡ 运行快速集成测试...")
    
    from tests.integration.test_framework import run_standard_tests
    
    try:
        results = run_standard_tests("quick_test")
        
        summary = results["summary"]
        print(f"\n📋 快速测试结果:")
        print(f"   场景: {summary['successful_scenarios']}/{summary['total_scenarios']} 成功")
        print(f"   步骤: {summary['successful_steps']}/{summary['total_steps']} 成功")
        print(f"   成功率: {summary['scenario_success_rate']:.2%}")
        print(f"   执行时间: {summary['total_execution_time']:.2f}秒")
        
        return summary['scenario_success_rate'] >= 0.8
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False


def run_full_test_suite(config_file=None):
    """运行完整测试套件"""
    print("🔄 运行完整集成测试套件...")
    
    try:
        runner = IntegrationTestRunner(config_file)
        results = runner.run_all_tests()
        
        summary = results.get("summary", {})
        print(f"\n📊 完整测试结果:")
        print(f"   总体成功率: {summary.get('overall_success_rate', 0):.2%}")
        print(f"   测试类型: {summary.get('successful_test_types', 0)}/{summary.get('total_test_types', 0)} 成功")
        print(f"   测试总数: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)} 成功")
        print(f"   执行时间: {results.get('total_execution_time', 0):.2f}秒")
        
        return summary.get('overall_success_rate', 0) >= 0.8
        
    except Exception as e:
        print(f"❌ 完整测试失败: {e}")
        return False


def run_comprehensive_test_suite():
    """运行综合测试套件"""
    print("🎯 运行综合集成测试套件...")
    
    try:
        result = run_comprehensive_tests()
        
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
        
        print(f"\n🎉 综合测试结果:")
        print(f"   测试总数: {result.testsRun}")
        print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"   失败: {len(result.failures)}")
        print(f"   错误: {len(result.errors)}")
        print(f"   成功率: {success_rate:.2%}")
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"❌ 综合测试失败: {e}")
        return False


def run_ci_pipeline():
    """运行CI管道测试"""
    print("⚙️ 运行CI管道测试...")
    
    try:
        ci_runner = ContinuousIntegrationRunner()
        ci_runner.create_standard_pipelines()
        results = ci_runner.run_all_pipelines()
        
        summary = results["summary"]
        print(f"\n🔧 CI管道测试结果:")
        print(f"   管道: {summary['successful_pipelines']}/{summary['total_pipelines']} 成功")
        print(f"   套件: {summary['successful_suites']}/{summary['total_suites']} 成功")
        print(f"   场景: {summary['successful_scenarios']}/{summary['total_scenarios']} 成功")
        print(f"   执行时间: {results['execution_time']:.2f}秒")
        
        return summary['failed_pipelines'] == 0
        
    except Exception as e:
        print(f"❌ CI管道测试失败: {e}")
        return False


def generate_test_report(results):
    """生成测试报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)
    
    # 生成JSON报告
    json_report = report_dir / f"integration_test_summary_{timestamp}.json"
    with open(json_report, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成文本报告
    text_report = report_dir / f"integration_test_summary_{timestamp}.txt"
    with open(text_report, 'w', encoding='utf-8') as f:
        f.write("AI浏览器代理 - 集成测试报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"生成时间: {datetime.now().isoformat()}\n")
        f.write(f"测试模式: {results.get('test_mode', 'unknown')}\n")
        f.write(f"测试结果: {'✅ 通过' if results.get('overall_success', False) else '❌ 失败'}\n")
        f.write(f"执行时间: {results.get('execution_time', 0):.2f}秒\n\n")
        
        if 'details' in results:
            f.write("详细结果:\n")
            for detail in results['details']:
                f.write(f"  - {detail}\n")
    
    print(f"\n📄 测试报告已生成:")
    print(f"   JSON: {json_report}")
    print(f"   文本: {text_report}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI浏览器代理集成测试执行器")
    parser.add_argument("--mode", choices=["quick", "full", "comprehensive", "ci", "all"], 
                       default="quick", help="测试模式")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--no-banner", action="store_true", help="不显示横幅")
    
    args = parser.parse_args()
    
    # 显示横幅
    if not args.no_banner:
        print_banner()
    
    start_time = datetime.now()
    results = {
        "test_mode": args.mode,
        "start_time": start_time.isoformat(),
        "overall_success": False,
        "details": []
    }
    
    try:
        if args.mode == "quick":
            success = run_quick_test()
            results["overall_success"] = success
            results["details"].append(f"快速测试: {'通过' if success else '失败'}")
            
        elif args.mode == "full":
            success = run_full_test_suite(args.config)
            results["overall_success"] = success
            results["details"].append(f"完整测试: {'通过' if success else '失败'}")
            
        elif args.mode == "comprehensive":
            success = run_comprehensive_test_suite()
            results["overall_success"] = success
            results["details"].append(f"综合测试: {'通过' if success else '失败'}")
            
        elif args.mode == "ci":
            success = run_ci_pipeline()
            results["overall_success"] = success
            results["details"].append(f"CI管道测试: {'通过' if success else '失败'}")
            
        elif args.mode == "all":
            print("🚀 运行所有测试模式...")
            
            # 依次运行所有测试
            quick_success = run_quick_test()
            results["details"].append(f"快速测试: {'通过' if quick_success else '失败'}")
            
            full_success = run_full_test_suite(args.config)
            results["details"].append(f"完整测试: {'通过' if full_success else '失败'}")
            
            comprehensive_success = run_comprehensive_test_suite()
            results["details"].append(f"综合测试: {'通过' if comprehensive_success else '失败'}")
            
            ci_success = run_ci_pipeline()
            results["details"].append(f"CI管道测试: {'通过' if ci_success else '失败'}")
            
            # 所有测试都通过才算成功
            results["overall_success"] = all([quick_success, full_success, comprehensive_success, ci_success])
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        results["details"].append("测试被用户中断")
        
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生错误: {e}")
        results["details"].append(f"执行错误: {e}")
        
    finally:
        end_time = datetime.now()
        results["end_time"] = end_time.isoformat()
        results["execution_time"] = (end_time - start_time).total_seconds()
        
        # 输出最终结果
        print("\n" + "=" * 80)
        print("🏁 测试执行完成")
        print("=" * 80)
        
        print(f"测试模式: {args.mode}")
        print(f"执行时间: {results['execution_time']:.2f}秒")
        print(f"最终结果: {'✅ 全部通过' if results['overall_success'] else '❌ 存在失败'}")
        
        if results['details']:
            print("\n详细结果:")
            for detail in results['details']:
                print(f"  {detail}")
        
        # 生成报告
        if args.report:
            generate_test_report(results)
        
        # 设置退出码
        sys.exit(0 if results['overall_success'] else 1)


if __name__ == "__main__":
    main()