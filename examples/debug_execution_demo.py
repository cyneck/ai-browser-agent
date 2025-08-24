#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示增强的调试输出功能
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demonstrate_debug_output():
    """演示调试输出功能"""
    
    print("=== 增强的调试输出功能演示 ===")
    print()
    
    print("🔧 新增的调试功能:")
    features = [
        "✅ 详细的JSON指令格式化输出",
        "✅ 每个步骤的详细信息打印", 
        "✅ 生成的Jinja2模板代码完整显示",
        "✅ 模板渲染过程可视化",
        "✅ 执行前后的状态对比"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print()
    print("📝 示例调试输出格式:")
    
    # 模拟的调试输出示例
    sample_instruction = {
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
    }
    
    print("\n" + "="*60)
    print("执行指令:")
    print("="*60)
    print(json.dumps(sample_instruction, ensure_ascii=False, indent=2))
    print("="*60)
    
    print("\n执行步骤: click - 点击科技栏目链接")
    print("步骤详情:", json.dumps(sample_instruction["steps"][0], ensure_ascii=False, indent=2))
    
    print("\n生成的执行代码:")
    print("="*50)
    sample_generated_code = """# 点击元素
try:
    element = page.locator("a:has-text('科技')")
    element.click()
    result = {
        "success": True,
        "message": "成功点击元素 a:has-text('科技')"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "点击失败",
        "error": str(e)
    }"""
    print(sample_generated_code)
    print("="*50)
    
    print("\n🎯 调试输出的价值:")
    benefits = [
        "🔍 快速定位问题：能看到具体生成的代码",
        "🛠️ 验证选择器：确认模板渲染是否正确",
        "📊 追踪执行流程：了解每一步的详细过程",
        "🚫 发现错误原因：通过生成代码判断问题所在",
        "⚡ 优化性能：识别执行瓶颈和无效操作"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    print("\n🔧 使用方法:")
    usage_steps = [
        "1. 运行任何自动化任务",
        "2. 查看控制台日志输出",
        "3. 找到 '生成的执行代码' 部分",
        "4. 检查生成的代码是否符合预期",
        "5. 根据代码内容调整选择器或指令"
    ]
    
    for step in usage_steps:
        print(f"  {step}")
    
    print("\n💡 调试技巧:")
    tips = [
        "🎯 检查选择器：确认生成的选择器字符串是否正确",
        "🔄 验证逻辑：查看try-catch结构和错误处理",
        "📝 对比模板：将生成代码与模板文件对比",
        "🚀 测试单独执行：可以复制生成代码到浏览器控制台测试",
        "📊 分析执行流程：了解每个步骤的具体实现"
    ]
    
    for tip in tips:
        print(f"  {tip}")
    
    print("\n⚠️ 常见问题诊断:")
    
    common_issues = [
        {
            "issue": "选择器匹配多个元素",
            "symptom": "Playwright strict mode violation",
            "solution": "检查生成代码中的选择器，确保足够具体"
        },
        {
            "issue": "元素不可见或未加载",
            "symptom": "Element not visible or timeout",
            "solution": "添加wait步骤，确保元素加载完成"
        },
        {
            "issue": "模板渲染错误",
            "symptom": "Template rendering failed",
            "solution": "检查指令格式，确保所需字段存在"
        },
        {
            "issue": "执行代码语法错误",
            "symptom": "SyntaxError in generated code",
            "solution": "检查模板文件，确认Jinja2语法正确"
        }
    ]
    
    for issue in common_issues:
        print(f"\n  问题: {issue['issue']}")
        print(f"  症状: {issue['symptom']}")
        print(f"  解决: {issue['solution']}")
    
    print("\n🚀 快速测试命令:")
    test_commands = [
        "# CLI模式测试",
        "python src/main.py --cli",
        "",
        "# Web模式测试", 
        "python src/main.py --web",
        "",
        "# 查看详细日志",
        "tail -f logs/executor.log  # 如果有日志文件",
    ]
    
    for command in test_commands:
        if command:
            print(f"  {command}")
        else:
            print()

if __name__ == "__main__":
    demonstrate_debug_output()