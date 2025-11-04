#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人类行为模拟器增强功能演示

展示新增的反检测机制、高级鼠标移动、打字错误模拟等功能
"""

import sys
import os
import time
from unittest.mock import Mock

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.action.human_behavior_simulator import HumanBehaviorSimulator


def demo_enhanced_mouse_movement():
    """演示增强的鼠标移动功能"""
    print("\n=== 增强鼠标移动演示 ===")
    
    config = {
        "enabled": True,
        "behavior_mode": "moderate",
        "mouse_move_enabled": True,
        "mouse_overshoot_probability": 0.3,
        "mouse_correction_probability": 0.2,
        "micro_movements_enabled": True,
    }
    
    simulator = HumanBehaviorSimulator(config)
    mock_page = Mock()
    mock_page.mouse = Mock()
    
    print("1. 短距离移动（直接移动）:")
    start_time = time.time()
    simulator.simulate_mouse_movement(mock_page, (100, 100), (105, 105))
    print(f"   移动完成，耗时: {time.time() - start_time:.3f}秒")
    print(f"   鼠标移动调用次数: {mock_page.mouse.move.call_count}")
    
    print("\n2. 长距离移动（贝塞尔曲线 + 可能过冲）:")
    mock_page.mouse.reset_mock()
    start_time = time.time()
    simulator.simulate_mouse_movement(mock_page, (100, 100), (500, 400))
    print(f"   移动完成，耗时: {time.time() - start_time:.3f}秒")
    print(f"   鼠标移动调用次数: {mock_page.mouse.move.call_count}")
    
    print("\n3. 微移动演示:")
    mock_page.mouse.reset_mock()
    start_time = time.time()
    simulator.simulate_micro_movements(mock_page)
    print(f"   微移动完成，耗时: {time.time() - start_time:.3f}秒")
    print(f"   鼠标移动调用次数: {mock_page.mouse.move.call_count}")


def demo_enhanced_typing():
    """演示增强的打字功能"""
    print("\n=== 增强打字功能演示 ===")
    
    config = {
        "enabled": True,
        "behavior_mode": "moderate",
        "typing_mistakes_probability": 0.2,
        "backspace_correction_probability": 0.8,
        "focus_behavior_simulation": True,
    }
    
    simulator = HumanBehaviorSimulator(config)
    mock_page = Mock()
    mock_element = Mock()
    mock_page.locator.return_value = mock_element
    
    test_texts = [
        "hello world",
        "The quick brown fox jumps over the lazy dog",
        "user@example.com",
        "Password123!"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. 输入文本: '{text}'")
        mock_element.reset_mock()
        
        start_time = time.time()
        simulator.simulate_human_typing(mock_page, "#input", text)
        duration = time.time() - start_time
        
        print(f"   输入完成，耗时: {duration:.3f}秒")
        print(f"   点击调用: {mock_element.click.call_count}")
        print(f"   清空调用: {mock_element.clear.call_count}")
        print(f"   输入调用: {mock_element.type.call_count}")
        print(f"   按键调用: {mock_element.press.call_count}")
        
        # 计算平均打字速度
        if duration > 0:
            speed = len(text) / duration
            print(f"   平均速度: {speed:.1f} 字符/秒")


def demo_scroll_with_momentum():
    """演示带惯性的滚动功能"""
    print("\n=== 惯性滚动演示 ===")
    
    config = {
        "enabled": True,
        "scroll_momentum_simulation": True,
    }
    
    simulator = HumanBehaviorSimulator(config)
    mock_page = Mock()
    
    directions = ["down", "up", "right", "left"]
    distances = [300, 500, 200, 800]
    
    for direction, distance in zip(directions, distances):
        print(f"\n滚动方向: {direction}, 距离: {distance}px")
        mock_page.reset_mock()
        
        start_time = time.time()
        simulator.simulate_scroll_with_momentum(mock_page, direction, distance)
        duration = time.time() - start_time
        
        print(f"   滚动完成，耗时: {duration:.3f}秒")
        print(f"   页面评估调用次数: {mock_page.evaluate.call_count}")


def demo_anti_detection_measures():
    """演示反检测措施"""
    print("\n=== 反检测措施演示 ===")
    
    config = {
        "enabled": True,
        "anti_detection_enabled": True,
        "viewport_randomization": True,
        "request_timing_randomization": True,
    }
    
    simulator = HumanBehaviorSimulator(config)
    mock_page = Mock()
    mock_page.set_viewport_size = Mock()
    mock_page.evaluate = Mock()
    mock_page.mouse = Mock()
    
    print("1. 应用反检测措施:")
    start_time = time.time()
    simulator.apply_anti_detection_measures(mock_page)
    duration = time.time() - start_time
    
    print(f"   反检测措施应用完成，耗时: {duration:.3f}秒")
    
    print("\n2. 视口随机化:")
    mock_page.reset_mock()
    simulator._randomize_viewport(mock_page)
    
    if mock_page.set_viewport_size.called:
        call_args = mock_page.set_viewport_size.call_args[0][0]
        print(f"   新视口大小: {call_args['width']}x{call_args['height']}")
    
    print("\n3. 浏览模式模拟:")
    mock_page.reset_mock()
    for i in range(5):
        simulator._simulate_browsing_patterns(mock_page)
    
    print(f"   执行了5次浏览模式模拟")
    print(f"   页面评估调用: {mock_page.evaluate.call_count}")
    print(f"   鼠标移动调用: {mock_page.mouse.move.call_count}")


def demo_behavior_adjustment():
    """演示行为调整功能"""
    print("\n=== 行为调整演示 ===")
    
    simulator = HumanBehaviorSimulator({"enabled": True, "behavior_mode": "moderate"})
    
    print("初始配置:")
    print(f"   行为模式: {simulator.effective_config['behavior_mode']}")
    print(f"   基础延迟: {simulator.effective_config['base_delay_min']}-{simulator.effective_config['base_delay_max']}秒")
    print(f"   随机暂停概率: {simulator.effective_config['random_pause_probability']}")
    
    detection_levels = ["low", "medium", "high"]
    
    for level in detection_levels:
        print(f"\n检测级别调整为: {level}")
        simulator.adjust_behavior_based_on_detection(level)
        
        print(f"   行为模式: {simulator.effective_config['behavior_mode']}")
        print(f"   基础延迟: {simulator.effective_config['base_delay_min']}-{simulator.effective_config['base_delay_max']}秒")
        print(f"   随机暂停概率: {simulator.effective_config['random_pause_probability']}")


def demo_enhanced_statistics():
    """演示增强统计功能"""
    print("\n=== 增强统计信息演示 ===")
    
    config = {
        "enabled": True,
        "anti_detection_enabled": True,
        "micro_movements_enabled": True,
        "typing_mistakes_probability": 0.1,
        "scroll_momentum_simulation": True,
        "focus_behavior_simulation": True,
    }
    
    simulator = HumanBehaviorSimulator(config)
    
    # 模拟一些操作历史
    actions = [
        ("navigate", True, 2.1),
        ("click", True, 0.5),
        ("fill", True, 3.2),
        ("scroll", True, 1.1),
        ("click", False, 0.8),  # 失败的操作
        ("extract", True, 1.5),
        ("fill", True, 2.8),
        ("click", True, 0.6),
    ]
    
    print("模拟操作历史:")
    for action_type, success, duration in actions:
        simulator.record_action(action_type, success, duration)
        print(f"   {action_type}: {'成功' if success else '失败'} ({duration}秒)")
    
    print("\n增强统计信息:")
    stats = simulator.get_enhanced_stats()
    
    print(f"   总操作数: {stats['total_actions']}")
    print(f"   成功率: {stats['success_rate']:.1%}")
    print(f"   平均间隔: {stats['average_interval']:.2f}秒")
    print(f"   最近错误率: {stats['recent_error_rate']:.1%}")
    print(f"   反检测启用: {stats['anti_detection_enabled']}")
    
    print("\n操作类型分布:")
    for action_type, count in stats['action_type_distribution'].items():
        print(f"   {action_type}: {count}次")
    
    print("\n高级功能状态:")
    advanced = stats['advanced_features_enabled']
    for feature, enabled in advanced.items():
        print(f"   {feature}: {'启用' if enabled else '禁用'}")


def main():
    """主演示函数"""
    print("人类行为模拟器增强功能演示")
    print("=" * 50)
    
    try:
        demo_enhanced_mouse_movement()
        demo_enhanced_typing()
        demo_scroll_with_momentum()
        demo_anti_detection_measures()
        demo_behavior_adjustment()
        demo_enhanced_statistics()
        
        print("\n" + "=" * 50)
        print("所有演示完成！")
        print("\n主要增强功能:")
        print("✅ 更自然的鼠标移动轨迹（贝塞尔曲线 + 过冲修正）")
        print("✅ 智能打字错误和修正模拟")
        print("✅ 带惯性的滚动行为")
        print("✅ 反检测机制（视口随机化、浏览模式模拟）")
        print("✅ 自适应行为调整")
        print("✅ 增强的统计和监控")
        print("✅ 微移动和焦点行为模拟")
        
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()