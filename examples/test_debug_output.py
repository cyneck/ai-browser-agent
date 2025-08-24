#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实际测试增强的调试输出
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from src.action.executor import ActionExecutor
from src.common.logger import get_logger

def test_debug_output():
    """测试实际的调试输出"""
    
    print("=== 实际调试输出测试 ===")
    print()
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 创建执行器
        executor = ActionExecutor(page)
        
        # 导航到一个测试页面
        page.goto("data:text/html,<html><body><h1>测试页面</h1><a href='#tech'>科技</a><button id='test-btn'>测试按钮</button></body></html>")
        
        print("🧪 测试指令1: 点击链接")
        instruction1 = {
            "action": "click",
            "selector": "a:has-text('科技')",
            "description": "点击科技链接"
        }
        
        result1 = executor.execute(instruction1, {})
        print(f"执行结果: {'成功' if result1.get('success') else '失败'}")
        print(f"消息: {result1.get('message', '无')}")
        print()
        
        print("🧪 测试指令2: 多步操作")
        instruction2 = {
            "steps": [
                {
                    "action": "click",
                    "selector": "button:has-text('测试按钮')",
                    "description": "点击测试按钮"
                },
                {
                    "action": "wait",
                    "value": 1000,
                    "description": "等待1秒"
                }
            ],
            "description": "执行多步测试操作"
        }
        
        result2 = executor.execute(instruction2, {})
        print(f"执行结果: {'成功' if result2.get('success') else '失败'}")
        print(f"消息: {result2.get('message', '无')}")
        print()
        
        print("🧪 测试指令3: 故意的错误选择器")
        instruction3 = {
            "action": "click",
            "selector": "a:has-text('不存在的元素')",
            "description": "点击不存在的元素"
        }
        
        result3 = executor.execute(instruction3, {})
        print(f"执行结果: {'成功' if result3.get('success') else '失败'}")
        print(f"错误消息: {result3.get('error', '无')}")
        print()
        
        browser.close()
    
    print("✅ 测试完成！")
    print()
    print("📝 观察要点:")
    observations = [
        "🔍 查看日志中的 '执行指令:' 部分 - 显示格式化的JSON",
        "👀 注意 '生成的执行代码:' 部分 - 显示实际执行的Python代码",
        "📊 观察每个步骤的详细信息输出",
        "🚫 错误情况下的详细错误信息和生成代码",
        "⏱️ 执行时间和步骤流程的可视化"
    ]
    
    for obs in observations:
        print(f"  {obs}")

if __name__ == "__main__":
    # 配置日志级别确保能看到debug信息
    logger = get_logger()
    logger.setLevel("INFO")
    
    test_debug_output()