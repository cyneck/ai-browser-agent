#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最终验收测试执行脚本

提供便捷的最终验收测试执行入口，支持不同的测试模式和报告生成。
"""

import sys
import os
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Import will be done dynamically to avoid circular import issues


def run_quick_acceptance_test() -> bool:
    """运行快速验收测试"""
    print("🚀 运行快速验收测试...")
    
    try:
        # 运行核心功能测试
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/test_final_acceptance.py::FinalAcceptanceTests::test_system_integrity_validation",
            "tests/integration/test_final_acceptance.py::FinalAcceptanceTests::test_requirements_implementation_validation",
            "-v", "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 快速验收测试执行失败: {e}")
        return False


def run_comprehensive_acceptance_test() -> bool:
    """运行全面验收测试"""
    print("🎯 运行全面验收测试...")
    
    try:
        # 直接运行测试文件
        result = subprocess.run([
            sys.executable, "tests/integration/test_final_acceptance.py"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 全面验收测试执行失败: {e}")
        return False


def run_custom_acceptance_test(test_categories: List[str]) -> bool:
    """运行自定义验收测试"""
    print(f"🔧 运行自定义验收测试: {', '.join(test_categories)}")
    
    try:
        # 运行指定的测试方法
        test_methods = []
        
        if "system" in test_categories:
            test_methods.append("test_system_requirements_validation")
        
        if "requirements" in test_categories:
            test_methods.append("test_system_requirements_validation")
        
        if "user" in test_categories:
            test_methods.append("test_user_acceptance_scenarios")
        
        if "performance" in test_categories or "security" in test_categories or "integration" in test_categories:
            test_methods.append("test_complete_system_acceptance")
        
        # 运行选定的测试方法
        for method in test_methods:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                f"tests/integration/test_final_acceptance.py::FinalAcceptanceTests::{method}",
                "-v", "--tb=short"
            ], cwd=project_root, capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)
            
            if result.returncode != 0:
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 自定义验收测试执行失败: {e}")
        return False


def generate_test_report(output_file: str = None) -> bool:
    """生成测试报告"""
    print("📊 生成验收测试报告...")
    
    try:
        # 运行测试并捕获输出
        result = subprocess.run([
            sys.executable, "tests/integration/test_final_acceptance.py"
        ], cwd=project_root, capture_output=True, text=True)
        
        # 保存报告
        if output_file:
            report_path = Path(output_file)
        else:
            report_path = Path(__file__).parent / "test_data" / f"acceptance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n错误输出:\n")
                f.write(result.stderr)
        
        print(f"✅ 报告已保存到: {report_path}")
        print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        return False


def check_test_environment() -> bool:
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    checks = []
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        checks.append(("Python版本", True, f"{python_version.major}.{python_version.minor}"))
    else:
        checks.append(("Python版本", False, f"{python_version.major}.{python_version.minor} (需要3.8+)"))
    
    # 检查关键依赖
    dependencies = ["playwright", "fastapi", "uvicorn", "requests", "pytest"]
    
    for dep in dependencies:
        try:
            __import__(dep)
            checks.append((f"依赖 {dep}", True, "已安装"))
        except ImportError:
            checks.append((f"依赖 {dep}", False, "未安装"))
    
    # 检查项目结构
    required_dirs = [
        project_root / "src",
        project_root / "tests",
        project_root / "tests" / "integration"
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            checks.append((f"目录 {dir_path.name}", True, "存在"))
        else:
            checks.append((f"目录 {dir_path.name}", False, "不存在"))
    
    # 检查关键文件
    required_files = [
        project_root / "src" / "main.py",
        project_root / "src" / "reasoning" / "agent.py",
        project_root / "tests" / "integration" / "test_final_acceptance.py"
    ]
    
    for file_path in required_files:
        if file_path.exists():
            checks.append((f"文件 {file_path.name}", True, "存在"))
        else:
            checks.append((f"文件 {file_path.name}", False, "不存在"))
    
    # 输出检查结果
    print("\n环境检查结果:")
    print("-" * 50)
    
    all_passed = True
    for name, passed, details in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {details}")
        if not passed:
            all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("✅ 测试环境检查通过")
    else:
        print("❌ 测试环境存在问题，请先解决上述问题")
    
    return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI浏览器代理最终验收测试")
    parser.add_argument("mode", choices=["quick", "full", "custom", "report", "check"], 
                       help="测试模式")
    parser.add_argument("--categories", nargs="+", 
                       choices=["system", "requirements", "user", "performance", "security", "integration"],
                       help="自定义测试类别 (仅在custom模式下有效)")
    parser.add_argument("--output", "-o", help="报告输出文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置详细输出
    if args.verbose:
        os.environ["VERBOSE"] = "1"
    
    print("🎯 AI浏览器代理最终验收测试")
    print("=" * 60)
    print(f"测试模式: {args.mode}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = False
    
    try:
        if args.mode == "check":
            success = check_test_environment()
        
        elif args.mode == "quick":
            if check_test_environment():
                success = run_quick_acceptance_test()
            else:
                print("❌ 环境检查未通过，无法运行测试")
        
        elif args.mode == "full":
            if check_test_environment():
                success = run_comprehensive_acceptance_test()
            else:
                print("❌ 环境检查未通过，无法运行测试")
        
        elif args.mode == "custom":
            if not args.categories:
                print("❌ 自定义模式需要指定测试类别")
                return 1
            
            if check_test_environment():
                success = run_custom_acceptance_test(args.categories)
            else:
                print("❌ 环境检查未通过，无法运行测试")
        
        elif args.mode == "report":
            success = generate_test_report(args.output)
        
        # 输出最终结果
        print("\n" + "=" * 60)
        if success:
            print("🎉 验收测试执行成功！")
        else:
            print("❌ 验收测试执行失败！")
        print("=" * 60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())