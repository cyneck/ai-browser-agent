#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小红书网络限制回退策略演示

演示当小红书出现网络访问限制（错误代码300012）时，
系统如何自动使用多重回退策略完成搜索任务。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reasoning.instruction_builder import InstructionBuilder
from src.common.logger import get_logger


def demonstrate_xiaohongshu_fallback():
    """演示小红书网络限制的回退策略"""
    logger = get_logger()
    builder = InstructionBuilder()
    
    print("="*60)
    print("小红书网络限制回退策略演示")
    print("="*60)
    
    # 测试用例：小红书搜索请求
    test_cases = [
        "打开小红书，查询合生汇附近咖啡店",
        "在小红书搜索北京美食推荐",
        "去小红书找上海网红打卡点"
    ]
    
    for i, user_text in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {user_text}")
        print("-" * 50)
        
        # 模拟空白页面（需要导航）
        page_data = {"is_valid": False, "url": "about:blank"}
        session_state = {"conversation_history": []}
        
        try:
            # 使用优化构建方法（会触发简单启发式规则）
            result = builder.build_optimized(user_text, page_data, session_state)
            
            print(f"生成的指令:")
            print(f"描述: {result.get('description', 'N/A')}")
            
            if 'fallback_info' in result:
                print(f"\n回退策略信息:")
                print(f"原因: {result['fallback_info']['reason']}")
                if 'primary_strategy' in result['fallback_info']:
                    print(f"主要策略: {result['fallback_info']['primary_strategy']}")
                if 'alternative_strategies' in result['fallback_info']:
                    print(f"备用策略: {', '.join(result['fallback_info']['alternative_strategies'])}")
                if 'strategy' in result['fallback_info']:
                    print(f"策略: {result['fallback_info']['strategy']}")
            
            print(f"\n执行步骤:")
            if 'steps' in result:
                for j, step in enumerate(result['steps'], 1):
                    action = step.get('action', 'unknown')
                    desc = step.get('description', 'N/A')
                    print(f"  {j}. {action}: {desc}")
                    if action == 'navigate':
                        print(f"     URL: {step.get('value', 'N/A')}")
                    elif action == 'fill':
                        print(f"     选择器: {step.get('selector', 'N/A')}")
                        print(f"     内容: {step.get('value', 'N/A')}")
            else:
                print(f"  单步操作: {result.get('action', 'N/A')}")
                
        except Exception as e:
            logger.error(f"测试用例失败: {e}")
            print(f"错误: {e}")
    
    print("\n" + "="*60)
    print("演示总结")
    print("="*60)
    print("当检测到小红书请求时，系统会自动应用以下回退策略：")
    print("1. 主要策略：通过百度使用 site:xiaohongshu.com 搜索")
    print("2. 备用策略：通过必应搜索小红书相关内容")
    print("3. 备用策略：尝试访问小红书移动版")
    print("\n这样可以有效规避网络访问限制（错误代码300012）")


def test_xiaohongshu_plugin_directly():
    """直接测试小红书插件的回退策略"""
    print("\n" + "="*60)
    print("小红书插件回退策略详细测试")
    print("="*60)
    
    builder = InstructionBuilder()
    
    # 找到小红书插件
    xiaohongshu_plugin = None
    for plugin in builder.plugin_manager.website_plugins:
        if plugin.can_handle_url("https://www.xiaohongshu.com"):
            xiaohongshu_plugin = plugin
            break
    
    if xiaohongshu_plugin and hasattr(xiaohongshu_plugin, 'build_fallback_search_strategies'):
        print("找到小红书插件，测试回退策略...")
        
        query = "合生汇附近咖啡店"
        strategies = xiaohongshu_plugin.build_fallback_search_strategies(query)
        
        for i, strategy in enumerate(strategies, 1):
            print(f"\n策略 {i}: {strategy['description']}")
            for j, step in enumerate(strategy['steps'], 1):
                print(f"  {j}. {step['action']}: {step['description']}")
                if 'value' in step:
                    print(f"     值: {step['value']}")
                if 'selector' in step:
                    print(f"     选择器: {step['selector']}")
    else:
        print("未找到小红书插件或插件不支持回退策略")


if __name__ == "__main__":
    try:
        demonstrate_xiaohongshu_fallback()
        test_xiaohongshu_plugin_directly()
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        sys.exit(1)