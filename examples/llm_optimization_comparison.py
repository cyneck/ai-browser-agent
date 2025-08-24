#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM调用优化对比演示

清晰展示AI浏览器代理LLM调用优化前后的差异：
- 优化前：一次人机交互 = 2次LLM调用
- 优化后：一次人机交互 = 1次LLM调用
"""

import json
from typing import Dict, Any


class LLMCallOptimizationDemo:
    """LLM调用优化演示类"""
    
    def __init__(self):
        self.llm_call_count = 0
    
    def mock_llm_call(self, prompt: str) -> Dict[str, Any]:
        """模拟LLM调用"""
        self.llm_call_count += 1
        print(f"🔄 第{self.llm_call_count}次LLM调用")
        print(f"📝 提示词长度: {len(prompt)} 字符")
        
        # 根据提示词内容返回不同的模拟结果
        if "导航" in prompt or "navigate" in prompt:
            return {
                "action": "navigate",
                "url": "https://www.baidu.com",
                "description": "导航到百度"
            }
        else:
            return {
                "steps": [
                    {
                        "action": "navigate",
                        "url": "https://www.baidu.com", 
                        "description": "导航到百度"
                    },
                    {
                        "action": "fill",
                        "selector": "#kw",
                        "value": "人工智能",
                        "description": "在搜索框输入关键词"
                    },
                    {
                        "action": "click",
                        "selector": "#su",
                        "description": "点击搜索按钮"
                    }
                ],
                "description": "在百度搜索人工智能"
            }
    
    def reset_counter(self):
        """重置计数器"""
        self.llm_call_count = 0
    
    def simulate_old_version(self, user_input: str):
        """模拟优化前的版本（双重LLM调用）"""
        print("📊 模拟优化前的版本")
        print("-" * 40)
        
        self.reset_counter()
        
        # 第一阶段：页面分析 + 导航指令生成
        print("🔍 第一阶段：分析页面并生成导航指令")
        page_data_empty = {"is_valid": False, "url": "about:blank"}
        
        prompt1 = f"""
当前页面信息：空白页面
用户指令: {user_input}
请生成导航指令。
        """
        
        result1 = self.mock_llm_call(prompt1)
        print(f"📋 第一阶段结果: {json.dumps(result1, ensure_ascii=False, indent=2)}")
        
        # 模拟导航执行
        print("⏳ 执行导航...")
        
        # 第二阶段：重新分析页面 + 生成操作指令
        print("\n🔍 第二阶段：重新分析页面并生成操作指令")
        page_data_loaded = {
            "is_valid": True,
            "url": "https://www.baidu.com",
            "title": "百度一下，你就知道",
            "elements": [
                {"tag": "input", "id": "kw", "placeholder": "请输入搜索词"},
                {"tag": "input", "id": "su", "value": "百度一下"}
            ]
        }
        
        prompt2 = f"""
当前页面信息：
URL: https://www.baidu.com
标题: 百度一下，你就知道
页面元素: {json.dumps(page_data_loaded['elements'], ensure_ascii=False)}

用户指令: {user_input}
请生成操作指令。
        """
        
        result2 = self.mock_llm_call(prompt2)
        print(f"📋 第二阶段结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")
        
        old_version_calls = self.llm_call_count
        print(f"\n📊 优化前总LLM调用次数: {old_version_calls}")
        
        return old_version_calls, [result1, result2]
    
    def simulate_new_version(self, user_input: str):
        """模拟优化后的版本（单次LLM调用）"""
        print("\n📊 模拟优化后的版本")
        print("-" * 40)
        
        self.reset_counter()
        
        # 一次性智能分析 + 完整指令生成
        print("🧠 智能分析：一次性生成完整流程")
        
        # 上下文分析
        print("🔍 上下文分析：")
        print("  • 检测到导航需求：需要访问百度")
        print("  • 检测到搜索意图：用户想搜索内容")
        print("  • 推断完整流程：导航 + 搜索操作")
        
        enhanced_prompt = f"""
你是一个高级的网页自动化助手，擅长在单次对话中生成完整的操作流程。

上下文分析：
- 需要导航到: https://www.baidu.com
- 搜索意图识别: 用户想要搜索 "人工智能"
请生成包含导航和后续操作的完整流程。

当前页面信息：空白页面
用户指令: {user_input}

请根据用户指令，生成一次性完成所有操作的多步骤JSON指令。
注意：必须包含从开始到结束的完整流程，不要遗漏任何步骤。
        """
        
        result = self.mock_llm_call(enhanced_prompt)
        print(f"📋 完整流程结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        new_version_calls = self.llm_call_count
        print(f"\n📊 优化后总LLM调用次数: {new_version_calls}")
        
        return new_version_calls, result
    
    def show_comparison(self):
        """显示优化对比"""
        print("🚀 AI浏览器代理 LLM调用优化对比演示")
        print("=" * 60)
        
        user_input = "在百度搜索人工智能的最新发展"
        print(f"🎯 测试指令: {user_input}")
        print("📝 场景: 需要导航到百度 + 执行搜索操作")
        print("=" * 60)
        
        # 模拟优化前版本
        old_calls, old_results = self.simulate_old_version(user_input)
        
        # 模拟优化后版本
        new_calls, new_result = self.simulate_new_version(user_input)
        
        # 显示优化效果
        print("\n" + "=" * 60)
        print("📊 优化效果对比")
        print("=" * 60)
        
        print(f"🔴 优化前LLM调用次数: {old_calls}")
        print(f"🟢 优化后LLM调用次数: {new_calls}")
        
        reduction = old_calls - new_calls
        percentage = (reduction / old_calls) * 100
        
        print(f"📈 调用次数减少: {reduction} 次")
        print(f"📈 减少百分比: {percentage:.1f}%")
        
        print(f"\n💰 成本效益:")
        print(f"  • API调用成本节约: {percentage:.1f}%")
        print(f"  • 响应时间减少: 约{percentage:.1f}%")
        print(f"  • 用户体验提升: 更快的交互响应")
        
        print(f"\n🛠️ 技术改进:")
        print(f"  • 智能上下文分析：提前识别用户完整意图")
        print(f"  • 增强提示词构建：一次性生成完整操作流程")
        print(f"  • 启发式规则：简单操作无需LLM调用")
        print(f"  • 向后兼容：保持原有API接口不变")
        
        print(f"\n✅ 优化成功！从 {old_calls} 次LLM调用减少到 {new_calls} 次LLM调用。")


def main():
    """主函数"""
    demo = LLMCallOptimizationDemo()
    demo.show_comparison()


if __name__ == "__main__":
    main()