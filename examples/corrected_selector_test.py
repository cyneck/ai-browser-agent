#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修正后的选择器策略
"""

import json

def test_corrected_selector_strategy():
    """测试修正后避免严格模式违规的选择器策略"""
    
    print("=== 修正后的选择器策略测试 ===")
    print()
    
    # 原始问题案例
    print("📋 原始问题案例:")
    original_case = {
        "html_element": '<a href="https://news.qq.com/ch/tech/" target="_blank" rel="noopener" class="nav-link nav-hover">科技</a>',
        "context": "页面有18个 .nav-link.nav-hover 元素",
        "problematic_instruction": [
            {'action': 'click', 'description': '点击科技栏目链接', 'selector': '.nav-link.nav-hover:nth-child(2)', 'value': None}, 
            {'action': 'wait', 'description': '等待页面加载完成', 'selector': 'body', 'value': 3000}
        ]
    }
    
    print(f"目标HTML: {original_case['html_element']}")
    print(f"页面环境: {original_case['context']}")
    print("原始有问题的指令:")
    print(json.dumps(original_case['problematic_instruction'], ensure_ascii=False, indent=2))
    print()
    
    # 修正后的策略
    print("✅ 修正后的精确选择器策略:")
    
    corrected_strategies = [
        {
            "name": "策略1: 纯文本内容定位",
            "instruction": {
                "steps": [
                    {
                        "action": "click",
                        "selector": "a:has-text('科技')",
                        "description": "点击科技栏目链接"
                    },
                    {
                        "action": "wait",
                        "value": 3000,
                        "description": "等待页面加载完成"
                    }
                ],
                "description": "导航到科技栏目"
            },
            "explanation": "直接使用文本内容，最精确且不会匹配多个元素"
        },
        {
            "name": "策略2: href属性精确匹配",
            "instruction": {
                "steps": [
                    {
                        "action": "click", 
                        "selector": "a[href='https://news.qq.com/ch/tech/']",
                        "description": "点击科技栏目链接"
                    },
                    {
                        "action": "wait",
                        "value": 3000, 
                        "description": "等待页面加载完成"
                    }
                ],
                "description": "导航到科技栏目"
            },
            "explanation": "使用完整href属性，具有唯一性保证"
        },
        {
            "name": "策略3: 组合属性定位",
            "instruction": {
                "steps": [
                    {
                        "action": "click",
                        "selector": "a[href*='/tech/']:has-text('科技')",
                        "description": "点击科技栏目链接"
                    },
                    {
                        "action": "wait",
                        "value": 3000,
                        "description": "等待页面加载完成"
                    }
                ],
                "description": "导航到科技栏目"
            },
            "explanation": "组合href部分匹配和文本内容，双重保证唯一性"
        },
        {
            "name": "策略4: 安全的多重备选",
            "instruction": {
                "steps": [
                    {
                        "action": "click",
                        "selector": "a[href*='/tech/']:has-text('科技'), a[href='https://news.qq.com/ch/tech/']",
                        "description": "点击科技栏目链接"
                    },
                    {
                        "action": "wait",
                        "value": 3000,
                        "description": "等待页面加载完成"
                    }
                ],
                "description": "导航到科技栏目"
            },
            "explanation": "提供备选选择器，但每个都足够精确，不会匹配多个元素"
        }
    ]
    
    for i, strategy in enumerate(corrected_strategies, 1):
        print(f"\n{strategy['name']}:")
        print(f"说明: {strategy['explanation']}")
        print("JSON指令:")
        print(json.dumps(strategy['instruction'], ensure_ascii=False, indent=2))
    
    print("\n" + "="*60)
    print("🎯 关键改进点:")
    
    improvements = [
        "✅ 使用标准的多步格式 {'steps': [...], 'description': '...'}", 
        "✅ 移除了过于宽泛的 .nav-link.nav-hover 选择器",
        "✅ 优先使用文本内容 :has-text('科技') 进行精确定位",
        "✅ 提供href属性作为可靠的唯一标识符",
        "✅ 确保所有备选选择器都具有相同的精确性",
        "✅ 避免依赖DOM位置的 :nth-child() 选择器",
        "✅ 每个选择器都只匹配单一目标元素"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")
    
    print("\n🔍 选择器验证方法:")
    validation_methods = [
        "1. 浏览器控制台: document.querySelectorAll('a:has-text(\"科技\")').length",
        "2. Playwright: await page.locator('a:has-text(\"科技\")').count()",
        "3. 期望结果: 返回值应该等于 1",
        "4. 如果 > 1: 需要增加更多约束条件",
        "5. 如果 = 0: 选择器不正确或元素未加载"
    ]
    
    for method in validation_methods:
        print(f"  {method}")
    
    print(f"\n💡 最佳实践总结:")
    best_practices = [
        "🎯 优先级: 文本内容 > 唯一属性 > 组合属性 > 结构位置",
        "🛡️ 安全原则: 每个选择器必须精确匹配唯一元素", 
        "🔄 备选策略: 只有在保证精确性的前提下才提供备选",
        "🚫 避免陷阱: 不要为了容错而使用过于宽泛的选择器",
        "✅ 测试验证: 始终验证选择器的唯一性"
    ]
    
    for practice in best_practices:
        print(f"  {practice}")

if __name__ == "__main__":
    test_corrected_selector_strategy()