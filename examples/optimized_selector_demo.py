#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试优化后的选择器生成策略
"""

import json

def test_optimized_selector_examples():
    """展示优化后的选择器生成示例"""
    
    print("=== 优化后的选择器生成策略 ===")
    print()
    
    examples = [
        {
            "scenario": "点击科技链接",
            "original_fragile": ".nav-link.nav-hover:nth-child(2)",
            "optimized_robust": "a:has-text('科技'), a[href*='tech'], .nav-tech",
            "explanation": "使用文本内容优先，href属性作为备选，避免依赖DOM位置"
        },
        {
            "scenario": "填写登录用户名",
            "original_fragile": ".form-control.username-input",
            "optimized_robust": "input[name='username'], #username, [placeholder*='用户名']",
            "explanation": "优先使用name属性，ID作为备选，placeholder作为语义匹配"
        },
        {
            "scenario": "点击搜索按钮",
            "original_fragile": ".btn.btn-primary:nth-child(3)",
            "optimized_robust": "button:has-text('搜索'), input[type='submit'], #search-btn",
            "explanation": "基于文本内容最稳定，类型属性和ID作为备选"
        },
        {
            "scenario": "选择下拉菜单",
            "original_fragile": "div.dropdown > ul > li:nth-child(2)",
            "optimized_robust": "select[name='category'], #category-select, [aria-label*='分类']",
            "explanation": "优先使用语义化属性，避免深层DOM结构依赖"
        },
        {
            "scenario": "点击导航菜单",
            "original_fragile": "nav > ul > li:first-child > a",
            "optimized_robust": "a:has-text('首页'), a[href='/'], nav a:first",
            "explanation": "文本内容最可靠，href属性次之，结构位置作为最后备选"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"示例 {i}: {example['scenario']}")
        print(f"  原始脆弱选择器: {example['original_fragile']}")
        print(f"  优化稳定选择器: {example['optimized_robust']}")
        print(f"  优化说明: {example['explanation']}")
        print()
    
    print("=== 选择器优先级策略 ===")
    priority_levels = [
        "1. 唯一标识符 (ID, name, data-*)",
        "2. 语义和内容 (has-text, aria-label, 语义标签)",
        "3. 属性部分匹配 (href*, class*, placeholder*)",
        "4. 多重备选策略 (逗号分隔的多个选择器)",
        "5. 避免脆弱选择器 (nth-child, 深层嵌套, 纯样式类)"
    ]
    
    for level in priority_levels:
        print(f"  {level}")
    
    print()
    print("=== JSON指令格式改进 ===")
    
    # 展示从原始问题格式到优化格式的转换
    original_problematic = [
        {'action': 'click', 'description': '点击科技栏目链接', 'selector': '.nav-link.nav-hover:nth-child(2)', 'value': None}, 
        {'action': 'wait', 'description': '等待页面加载完成', 'selector': 'body', 'value': 3000}
    ]
    
    optimized_format = {
        "steps": [
            {
                "action": "wait",
                "selector": "nav, .nav-menu, [role='navigation']",
                "timeout": 5000,
                "description": "等待导航菜单加载"
            },
            {
                "action": "click",
                "selector": "a:has-text('科技'), a[href*='tech'], .nav-tech",
                "description": "点击科技栏目链接"
            },
            {
                "action": "wait",
                "value": 3000,
                "description": "等待页面加载完成"
            }
        ],
        "description": "导航到科技栏目"
    }
    
    print("原始有问题的格式:")
    print(json.dumps(original_problematic, ensure_ascii=False, indent=2))
    print()
    
    print("优化后的格式:")
    print(json.dumps(optimized_format, ensure_ascii=False, indent=2))
    print()
    
    print("=== 改进要点 ===")
    improvements = [
        "✅ 使用标准的多步格式 {'steps': [...], 'description': '...'}", 
        "✅ 增加等待导航元素加载的步骤",
        "✅ 使用多重备选选择器 '选择器1, 选择器2, 选择器3'",
        "✅ 优先使用文本内容匹配 :has-text('科技')",
        "✅ 提供属性匹配备选 a[href*='tech']",
        "✅ 避免依赖DOM位置的脆弱选择器"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")

if __name__ == "__main__":
    test_optimized_selector_examples()