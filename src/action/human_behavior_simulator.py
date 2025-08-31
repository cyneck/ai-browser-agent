#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人类行为模拟器

模拟真实用户的行为模式，包括时间延迟、鼠标移动、打字速度等，
避免触发网站的反爬虫机制和人机验证。
"""

import random
import time
import math
from typing import Dict, Any, List, Optional, Tuple
from playwright.sync_api import Page
from src.common.logger import get_logger


class HumanBehaviorSimulator:
    """人类行为模拟器类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化人类行为模拟器
        
        Args:
            config: 配置参数字典
        """
        self.logger = get_logger()
        self.config = config or {}
        
        # 默认配置
        self.default_config = {
            # 基础延迟设置 (秒)
            "base_delay_min": 0.3,
            "base_delay_max": 1.2,
            
            # 操作间隔设置 (秒)
            "action_interval_min": 0.5,
            "action_interval_max": 3.0,
            
            # 打字速度设置 (字符/秒)
            "typing_speed_min": 3,
            "typing_speed_max": 8,
            
            # 鼠标移动设置
            "mouse_move_enabled": True,
            "mouse_move_steps": 20,
            "mouse_move_duration": 0.8,
            
            # 随机暂停设置
            "random_pause_probability": 0.15,
            "random_pause_min": 2.0,
            "random_pause_max": 8.0,
            
            # 页面等待设置
            "page_load_wait_min": 1.0,
            "page_load_wait_max": 3.5,
            
            # 模式设置
            "behavior_mode": "moderate",  # conservative, moderate, aggressive
            
            # 启用/禁用功能
            "enabled": True,
            "adaptive_timing": True,
            "jitter_enabled": True,
        }
        
        # 合并配置
        self.effective_config = {**self.default_config, **self.config}
        
        # 行为历史记录，用于自适应调整
        self.action_history: List[Dict[str, Any]] = []
        self.last_action_time = 0
        
        # 模式特定配置 - 在合并配置后应用
        self._apply_behavior_mode()
        
    def _apply_behavior_mode(self):
        """根据行为模式调整配置参数"""
        mode = self.effective_config["behavior_mode"]
        
        if mode == "conservative":
            # 保守模式：更长的延迟，更谨慎
            self.effective_config.update({
                "base_delay_min": 0.8,
                "base_delay_max": 2.5,
                "action_interval_min": 1.5,
                "action_interval_max": 5.0,
                "random_pause_probability": 0.25,
                "random_pause_min": 3.0,
                "random_pause_max": 12.0,
            })
        elif mode == "aggressive":
            # 激进模式：较短的延迟，更快速
            self.effective_config.update({
                "base_delay_min": 0.1,
                "base_delay_max": 0.6,
                "action_interval_min": 0.2,
                "action_interval_max": 1.5,
                "random_pause_probability": 0.08,
                "random_pause_min": 1.0,
                "random_pause_max": 4.0,
            })
        # moderate 模式使用默认配置
        
        # 如果用户明确设置了某些值，保持用户的设置
        for key, value in self.config.items():
            if key in ["base_delay_min", "base_delay_max", "action_interval_min", 
                      "action_interval_max", "random_pause_probability", 
                      "random_pause_min", "random_pause_max"]:
                self.effective_config[key] = value
        
    def is_enabled(self) -> bool:
        """检查行为模拟是否启用"""
        return self.effective_config["enabled"]
        
    def get_base_delay(self) -> float:
        """获取基础延迟时间"""
        if not self.is_enabled():
            return 0.0
            
        min_delay = self.effective_config["base_delay_min"]
        max_delay = self.effective_config["base_delay_max"]
        delay = random.uniform(min_delay, max_delay)
        
        # 添加抖动
        if self.effective_config["jitter_enabled"]:
            jitter = random.uniform(-0.1, 0.1)
            delay = max(0.1, delay + jitter)
            
        return delay
        
    def get_action_interval(self, action_type: str) -> float:
        """
        获取操作间隔时间
        
        Args:
            action_type: 操作类型
            
        Returns:
            float: 间隔时间（秒）
        """
        if not self.is_enabled():
            return 0.0
            
        base_min = self.effective_config["action_interval_min"]
        base_max = self.effective_config["action_interval_max"]
        
        # 根据操作类型调整
        type_multipliers = {
            "navigate": 1.5,  # 导航需要更长等待
            "click": 1.0,
            "fill": 1.2,      # 输入稍微慢一点
            "scroll": 0.8,    # 滚动可以快一点
            "wait": 0.5,
        }
        
        multiplier = type_multipliers.get(action_type, 1.0)
        interval = random.uniform(base_min * multiplier, base_max * multiplier)
        
        # 自适应调整
        if self.effective_config["adaptive_timing"]:
            interval = self._apply_adaptive_timing(interval, action_type)
            
        return interval
        
    def _apply_adaptive_timing(self, base_interval: float, action_type: str) -> float:
        """根据历史记录自适应调整时间"""
        if len(self.action_history) < 3:
            return base_interval
            
        # 计算最近操作的频率
        recent_actions = self.action_history[-5:]
        if len(recent_actions) >= 2:
            time_diffs = []
            for i in range(1, len(recent_actions)):
                diff = recent_actions[i]["timestamp"] - recent_actions[i-1]["timestamp"]
                time_diffs.append(diff)
                
            avg_interval = sum(time_diffs) / len(time_diffs)
            
            # 如果最近操作太频繁，增加延迟
            if avg_interval < 2.0:
                base_interval *= 1.3
            elif avg_interval > 8.0:
                base_interval *= 0.8
                
        return base_interval
        
    def should_add_random_pause(self) -> bool:
        """判断是否应该添加随机暂停"""
        if not self.is_enabled():
            return False
            
        probability = self.effective_config["random_pause_probability"]
        return random.random() < probability
        
    def get_random_pause_duration(self) -> float:
        """获取随机暂停时长"""
        min_pause = self.effective_config["random_pause_min"]
        max_pause = self.effective_config["random_pause_max"]
        return random.uniform(min_pause, max_pause)
        
    def get_typing_delay(self, text: str) -> List[float]:
        """
        生成打字延迟序列
        
        Args:
            text: 要输入的文本
            
        Returns:
            List[float]: 每个字符的延迟时间
        """
        if not self.is_enabled():
            return [0.0] * len(text)
            
        min_speed = self.effective_config["typing_speed_min"]
        max_speed = self.effective_config["typing_speed_max"]
        
        delays = []
        for i, char in enumerate(text):
            # 基础延迟
            base_delay = 1.0 / random.uniform(min_speed, max_speed)
            
            # 特殊字符延迟调整
            if char in ".,!?;:":
                base_delay *= 1.5  # 标点符号稍慢
            elif char == " ":
                base_delay *= 1.2  # 空格稍慢
            elif char.isupper():
                base_delay *= 1.1  # 大写字母稍慢
                
            # 添加自然的变化
            variation = random.uniform(0.7, 1.4)
            final_delay = base_delay * variation
            
            delays.append(max(0.05, final_delay))
            
        return delays
        
    def simulate_mouse_movement(self, page: Page, start_pos: Tuple[int, int], 
                              end_pos: Tuple[int, int]) -> None:
        """
        模拟自然的鼠标移动
        
        Args:
            page: Playwright页面对象
            start_pos: 起始位置 (x, y)
            end_pos: 目标位置 (x, y)
        """
        if not self.is_enabled() or not self.effective_config["mouse_move_enabled"]:
            return
            
        steps = self.effective_config["mouse_move_steps"]
        duration = self.effective_config["mouse_move_duration"]
        
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # 生成贝塞尔曲线路径
        control1_x = start_x + (end_x - start_x) * 0.25 + random.randint(-50, 50)
        control1_y = start_y + (end_y - start_y) * 0.25 + random.randint(-50, 50)
        control2_x = start_x + (end_x - start_x) * 0.75 + random.randint(-50, 50)
        control2_y = start_y + (end_y - start_y) * 0.75 + random.randint(-50, 50)
        
        for i in range(steps + 1):
            t = i / steps
            
            # 贝塞尔曲线插值
            x = (1-t)**3 * start_x + 3*(1-t)**2*t * control1_x + \
                3*(1-t)*t**2 * control2_x + t**3 * end_x
            y = (1-t)**3 * start_y + 3*(1-t)**2*t * control1_y + \
                3*(1-t)*t**2 * control2_y + t**3 * end_y
                
            try:
                page.mouse.move(x, y)
                if i < steps:
                    time.sleep(duration / steps)
            except Exception as e:
                self.logger.debug(f"鼠标移动模拟失败: {e}")
                break
                
    def wait_before_action(self, action_type: str) -> None:
        """
        在执行操作前等待
        
        Args:
            action_type: 操作类型
        """
        if not self.is_enabled():
            return
            
        # 检查是否需要随机暂停
        if self.should_add_random_pause():
            pause_duration = self.get_random_pause_duration()
            self.logger.debug(f"执行随机暂停: {pause_duration:.2f}秒")
            time.sleep(pause_duration)
            
        # 获取操作间隔
        interval = self.get_action_interval(action_type)
        
        # 计算距离上次操作的时间
        current_time = time.time()
        if self.last_action_time > 0:
            elapsed = current_time - self.last_action_time
            remaining = interval - elapsed
            
            if remaining > 0:
                self.logger.debug(f"等待操作间隔: {remaining:.2f}秒")
                time.sleep(remaining)
                
        # 添加基础延迟
        base_delay = self.get_base_delay()
        if base_delay > 0:
            self.logger.debug(f"基础延迟: {base_delay:.2f}秒")
            time.sleep(base_delay)
            
    def record_action(self, action_type: str, success: bool, 
                     execution_time: float) -> None:
        """
        记录操作历史
        
        Args:
            action_type: 操作类型
            success: 是否成功
            execution_time: 执行时间
        """
        current_time = time.time()
        
        action_record = {
            "action_type": action_type,
            "timestamp": current_time,
            "success": success,
            "execution_time": execution_time,
        }
        
        self.action_history.append(action_record)
        self.last_action_time = current_time
        
        # 保持历史记录在合理范围内
        if len(self.action_history) > 50:
            self.action_history = self.action_history[-30:]
            
    def get_page_load_wait_time(self) -> float:
        """获取页面加载等待时间"""
        if not self.is_enabled():
            return 0.0
            
        min_wait = self.effective_config["page_load_wait_min"]
        max_wait = self.effective_config["page_load_wait_max"]
        return random.uniform(min_wait, max_wait)
        
    def simulate_human_typing(self, page: Page, selector: str, text: str) -> None:
        """
        模拟人类打字行为
        
        Args:
            page: Playwright页面对象
            selector: 元素选择器
            text: 要输入的文本
        """
        if not self.is_enabled():
            page.locator(selector).fill(text)
            return
            
        element = page.locator(selector)
        
        # 先清空输入框
        element.click()
        element.clear()
        
        # 获取打字延迟序列
        delays = self.get_typing_delay(text)
        
        # 逐字符输入
        for i, char in enumerate(text):
            element.type(char)
            
            if i < len(delays):
                time.sleep(delays[i])
                
        self.logger.debug(f"完成人类打字模拟，输入文本长度: {len(text)}")
        
    def get_stats(self) -> Dict[str, Any]:
        """获取行为模拟统计信息"""
        if not self.action_history:
            return {"total_actions": 0}
            
        total_actions = len(self.action_history)
        successful_actions = sum(1 for a in self.action_history if a["success"])
        success_rate = successful_actions / total_actions if total_actions > 0 else 0
        
        if len(self.action_history) >= 2:
            time_diffs = []
            for i in range(1, len(self.action_history)):
                diff = self.action_history[i]["timestamp"] - self.action_history[i-1]["timestamp"]
                time_diffs.append(diff)
                
            avg_interval = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        else:
            avg_interval = 0
            
        return {
            "total_actions": total_actions,
            "success_rate": success_rate,
            "average_interval": avg_interval,
            "behavior_mode": self.effective_config["behavior_mode"],
            "enabled": self.effective_config["enabled"],
        }