#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一执行器演示

演示重构后的执行器如何统一处理单步和多步指令。
单步指令现在被视为多步指令的特殊情况。
"""

import sys
import os
from unittest.mock import MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.action.executor import ActionExecutor


def demo_unified_execution():
    """演示统一的执行方式"""
    
    # 创建模拟的页面对象
    mock_page = MagicMock()
    mock_page.locator.return_value.click.return_value = None
    mock_page.locator.return_value.fill.return_value = None
    mock_page.goto.return_value = None
    
    # 创建执行器
    executor = ActionExecutor(mock_page)
    
    print("=== 统一执行器演示 ===\n")
    
    # 演示1: 单步指令（现在内部转换为多步）
    print("1. 单步指令执行:")
    single_step_instruction = {
        "action": "click",
        "selector": "button#submit",
        "description": "点击提交按钮"
    }
    
    result = executor.execute(single_step_instruction, {})
    print(f"   指令: {single_step_instruction}")
    print(f"   结果: 成功={result.get('success')}, 消息={result.get('message')}")
    print(f"   步骤结果数量: {len(result.get('step_results', []))}")
    print()
    
    # 演示2: 多步指令
    print("2. 多步指令执行:")
    multi_step_instruction = {
        "steps": [
            {
                "action": "navigate",
                "value": "https://example.com",
                "description": "导航到示例网站"
            },
            {
                "action": "fill",
                "selector": "input[name='search']",
                "value": "测试搜索",
                "description": "填写搜索框"
            },
            {
                "action": "click",
                "selector": "button[type='submit']",
                "description": "点击搜索按钮"
            }
        ],
        "description": "完整的搜索流程"
    }
    
    result = executor.execute(multi_step_instruction, {})
    print(f"   描述: {multi_step_instruction['description']}")
    print(f"   结果: 成功={result.get('success')}, 消息={result.get('message')}")
    print(f"   步骤结果数量: {len(result.get('step_results', []))}")
    
    # 显示每个步骤的结果
    for i, step_result in enumerate(result.get('step_results', []), 1):
        print(f"     步骤 {i}: 成功={step_result.get('success')}, 消息={step_result.get('message')}")
    print()
    
    # 演示3: 内部标准化过程
    print("3. 内部标准化演示:")
    print("   单步指令内部被转换为:")
    normalized = executor._normalize_to_multi_step(single_step_instruction)
    print(f"   {normalized}")
    print()
    
    print("=== 重构优势 ===")
    print("✓ 消除了冗余的单步/多步分支逻辑")
    print("✓ 统一的错误处理和超时管理")
    print("✓ 简化的代码维护")
    print("✓ 保持向后兼容性")
    print("✓ 单步执行是多步执行的特殊情况")


if __name__ == "__main__":
    demo_unified_execution()