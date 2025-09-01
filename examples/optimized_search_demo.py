#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化搜索逻辑演示
展示新的搜索逻辑如何避免双重操作并使用Enter键
"""

import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reasoning.instruction_builder import InstructionBuilder


def test_optimized_search_logic():
    """测试优化的搜索逻辑"""
    print("🔍 优化搜索逻辑测试")
    print("=" * 50)
    
    # 创建指令构建器
    builder = InstructionBuilder()
    
    # 测试用例1: 空白页面搜索新闻
    print("\n📰 测试1: 空白页面搜索新闻")
    user_text = "今天有哪些新闻"
    page_data = {"url": "about:blank", "is_valid": False}
    session_state = {}
    
    instruction = builder.build_optimized(user_text, page_data, session_state)
    print("🔸 用户输入:", user_text)
    print("🔸 生成指令:")
    print(json.dumps(instruction, ensure_ascii=False, indent=2))
    
    # 检查新的优化特性
    steps = instruction.get("steps", [])
    has_direct_navigation = any(step.get("action") == "navigate" and "bing.com" in step.get("value", "") for step in steps)
    has_enter_key = any(step.get("action") == "key" and step.get("value") == "Enter" for step in steps)
    has_extract_results = any(step.get("action") == "extract_results" for step in steps)
    
    print("\n✅ 优化特性检查:")
    print(f"   - 直接导航到Bing首页: {has_direct_navigation}")
    print(f"   - 使用Enter键搜索: {has_enter_key}")
    print(f"   - 包含结果提取: {has_extract_results}")
    
    # 检查是否避免了双重搜索
    navigate_count = sum(1 for step in steps if step.get("action") == "navigate")
    search_url_navigation = any(
        step.get("action") == "navigate" and "search?q=" in step.get("value", "") 
        for step in steps
    )
    
    print(f"   - 导航步骤数量: {navigate_count}")
    print(f"   - 避免了URL搜索+表单搜索双重操作: {not search_url_navigation}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成!")


if __name__ == "__main__":
    test_optimized_search_logic()