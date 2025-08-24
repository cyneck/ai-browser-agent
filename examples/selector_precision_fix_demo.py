#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解决Playwright严格模式选择器问题的示例
"""

import json

def demonstrate_selector_precision_fix():
    """演示如何修复选择器精确性问题"""
    
    print("=== Playwright严格模式选择器问题修复 ===")
    print()
    
    # 实际遇到的问题
    print("🚫 问题描述:")
    print("选择器 'a:has-text(\"科技\"), .nav-link.nav-hover' 匹配了18个元素")
    print("Playwright严格模式要求选择器必须匹配唯一元素")
    print()
    
    print("📋 错误详情:")
    error_elements = [
        "1) <a class=\"nav-link nav-hover\" href=\"https://news.qq.com/\">要闻</a>",
        "2) <a class=\"nav-link nav-hover\" href=\"https://news.qq.com/ch/tech/\">科技</a>",
        "3) <a class=\"nav-link nav-hover\" href=\"https://news.qq.com/ch/finance/\">财经</a>",
        "... (共18个元素都有 .nav-link.nav-hover 类)"
    ]
    
    for element in error_elements:
        print(f"   {element}")
    print()
    
    print("🔍 问题分析:")
    problems = [
        "❌ .nav-link.nav-hover 是一个过于宽泛的选择器",
        "❌ 它匹配了所有导航链接，而不是特定的'科技'链接", 
        "❌ 虽然 a:has-text('科技') 很精确，但备选选择器破坏了精确性",
        "❌ Playwright会尝试所有选择器，如果任何一个匹配多个元素就报错"
    ]
    
    for problem in problems:
        print(f"   {problem}")
    print()
    
    print("✅ 解决方案:")
    
    # 展示不同的修复策略
    solutions = [
        {
            "strategy": "1. 使用单一精确选择器",
            "selector": "a:has-text('科技')",
            "explanation": "只使用最精确的选择器，不提供可能模糊的备选"
        },
        {
            "strategy": "2. 使用组合精确选择器", 
            "selector": "a[href*='/tech/']:has-text('科技'), a.nav-link[href*='tech']",
            "explanation": "所有备选选择器都足够精确，不会匹配多个元素"
        },
        {
            "strategy": "3. 使用更具体的属性组合",
            "selector": "a[href='https://news.qq.com/ch/tech/']",
            "explanation": "直接使用完整的href属性，最具唯一性"
        },
        {
            "strategy": "4. 使用角色和文本组合",
            "selector": "a:has-text('科技')[class*='nav-link']",
            "explanation": "在文本基础上添加类约束，确保唯一性"
        }
    ]
    
    for solution in solutions:
        print(f"   {solution['strategy']}")
        print(f"      选择器: {solution['selector']}")
        print(f"      说明: {solution['explanation']}")
        print()
    
    print("📝 优化后的JSON指令示例:")
    
    # 修复前的问题指令
    problematic_instruction = {
        "action": "click",
        "selector": "a:has-text('科技'), .nav-link.nav-hover",
        "description": "点击科技栏目链接"
    }
    
    # 修复后的精确指令
    fixed_instruction = {
        "action": "click", 
        "selector": "a:has-text('科技')",
        "description": "点击科技栏目链接"
    }
    
    # 带备选的安全指令
    safe_fallback_instruction = {
        "action": "click",
        "selector": "a[href*='/tech/']:has-text('科技'), a[href='https://news.qq.com/ch/tech/']",
        "description": "点击科技栏目链接"
    }
    
    print("❌ 有问题的指令:")
    print(json.dumps(problematic_instruction, ensure_ascii=False, indent=2))
    print()
    
    print("✅ 修复后的精确指令:")
    print(json.dumps(fixed_instruction, ensure_ascii=False, indent=2))
    print()
    
    print("✅ 带安全备选的指令:")
    print(json.dumps(safe_fallback_instruction, ensure_ascii=False, indent=2))
    print()
    
    print("🎯 选择器设计原则:")
    principles = [
        "✅ 优先使用唯一性最强的单一选择器",
        "✅ 备选选择器必须同样精确，不能为了容错而牺牲精确性",
        "✅ 测试每个选择器是否只匹配目标元素",
        "✅ 避免使用过于宽泛的类选择器作为备选",
        "✅ 如果文本内容唯一，就直接使用文本选择器",
        "✅ 组合多个属性来提高选择器的唯一性"
    ]
    
    for principle in principles:
        print(f"   {principle}")
    
    print()
    print("🔧 实用调试技巧:")
    debug_tips = [
        "1. 使用浏览器开发者工具测试选择器",
        "2. 在控制台运行: document.querySelectorAll('your-selector').length",
        "3. 确保返回值为1，表示只匹配一个元素",
        "4. 对于Playwright，可以用page.locator('selector').count()测试",
        "5. 如果count > 1，则需要让选择器更精确"
    ]
    
    for tip in debug_tips:
        print(f"   {tip}")

if __name__ == "__main__":
    demonstrate_selector_precision_fix()