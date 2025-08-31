#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人类行为模拟功能演示

演示AI浏览器智能体的人类行为模拟功能，展示如何避免触发反爬虫机制。
包括不同的行为模式、配置选项和实际使用场景。
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from playwright.sync_api import sync_playwright
from src.action.executor import ActionExecutor
from src.action.human_behavior_simulator import HumanBehaviorSimulator
from src.common.logger import get_logger


def demo_behavior_modes():
    """演示不同的行为模式"""
    print("=" * 60)
    print("🎭 人类行为模拟 - 模式演示")
    print("=" * 60)
    
    modes = ["conservative", "moderate", "aggressive"]
    
    for mode in modes:
        print(f"\n📋 {mode.upper()} 模式:")
        
        config = {"behavior_mode": mode, "enabled": True}
        simulator = HumanBehaviorSimulator(config)
        
        print(f"   基础延迟范围: {simulator.effective_config['base_delay_min']:.2f}s - {simulator.effective_config['base_delay_max']:.2f}s")
        print(f"   操作间隔范围: {simulator.effective_config['action_interval_min']:.2f}s - {simulator.effective_config['action_interval_max']:.2f}s")
        print(f"   随机暂停概率: {simulator.effective_config['random_pause_probability']:.1%}")
        print(f"   随机暂停范围: {simulator.effective_config['random_pause_min']:.1f}s - {simulator.effective_config['random_pause_max']:.1f}s")
        
        # 展示实际延迟生成
        delays = [simulator.get_base_delay() for _ in range(5)]
        intervals = [simulator.get_action_interval("click") for _ in range(5)]
        
        print(f"   示例基础延迟: {[f'{d:.2f}s' for d in delays]}")
        print(f"   示例操作间隔: {[f'{i:.2f}s' for i in intervals]}")


def demo_typing_simulation():
    """演示打字行为模拟"""
    print("\n" + "=" * 60)
    print("⌨️  人类打字行为模拟演示")
    print("=" * 60)
    
    simulator = HumanBehaviorSimulator({
        "typing_speed_min": 3,
        "typing_speed_max": 8
    })
    
    test_texts = [
        "hello",
        "Hello, World!",
        "user@example.com",
        "This is a longer sentence with punctuation."
    ]
    
    for text in test_texts:
        delays = simulator.get_typing_delay(text)
        total_time = sum(delays)
        avg_speed = len(text) / total_time if total_time > 0 else 0
        
        print(f"\n📝 文本: '{text}'")
        print(f"   字符数: {len(text)}")
        print(f"   总打字时间: {total_time:.2f}s")
        print(f"   平均速度: {avg_speed:.1f} 字符/秒")
        print(f"   字符延迟: {[f'{d:.3f}' for d in delays[:10]]}" + ("..." if len(delays) > 10 else ""))


def demo_adaptive_timing():
    """演示自适应时间调整"""
    print("\n" + "=" * 60)
    print("🧠 自适应时间调整演示")
    print("=" * 60)
    
    simulator = HumanBehaviorSimulator({
        "adaptive_timing": True,
        "action_interval_min": 1.0,
        "action_interval_max": 2.0
    })
    
    print("📊 模拟操作历史对时间调整的影响:")
    
    # 场景1: 快速操作
    print("\n🏃 快速操作场景 (平均间隔1秒):")
    current_time = time.time()
    for i in range(5):
        simulator.record_action("click", True, 0.1)
        simulator.action_history[-1]["timestamp"] = current_time + i * 1.0
        
    fast_interval = simulator.get_action_interval("click")
    print(f"   调整后间隔: {fast_interval:.2f}s (应该增加以避免过于频繁)")
    
    # 场景2: 慢速操作
    print("\n🐌 慢速操作场景 (平均间隔10秒):")
    simulator.action_history.clear()  # 清空历史
    for i in range(5):
        simulator.record_action("click", True, 0.1)
        simulator.action_history[-1]["timestamp"] = current_time + i * 10.0
        
    slow_interval = simulator.get_action_interval("click")
    print(f"   调整后间隔: {slow_interval:.2f}s (可能减少以提高效率)")


def demo_mouse_movement():
    """演示鼠标移动模拟"""
    print("\n" + "=" * 60)
    print("🖱️  鼠标移动轨迹模拟演示")
    print("=" * 60)
    
    simulator = HumanBehaviorSimulator({
        "mouse_move_enabled": True,
        "mouse_move_steps": 10,
        "mouse_move_duration": 1.0
    })
    
    # 模拟鼠标轨迹计算
    start_pos = (100, 100)
    end_pos = (500, 300)
    steps = simulator.effective_config["mouse_move_steps"]
    
    print(f"🎯 从 {start_pos} 移动到 {end_pos}")
    print(f"   移动步骤: {steps}")
    print(f"   移动时长: {simulator.effective_config['mouse_move_duration']}s")
    print(f"   每步间隔: {simulator.effective_config['mouse_move_duration']/steps:.3f}s")
    
    # 计算一些示例路径点
    print("\n📍 示例路径点 (贝塞尔曲线):")
    for i in range(0, steps + 1, 2):
        t = i / steps
        # 简化的线性插值作为示例
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
        print(f"   步骤 {i:2d}: ({x:6.1f}, {y:6.1f})")


def demo_anti_bot_features():
    """演示反机器人检测规避功能"""
    print("\n" + "=" * 60)
    print("🛡️  反机器人检测规避功能演示")
    print("=" * 60)
    
    features = [
        {
            "name": "随机化时间间隔",
            "description": "操作间的时间间隔随机化，避免机械式的固定节奏",
            "config": {"action_interval_min": 0.5, "action_interval_max": 3.0}
        },
        {
            "name": "自然鼠标移动",
            "description": "模拟真实用户的鼠标移动轨迹，使用贝塞尔曲线",
            "config": {"mouse_move_enabled": True, "mouse_move_steps": 20}
        },
        {
            "name": "人类打字模式",
            "description": "模拟真实打字速度和节奏，包括停顿和修正",
            "config": {"typing_speed_min": 3, "typing_speed_max": 8}
        },
        {
            "name": "随机暂停",
            "description": "随机插入较长的暂停，模拟用户思考时间",
            "config": {"random_pause_probability": 0.15, "random_pause_min": 2.0, "random_pause_max": 8.0}
        },
        {
            "name": "页面加载等待",
            "description": "模拟真实用户等待页面加载的行为",
            "config": {"page_load_wait_min": 1.0, "page_load_wait_max": 3.5}
        },
        {
            "name": "行为抖动",
            "description": "在时间计算中添加小幅随机变化，增加自然性",
            "config": {"jitter_enabled": True}
        },
        {
            "name": "自适应调整",
            "description": "根据历史操作频率自动调整后续操作的时间间隔",
            "config": {"adaptive_timing": True}
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i:2d}. 📌 {feature['name']}")
        print(f"     💡 {feature['description']}")
        print(f"     ⚙️  配置: {feature['config']}")


def demo_practical_scenario():
    """演示实际使用场景"""
    print("\n" + "=" * 60)
    print("🎬 实际使用场景演示")
    print("=" * 60)
    
    print("📋 场景: 模拟用户登录一个网站")
    print("   1. 导航到登录页面")
    print("   2. 填写用户名")
    print("   3. 填写密码") 
    print("   4. 点击登录按钮")
    print("   5. 等待页面加载")
    
    # 创建保守模式配置（适合敏感网站）
    conservative_config = {
        "behavior_mode": "conservative",
        "enabled": True,
        "mouse_move_enabled": True,
        "random_pause_probability": 0.2
    }
    
    simulator = HumanBehaviorSimulator(conservative_config)
    
    print(f"\n⚙️  使用配置模式: {conservative_config['behavior_mode']}")
    print("🕐 预估时间分布:")
    
    steps = [
        ("导航", "navigate"),
        ("填写用户名", "fill"),
        ("填写密码", "fill"),
        ("点击登录", "click"),
        ("等待加载", "wait")
    ]
    
    total_estimated_time = 0
    
    for step_name, action_type in steps:
        base_delay = simulator.get_base_delay()
        action_interval = simulator.get_action_interval(action_type)
        page_wait = simulator.get_page_load_wait_time() if action_type == "navigate" else 0
        
        step_time = base_delay + action_interval + page_wait
        total_estimated_time += step_time
        
        print(f"   {step_name:12s}: {step_time:5.2f}s (基础:{base_delay:.2f}s + 间隔:{action_interval:.2f}s" +
              (f" + 页面等待:{page_wait:.2f}s" if page_wait > 0 else "") + ")")
    
    print(f"\n⏱️  总预估时间: {total_estimated_time:.2f}s")
    print(f"📊 随机暂停概率: {simulator.effective_config['random_pause_probability']:.1%}")
    
    if simulator.should_add_random_pause():
        pause_time = simulator.get_random_pause_duration()
        print(f"🛑 额外随机暂停: {pause_time:.2f}s")
        total_estimated_time += pause_time
        
    print(f"🎯 最终预估时间: {total_estimated_time:.2f}s")


def demo_configuration_comparison():
    """演示不同配置的对比"""
    print("\n" + "=" * 60)
    print("⚖️  配置模式对比分析")
    print("=" * 60)
    
    configs = {
        "禁用模拟": {"enabled": False},
        "激进模式": {"behavior_mode": "aggressive", "enabled": True},
        "适中模式": {"behavior_mode": "moderate", "enabled": True},
        "保守模式": {"behavior_mode": "conservative", "enabled": True}
    }
    
    print("📊 相同操作序列的时间对比 (5个点击操作):")
    print(f"{'模式':12s} {'总时间':>8s} {'平均间隔':>10s} {'检测风险':>10s}")
    print("-" * 50)
    
    for mode_name, config in configs.items():
        simulator = HumanBehaviorSimulator(config)
        
        if not simulator.is_enabled():
            total_time = 0
            avg_interval = 0
            risk_level = "🔴 高"
        else:
            # 模拟5次点击操作的时间
            times = []
            for _ in range(5):
                base_delay = simulator.get_base_delay()
                action_interval = simulator.get_action_interval("click")
                times.append(base_delay + action_interval)
                
            total_time = sum(times)
            avg_interval = total_time / len(times)
            
            # 风险评估（基于时间间隔）
            if avg_interval < 1.0:
                risk_level = "🟠 中"
            elif avg_interval < 2.0:
                risk_level = "🟡 低"
            else:
                risk_level = "🟢 极低"
                
        print(f"{mode_name:12s} {total_time:6.2f}s {avg_interval:8.2f}s {risk_level:>10s}")


def demo_statistics_monitoring():
    """演示统计监控功能"""
    print("\n" + "=" * 60)
    print("📈 统计监控功能演示")
    print("=" * 60)
    
    simulator = HumanBehaviorSimulator({"enabled": True})
    
    # 模拟一系列操作
    print("🎯 模拟执行操作序列...")
    operations = [
        ("navigate", True, 1.2),
        ("click", True, 0.3),
        ("fill", True, 2.1),
        ("click", False, 0.5),  # 失败的操作
        ("scroll", True, 0.4),
        ("click", True, 0.3),
    ]
    
    for action_type, success, exec_time in operations:
        simulator.record_action(action_type, success, exec_time)
        print(f"   ✅ {action_type:8s} ({'成功' if success else '失败':2s}) - {exec_time:.1f}s")
        
    # 获取并显示统计信息
    stats = simulator.get_stats()
    
    print("\n📊 操作统计报告:")
    print(f"   总操作数: {stats['total_actions']}")
    print(f"   成功率: {stats['success_rate']:.1%}")
    print(f"   平均间隔: {stats['average_interval']:.2f}s")
    print(f"   行为模式: {stats['behavior_mode']}")
    print(f"   模拟状态: {'启用' if stats['enabled'] else '禁用'}")


def main():
    """主演示函数"""
    print("🤖 AI浏览器智能体 - 人类行为模拟功能演示")
    print("🎭 模拟真实用户行为，规避反爬虫检测机制")
    print()
    
    try:
        # 运行各个演示
        demo_behavior_modes()
        demo_typing_simulation()
        demo_adaptive_timing()
        demo_mouse_movement()
        demo_anti_bot_features()
        demo_practical_scenario()
        demo_configuration_comparison()
        demo_statistics_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成!")
        print("📚 要了解更多配置选项，请查看:")
        print("   - src/action/human_behavior_simulator.py")
        print("   - src/common/config.py")
        print("   - tests/unit/test_human_behavior_simulator.py")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    main()