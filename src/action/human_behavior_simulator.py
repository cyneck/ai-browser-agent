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
import numpy as np
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
            "mouse_curve_intensity": 0.3,  # 曲线强度
            "mouse_overshoot_probability": 0.1,  # 过冲概率
            "mouse_correction_probability": 0.05,  # 修正概率
            
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
            
            # 反检测机制
            "anti_detection_enabled": True,
            "viewport_randomization": True,
            "user_agent_rotation": False,  # 需要外部支持
            "request_timing_randomization": True,
            
            # 高级行为模拟
            "micro_movements_enabled": True,  # 微小移动
            "typing_mistakes_probability": 0.02,  # 打字错误概率
            "backspace_correction_probability": 0.8,  # 退格修正概率
            "scroll_momentum_simulation": True,  # 滚动惯性模拟
            "focus_behavior_simulation": True,  # 焦点行为模拟
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
        模拟自然的鼠标移动，包括过冲、修正和微调
        
        Args:
            page: Playwright页面对象
            start_pos: 起始位置 (x, y)
            end_pos: 目标位置 (x, y)
        """
        if not self.is_enabled() or not self.effective_config["mouse_move_enabled"]:
            return
            
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # 计算距离，根据距离调整行为
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        if distance < 10:
            # 短距离直接移动
            self._direct_mouse_move(page, start_pos, end_pos)
        else:
            # 长距离使用复杂轨迹
            self._complex_mouse_movement(page, start_pos, end_pos, distance)
            
    def _direct_mouse_move(self, page: Page, start_pos: Tuple[int, int], 
                          end_pos: Tuple[int, int]) -> None:
        """直接鼠标移动，用于短距离"""
        try:
            page.mouse.move(end_pos[0], end_pos[1])
            # 短暂延迟
            time.sleep(random.uniform(0.01, 0.05))
        except Exception as e:
            self.logger.debug(f"直接鼠标移动失败: {e}")
            
    def _complex_mouse_movement(self, page: Page, start_pos: Tuple[int, int], 
                               end_pos: Tuple[int, int], distance: float) -> None:
        """复杂鼠标移动，包括曲线、过冲和修正"""
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # 根据距离调整参数
        steps = max(10, min(50, int(distance / 10)))
        duration = self.effective_config["mouse_move_duration"]
        curve_intensity = self.effective_config["mouse_curve_intensity"]
        
        # 生成更自然的贝塞尔曲线控制点
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # 添加垂直于移动方向的偏移
        dx = end_x - start_x
        dy = end_y - start_y
        
        # 计算垂直向量
        if abs(dx) > abs(dy):
            offset_x = 0
            offset_y = random.uniform(-distance * curve_intensity, distance * curve_intensity)
        else:
            offset_x = random.uniform(-distance * curve_intensity, distance * curve_intensity)
            offset_y = 0
            
        control1_x = start_x + dx * 0.25 + offset_x * 0.5
        control1_y = start_y + dy * 0.25 + offset_y * 0.5
        control2_x = start_x + dx * 0.75 + offset_x * 0.5
        control2_y = start_y + dy * 0.75 + offset_y * 0.5
        
        # 主要移动路径
        path_points = []
        for i in range(steps + 1):
            t = i / steps
            
            # 使用缓动函数使移动更自然
            eased_t = self._ease_in_out_cubic(t)
            
            # 贝塞尔曲线插值
            x = (1-eased_t)**3 * start_x + 3*(1-eased_t)**2*eased_t * control1_x + \
                3*(1-eased_t)*eased_t**2 * control2_x + eased_t**3 * end_x
            y = (1-eased_t)**3 * start_y + 3*(1-eased_t)**2*eased_t * control1_y + \
                3*(1-eased_t)*eased_t**2 * control2_y + eased_t**3 * end_y
                
            # 添加微小的随机抖动
            if self.effective_config["jitter_enabled"]:
                x += random.uniform(-1, 1)
                y += random.uniform(-1, 1)
                
            path_points.append((int(x), int(y)))
            
        # 执行移动
        try:
            for i, (x, y) in enumerate(path_points):
                page.mouse.move(x, y)
                
                if i < len(path_points) - 1:
                    # 变化的延迟时间，开始快，中间慢，结束快
                    progress = i / (len(path_points) - 1)
                    delay_multiplier = 1 + 0.5 * math.sin(progress * math.pi)
                    delay = (duration / steps) * delay_multiplier
                    time.sleep(delay)
                    
            # 可能的过冲和修正
            if random.random() < self.effective_config["mouse_overshoot_probability"]:
                self._simulate_overshoot_correction(page, end_pos)
                
        except Exception as e:
            self.logger.debug(f"复杂鼠标移动失败: {e}")
            
    def _ease_in_out_cubic(self, t: float) -> float:
        """三次缓动函数，使移动更自然"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
            
    def _simulate_overshoot_correction(self, page: Page, target_pos: Tuple[int, int]) -> None:
        """模拟鼠标过冲和修正"""
        target_x, target_y = target_pos
        
        # 过冲距离
        overshoot_distance = random.uniform(5, 20)
        overshoot_angle = random.uniform(0, 2 * math.pi)
        
        overshoot_x = target_x + overshoot_distance * math.cos(overshoot_angle)
        overshoot_y = target_y + overshoot_distance * math.sin(overshoot_angle)
        
        try:
            # 过冲
            page.mouse.move(int(overshoot_x), int(overshoot_y))
            time.sleep(random.uniform(0.05, 0.15))
            
            # 修正回目标位置
            page.mouse.move(target_x, target_y)
            time.sleep(random.uniform(0.02, 0.08))
            
        except Exception as e:
            self.logger.debug(f"过冲修正模拟失败: {e}")
            
    def simulate_micro_movements(self, page: Page) -> None:
        """模拟微小的鼠标移动，增加真实感"""
        if not self.effective_config["micro_movements_enabled"]:
            return
            
        try:
            # 获取当前鼠标位置（如果可能）
            # 由于Playwright限制，我们模拟小范围随机移动
            for _ in range(random.randint(1, 3)):
                offset_x = random.uniform(-3, 3)
                offset_y = random.uniform(-3, 3)
                
                # 相对移动
                page.mouse.move(offset_x, offset_y)
                time.sleep(random.uniform(0.1, 0.3))
                
        except Exception as e:
            self.logger.debug(f"微移动模拟失败: {e}")
                
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
        模拟人类打字行为，包括错误和修正
        
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
        time.sleep(random.uniform(0.1, 0.3))  # 点击后短暂延迟
        element.clear()
        
        # 模拟焦点行为
        if self.effective_config["focus_behavior_simulation"]:
            self._simulate_focus_behavior(page, element)
        
        # 获取打字延迟序列
        delays = self.get_typing_delay(text)
        
        # 逐字符输入，包含错误模拟
        typed_text = ""
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # 决定是否制造打字错误
            if (random.random() < self.effective_config["typing_mistakes_probability"] and 
                len(typed_text) > 2 and i < len(text) - 1):
                
                # 制造错误
                wrong_char = self._get_nearby_key(char)
                element.type(wrong_char)
                typed_text += wrong_char
                time.sleep(delays[i] if i < len(delays) else 0.1)
                
                # 决定是否立即修正
                if random.random() < self.effective_config["backspace_correction_probability"]:
                    # 短暂停顿，然后退格修正
                    time.sleep(random.uniform(0.2, 0.8))
                    element.press("Backspace")
                    typed_text = typed_text[:-1]
                    time.sleep(random.uniform(0.1, 0.3))
                    
                    # 输入正确字符
                    element.type(char)
                    typed_text += char
                else:
                    # 继续输入几个字符后再修正
                    chars_before_correction = random.randint(1, 3)
                    for j in range(min(chars_before_correction, len(text) - i - 1)):
                        next_char = text[i + 1 + j]
                        element.type(next_char)
                        typed_text += next_char
                        time.sleep(delays[i + 1 + j] if i + 1 + j < len(delays) else 0.1)
                    
                    # 现在修正错误
                    backspace_count = chars_before_correction + 1
                    time.sleep(random.uniform(0.3, 1.0))  # 发现错误的延迟
                    
                    for _ in range(backspace_count):
                        element.press("Backspace")
                        typed_text = typed_text[:-1]
                        time.sleep(random.uniform(0.05, 0.15))
                    
                    # 重新输入正确的字符序列
                    for j in range(backspace_count):
                        correct_char = text[i + j]
                        element.type(correct_char)
                        typed_text += correct_char
                        time.sleep(delays[i + j] if i + j < len(delays) else 0.1)
                    
                    i += chars_before_correction
            else:
                # 正常输入
                element.type(char)
                typed_text += char
                
                if i < len(delays):
                    time.sleep(delays[i])
            
            i += 1
            
        self.logger.debug(f"完成人类打字模拟，输入文本长度: {len(text)}")
        
    def _simulate_focus_behavior(self, page: Page, element) -> None:
        """模拟获得焦点时的行为"""
        try:
            # 模拟点击获得焦点后的短暂停顿
            time.sleep(random.uniform(0.05, 0.2))
            
            # 可能的微小移动
            if random.random() < 0.3:
                self.simulate_micro_movements(page)
                
        except Exception as e:
            self.logger.debug(f"焦点行为模拟失败: {e}")
            
    def _get_nearby_key(self, char: str) -> str:
        """获取键盘上相邻的键，用于模拟打字错误"""
        # 简化的键盘布局映射
        keyboard_layout = {
            'q': ['w', 'a', 's'], 'w': ['q', 'e', 's', 'd'], 'e': ['w', 'r', 'd', 'f'],
            'r': ['e', 't', 'f', 'g'], 't': ['r', 'y', 'g', 'h'], 'y': ['t', 'u', 'h', 'j'],
            'u': ['y', 'i', 'j', 'k'], 'i': ['u', 'o', 'k', 'l'], 'o': ['i', 'p', 'l'],
            'p': ['o', 'l'],
            'a': ['q', 's', 'z'], 's': ['a', 'w', 'd', 'z', 'x'], 'd': ['s', 'e', 'f', 'x', 'c'],
            'f': ['d', 'r', 'g', 'c', 'v'], 'g': ['f', 't', 'h', 'v', 'b'], 'h': ['g', 'y', 'j', 'b', 'n'],
            'j': ['h', 'u', 'k', 'n', 'm'], 'k': ['j', 'i', 'l', 'm'], 'l': ['k', 'o', 'p'],
            'z': ['a', 's', 'x'], 'x': ['z', 's', 'd', 'c'], 'c': ['x', 'd', 'f', 'v'],
            'v': ['c', 'f', 'g', 'b'], 'b': ['v', 'g', 'h', 'n'], 'n': ['b', 'h', 'j', 'm'],
            'm': ['n', 'j', 'k'],
        }
        
        char_lower = char.lower()
        if char_lower in keyboard_layout:
            nearby_keys = keyboard_layout[char_lower]
            wrong_char = random.choice(nearby_keys)
            # 保持原始字符的大小写
            return wrong_char.upper() if char.isupper() else wrong_char
        else:
            # 如果不在映射中，返回一个随机的相似字符
            similar_chars = ['a', 'e', 'i', 'o', 'u'] if char.lower() in 'aeiou' else ['b', 'c', 'd', 'f', 'g']
            return random.choice(similar_chars)
        
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
        
    def simulate_scroll_with_momentum(self, page: Page, direction: str = "down", 
                                    distance: int = 300) -> None:
        """
        模拟带惯性的滚动行为
        
        Args:
            page: Playwright页面对象
            direction: 滚动方向 ("up", "down", "left", "right")
            distance: 滚动距离
        """
        if not self.effective_config["scroll_momentum_simulation"]:
            # 简单滚动
            if direction == "down":
                page.evaluate(f"window.scrollBy(0, {distance})")
            elif direction == "up":
                page.evaluate(f"window.scrollBy(0, -{distance})")
            elif direction == "right":
                page.evaluate(f"window.scrollBy({distance}, 0)")
            elif direction == "left":
                page.evaluate(f"window.scrollBy(-{distance}, 0)")
            return
            
        # 模拟惯性滚动
        steps = random.randint(8, 15)
        total_duration = random.uniform(0.8, 1.5)
        
        # 计算每步的滚动距离（开始快，逐渐减慢）
        scroll_distances = []
        remaining_distance = distance
        
        for i in range(steps):
            # 使用指数衰减
            progress = i / (steps - 1)
            decay_factor = math.exp(-3 * progress)  # 指数衰减
            
            if i == steps - 1:
                # 最后一步滚动剩余距离
                step_distance = remaining_distance
            else:
                step_distance = int(distance * decay_factor / sum(math.exp(-3 * j / (steps - 1)) for j in range(steps)))
                step_distance = min(step_distance, remaining_distance)
                
            scroll_distances.append(step_distance)
            remaining_distance -= step_distance
            
        # 执行分步滚动
        try:
            for i, step_distance in enumerate(scroll_distances):
                if step_distance <= 0:
                    continue
                    
                if direction == "down":
                    page.evaluate(f"window.scrollBy(0, {step_distance})")
                elif direction == "up":
                    page.evaluate(f"window.scrollBy(0, -{step_distance})")
                elif direction == "right":
                    page.evaluate(f"window.scrollBy({step_distance}, 0)")
                elif direction == "left":
                    page.evaluate(f"window.scrollBy(-{step_distance}, 0)")
                    
                # 变化的延迟时间
                delay = (total_duration / steps) * (1 + 0.5 * math.sin(i * math.pi / steps))
                time.sleep(delay)
                
        except Exception as e:
            self.logger.debug(f"惯性滚动模拟失败: {e}")
            
    def apply_anti_detection_measures(self, page: Page) -> None:
        """
        应用反检测措施
        
        Args:
            page: Playwright页面对象
        """
        if not self.effective_config["anti_detection_enabled"]:
            return
            
        try:
            # 随机化视口大小
            if self.effective_config["viewport_randomization"]:
                self._randomize_viewport(page)
                
            # 随机化请求时间
            if self.effective_config["request_timing_randomization"]:
                self._add_request_timing_variation()
                
            # 模拟人类浏览行为
            self._simulate_browsing_patterns(page)
            
        except Exception as e:
            self.logger.debug(f"反检测措施应用失败: {e}")
            
    def _randomize_viewport(self, page: Page) -> None:
        """随机化视口大小"""
        try:
            # 常见的屏幕分辨率
            common_resolutions = [
                (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
                (1280, 720), (1600, 900), (1024, 768), (1280, 1024)
            ]
            
            base_width, base_height = random.choice(common_resolutions)
            
            # 添加小的随机变化
            width = base_width + random.randint(-50, 50)
            height = base_height + random.randint(-50, 50)
            
            page.set_viewport_size({"width": width, "height": height})
            self.logger.debug(f"视口大小随机化为: {width}x{height}")
            
        except Exception as e:
            self.logger.debug(f"视口随机化失败: {e}")
            
    def _add_request_timing_variation(self) -> None:
        """添加请求时间变化"""
        # 在请求之间添加随机延迟
        variation = random.uniform(0.1, 0.8)
        time.sleep(variation)
        
    def _simulate_browsing_patterns(self, page: Page) -> None:
        """模拟人类浏览模式"""
        try:
            # 随机滚动一小段距离
            if random.random() < 0.3:
                scroll_distance = random.randint(50, 200)
                self.simulate_scroll_with_momentum(page, "down", scroll_distance)
                
            # 随机微移动鼠标
            if random.random() < 0.4:
                self.simulate_micro_movements(page)
                
            # 模拟阅读停顿
            if random.random() < 0.2:
                reading_pause = random.uniform(1.0, 3.0)
                time.sleep(reading_pause)
                
        except Exception as e:
            self.logger.debug(f"浏览模式模拟失败: {e}")
            
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """获取增强的统计信息"""
        basic_stats = self.get_stats()
        
        # 添加更多统计信息
        if self.action_history:
            action_types = [action["action_type"] for action in self.action_history]
            action_type_counts = {}
            for action_type in action_types:
                action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
                
            # 计算最近的错误率
            recent_actions = self.action_history[-10:]
            recent_errors = sum(1 for action in recent_actions if not action["success"])
            recent_error_rate = recent_errors / len(recent_actions) if recent_actions else 0
            
            basic_stats.update({
                "action_type_distribution": action_type_counts,
                "recent_error_rate": recent_error_rate,
                "anti_detection_enabled": self.effective_config["anti_detection_enabled"],
                "advanced_features_enabled": {
                    "micro_movements": self.effective_config["micro_movements_enabled"],
                    "typing_mistakes": self.effective_config["typing_mistakes_probability"] > 0,
                    "scroll_momentum": self.effective_config["scroll_momentum_simulation"],
                    "focus_behavior": self.effective_config["focus_behavior_simulation"],
                }
            })
            
        return basic_stats
        
    def adjust_behavior_based_on_detection(self, detection_level: str) -> None:
        """
        根据检测级别调整行为
        
        Args:
            detection_level: 检测级别 ("low", "medium", "high")
        """
        if detection_level == "high":
            # 高检测风险，切换到最保守模式
            self.effective_config.update({
                "behavior_mode": "conservative",
                "base_delay_min": 1.5,
                "base_delay_max": 4.0,
                "action_interval_min": 3.0,
                "action_interval_max": 8.0,
                "random_pause_probability": 0.4,
                "typing_mistakes_probability": 0.05,
                "micro_movements_enabled": True,
            })
            self.logger.info("检测到高风险，切换到超保守模式")
            
        elif detection_level == "medium":
            # 中等检测风险，增加随机性
            self.effective_config.update({
                "behavior_mode": "conservative",
                "random_pause_probability": 0.25,
                "typing_mistakes_probability": 0.03,
                "jitter_enabled": True,
            })
            self.logger.info("检测到中等风险，增加行为随机性")
            
        elif detection_level == "low":
            # 低检测风险，可以稍微激进一些
            if self.effective_config["behavior_mode"] == "conservative":
                self.effective_config["behavior_mode"] = "moderate"
                self._apply_behavior_mode()
                self.logger.info("检测风险降低，切换到适中模式")