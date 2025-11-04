#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试运行脚本

提供便捷的测试执行入口，支持不同类型的测试。
"""

import sys
import os
import subprocess
from pathlib import Path


def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/unit/", 
            "-v", 
            "--tb=short"
        ], cwd=Path.cwd())
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 单元测试执行失败: {e}")
        return False


def run_integration_tests(mode="quick"):
    """运行集成测试"""
    print(f"🔄 运行集成测试 ({mode} 模式)...")
    try:
        result = subprocess.run([
            sys.executable, 
            "tests/integration/run_integration_tests.py",
            "--mode", mode,
            "--report"
        ], cwd=Path.cwd())
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 集成测试执行失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("🚀 运行完整测试套件...")
    
    success = True
    
    # 运行单元测试
    if not run_unit_tests():
        success = False
        print("⚠️ 单元测试失败")
    
    # 运行集成测试
    if not run_integration_tests("all"):
        success = False
        print("⚠️ 集成测试失败")
    
    return success


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python run_tests.py [unit|integration|all] [options]")
        print("  unit        - 运行单元测试")
        print("  integration - 运行集成测试")
        print("  all         - 运行所有测试")
        sys.exit(1)
    
    test_type = sys.argv[1]
    
    if test_type == "unit":
        success = run_unit_tests()
    elif test_type == "integration":
        mode = sys.argv[2] if len(sys.argv) > 2 else "quick"
        success = run_integration_tests(mode)
    elif test_type == "all":
        success = run_all_tests()
    else:
        print(f"❌ 未知的测试类型: {test_type}")
        sys.exit(1)
    
    if success:
        print("✅ 测试执行成功")
        sys.exit(0)
    else:
        print("❌ 测试执行失败")
        sys.exit(1)


if __name__ == "__main__":
    main()