#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能错误恢复管理器

实现自动重试机制、退避策略、备选执行路径和用户交互式错误解决方案。
"""

from __future__ import annotations

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from src.common.logger import get_logger, get_structured_logger
from src.common.performance_monitor import get_performance_monitor
from src.common.exceptions import (
    BrowserAgentError, ErrorContext, ErrorCategory, ErrorSeverity,
    TimeoutError, ElementNotFoundError, ElementNotInteractableError,
    NetworkError, ActionExecutionError
)


class RecoveryStatus(Enum):
    """恢复状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_USER_INPUT = "requires_user_input"


class RecoveryStrategy(Enum):
    """恢复策略枚举"""
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    ALTERNATIVE_PATH = "alternative_path"
    DEGRADED_MODE = "degraded_mode"
    USER_INTERVENTION = "user_intervention"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class RecoveryAttempt:
    """恢复尝试记录"""
    attempt_id: str
    timestamp: datetime
    strategy: RecoveryStrategy
    action_type: str
    parameters: Dict[str, Any]
    duration: float = 0.0
    status: RecoveryStatus = RecoveryStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "timestamp": self.timestamp.isoformat(),
            "strategy": self.strategy.value,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "duration": self.duration,
            "status": self.status.value,
            "result": self.result,
            "error_message": self.error_message
        }


@dataclass
class RecoveryPlan:
    """恢复计划"""
    plan_id: str
    error: BrowserAgentError
    strategies: List[RecoveryStrategy] = field(default_factory=list)
    attempts: List[RecoveryAttempt] = field(default_factory=list)
    current_strategy_index: int = 0
    max_total_attempts: int = 5
    max_duration: float = 300.0  # 5分钟
    start_time: datetime = field(default_factory=datetime.now)
    status: RecoveryStatus = RecoveryStatus.PENDING
    user_feedback_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "error": self.error.to_dict(),
            "strategies": [s.value for s in self.strategies],
            "attempts": [a.to_dict() for a in self.attempts],
            "current_strategy_index": self.current_strategy_index,
            "max_total_attempts": self.max_total_attempts,
            "max_duration": self.max_duration,
            "start_time": self.start_time.isoformat(),
            "status": self.status.value,
            "user_feedback_required": self.user_feedback_required
        }


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise Exception("熔断器开启，拒绝执行")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置熔断器"""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class AlternativePathManager:
    """备选路径管理器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.alternative_selectors = {}
        self.fallback_actions = {}
    
    def register_alternative_selector(self, original_selector: str, 
                                    alternatives: List[str]):
        """注册备选选择器"""
        self.alternative_selectors[original_selector] = alternatives
    
    def register_fallback_action(self, action_type: str, 
                               fallback_func: Callable):
        """注册备选动作"""
        self.fallback_actions[action_type] = fallback_func
    
    def get_alternative_selectors(self, selector: str) -> List[str]:
        """获取备选选择器"""
        alternatives = self.alternative_selectors.get(selector, [])
        
        # 生成智能备选选择器
        if not alternatives:
            alternatives = self._generate_smart_alternatives(selector)
        
        return alternatives
    
    def _generate_smart_alternatives(self, selector: str) -> List[str]:
        """生成智能备选选择器"""
        alternatives = []
        
        # CSS选择器转换为其他类型
        if selector.startswith('#'):
            # ID选择器转换
            element_id = selector[1:]
            alternatives.extend([
                f'[id="{element_id}"]',
                f'*[id*="{element_id}"]',
                f'text="{element_id}"'  # 尝试文本匹配
            ])
        
        elif selector.startswith('.'):
            # 类选择器转换
            class_name = selector[1:]
            alternatives.extend([
                f'[class*="{class_name}"]',
                f'*[class~="{class_name}"]'
            ])
        
        elif selector.startswith('//'):
            # XPath转换为CSS
            # 简单的XPath到CSS转换
            if '[@id=' in selector:
                id_match = selector.split('[@id=')[1].split(']')[0].strip('"\'')
                alternatives.append(f'#{id_match}')
        
        else:
            # 标签选择器增强
            alternatives.extend([
                f'{selector}:visible',
                f'{selector}:enabled',
                f'{selector}:not([disabled])'
            ])
        
        return alternatives
    
    def execute_fallback_action(self, action_type: str, *args, **kwargs) -> Any:
        """执行备选动作"""
        if action_type in self.fallback_actions:
            return self.fallback_actions[action_type](*args, **kwargs)
        else:
            raise ValueError(f"未找到备选动作: {action_type}")


class UserInteractionManager:
    """用户交互管理器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.pending_interactions = {}
        self.interaction_callbacks = {}
    
    def request_user_input(self, interaction_id: str, prompt: str, 
                          options: Optional[List[str]] = None,
                          timeout: float = 300.0) -> str:
        """请求用户输入"""
        
        interaction = {
            "id": interaction_id,
            "prompt": prompt,
            "options": options,
            "timestamp": datetime.now(),
            "timeout": timeout,
            "status": "pending"
        }
        
        self.pending_interactions[interaction_id] = interaction
        
        self.logger.info(f"请求用户输入: {prompt}")
        
        # 在实际实现中，这里会通过UI或CLI接口与用户交互
        # 现在返回默认响应
        return self._get_default_response(prompt, options)
    
    def _get_default_response(self, prompt: str, options: Optional[List[str]]) -> str:
        """获取默认响应（用于自动化测试）"""
        if options:
            return options[0]  # 选择第一个选项
        
        # 根据提示内容返回合理的默认值
        if "重试" in prompt or "retry" in prompt.lower():
            return "yes"
        elif "跳过" in prompt or "skip" in prompt.lower():
            return "no"
        elif "继续" in prompt or "continue" in prompt.lower():
            return "yes"
        else:
            return "continue"
    
    def provide_user_response(self, interaction_id: str, response: str):
        """提供用户响应"""
        if interaction_id in self.pending_interactions:
            self.pending_interactions[interaction_id]["response"] = response
            self.pending_interactions[interaction_id]["status"] = "completed"
            
            # 触发回调
            if interaction_id in self.interaction_callbacks:
                self.interaction_callbacks[interaction_id](response)
    
    def register_callback(self, interaction_id: str, callback: Callable):
        """注册交互回调"""
        self.interaction_callbacks[interaction_id] = callback


class RecoveryManager:
    """智能错误恢复管理器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.structured_logger = get_structured_logger()
        self.perf_monitor = get_performance_monitor()
        
        # 组件初始化
        self.circuit_breakers = {}
        self.alternative_path_manager = AlternativePathManager()
        self.user_interaction_manager = UserInteractionManager()
        
        # 恢复计划存储
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        
        # 配置参数
        self.config = {
            "max_retry_attempts": 3,
            "base_retry_delay": 1.0,
            "max_retry_delay": 30.0,
            "backoff_multiplier": 2.0,
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 60.0,
            "user_interaction_timeout": 300.0
        }
        
        # 统计信息
        self.stats = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "user_interventions": 0,
            "circuit_breaker_trips": 0
        }
    
    def create_recovery_plan(self, error: BrowserAgentError, 
                           context: Dict[str, Any]) -> RecoveryPlan:
        """创建恢复计划"""
        
        plan_id = f"recovery_{int(time.time() * 1000)}"
        
        # 根据错误类型选择恢复策略
        strategies = self._select_recovery_strategies(error, context)
        
        plan = RecoveryPlan(
            plan_id=plan_id,
            error=error,
            strategies=strategies,
            max_total_attempts=self.config["max_retry_attempts"]
        )
        
        self.recovery_plans[plan_id] = plan
        
        self.logger.info(f"创建恢复计划: {plan_id}, 策略: {[s.value for s in strategies]}")
        
        return plan
    
    def _select_recovery_strategies(self, error: BrowserAgentError, 
                                  context: Dict[str, Any]) -> List[RecoveryStrategy]:
        """选择恢复策略"""
        
        strategies = []
        
        # 根据错误类别选择策略
        if error.category == ErrorCategory.TIMEOUT:
            strategies.extend([
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.ALTERNATIVE_PATH,
                RecoveryStrategy.USER_INTERVENTION
            ])
        
        elif error.category == ErrorCategory.BROWSER:
            if isinstance(error, ElementNotFoundError):
                strategies.extend([
                    RecoveryStrategy.IMMEDIATE_RETRY,
                    RecoveryStrategy.ALTERNATIVE_PATH,
                    RecoveryStrategy.DEGRADED_MODE
                ])
            elif isinstance(error, ElementNotInteractableError):
                strategies.extend([
                    RecoveryStrategy.EXPONENTIAL_BACKOFF,
                    RecoveryStrategy.ALTERNATIVE_PATH,
                    RecoveryStrategy.USER_INTERVENTION
                ])
        
        elif error.category == ErrorCategory.NETWORK:
            strategies.extend([
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.CIRCUIT_BREAKER,
                RecoveryStrategy.USER_INTERVENTION
            ])
        
        elif error.category == ErrorCategory.LLM:
            strategies.extend([
                RecoveryStrategy.IMMEDIATE_RETRY,
                RecoveryStrategy.ALTERNATIVE_PATH,
                RecoveryStrategy.DEGRADED_MODE
            ])
        
        else:
            # 默认策略
            strategies.extend([
                RecoveryStrategy.IMMEDIATE_RETRY,
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.USER_INTERVENTION
            ])
        
        return strategies
    
    def execute_recovery_plan(self, plan_id: str, 
                            executor_callback: Callable) -> Dict[str, Any]:
        """执行恢复计划"""
        
        if plan_id not in self.recovery_plans:
            return {
                "success": False,
                "message": f"未找到恢复计划: {plan_id}"
            }
        
        plan = self.recovery_plans[plan_id]
        plan.status = RecoveryStatus.IN_PROGRESS
        
        self.stats["total_recoveries"] += 1
        
        try:
            # 执行恢复策略
            for strategy_index, strategy in enumerate(plan.strategies):
                plan.current_strategy_index = strategy_index
                
                # 检查是否超时或超过最大尝试次数
                if self._should_stop_recovery(plan):
                    break
                
                # 执行当前策略
                result = self._execute_strategy(plan, strategy, executor_callback)
                
                if result["success"]:
                    plan.status = RecoveryStatus.SUCCESS
                    self.stats["successful_recoveries"] += 1
                    
                    self.logger.info(f"恢复成功: {plan_id}, 策略: {strategy.value}")
                    
                    return {
                        "success": True,
                        "message": "恢复成功",
                        "plan_id": plan_id,
                        "strategy_used": strategy.value,
                        "attempts": len(plan.attempts)
                    }
            
            # 所有策略都失败了
            plan.status = RecoveryStatus.FAILED
            self.stats["failed_recoveries"] += 1
            
            return {
                "success": False,
                "message": "所有恢复策略都失败了",
                "plan_id": plan_id,
                "attempts": len(plan.attempts)
            }
        
        except Exception as e:
            plan.status = RecoveryStatus.FAILED
            self.stats["failed_recoveries"] += 1
            
            self.logger.error(f"恢复计划执行异常: {e}")
            
            return {
                "success": False,
                "message": f"恢复计划执行异常: {e}",
                "plan_id": plan_id
            }
    
    def _should_stop_recovery(self, plan: RecoveryPlan) -> bool:
        """判断是否应该停止恢复"""
        
        # 检查总尝试次数
        if len(plan.attempts) >= plan.max_total_attempts:
            return True
        
        # 检查总耗时
        elapsed = datetime.now() - plan.start_time
        if elapsed.total_seconds() > plan.max_duration:
            return True
        
        return False
    
    def _execute_strategy(self, plan: RecoveryPlan, strategy: RecoveryStrategy,
                         executor_callback: Callable) -> Dict[str, Any]:
        """执行恢复策略"""
        
        attempt_id = f"{plan.plan_id}_attempt_{len(plan.attempts)}"
        start_time = time.time()
        
        attempt = RecoveryAttempt(
            attempt_id=attempt_id,
            timestamp=datetime.now(),
            strategy=strategy,
            action_type="recovery",
            parameters={}
        )
        
        plan.attempts.append(attempt)
        attempt.status = RecoveryStatus.IN_PROGRESS
        
        try:
            if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
                result = self._immediate_retry(plan, executor_callback)
            
            elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
                result = self._exponential_backoff_retry(plan, executor_callback)
            
            elif strategy == RecoveryStrategy.ALTERNATIVE_PATH:
                result = self._alternative_path_recovery(plan, executor_callback)
            
            elif strategy == RecoveryStrategy.DEGRADED_MODE:
                result = self._degraded_mode_recovery(plan, executor_callback)
            
            elif strategy == RecoveryStrategy.USER_INTERVENTION:
                result = self._user_intervention_recovery(plan, executor_callback)
            
            elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                result = self._circuit_breaker_recovery(plan, executor_callback)
            
            else:
                result = {"success": False, "message": f"未知策略: {strategy}"}
            
            attempt.result = result
            attempt.status = RecoveryStatus.SUCCESS if result["success"] else RecoveryStatus.FAILED
            
            return result
        
        except Exception as e:
            attempt.error_message = str(e)
            attempt.status = RecoveryStatus.FAILED
            
            return {
                "success": False,
                "message": f"策略执行异常: {e}"
            }
        
        finally:
            attempt.duration = time.time() - start_time
    
    def _immediate_retry(self, plan: RecoveryPlan, 
                        executor_callback: Callable) -> Dict[str, Any]:
        """立即重试策略"""
        
        try:
            # 直接重新执行原始指令
            original_instruction = plan.error.context.instruction
            if original_instruction:
                result = executor_callback(original_instruction)
                return result
            else:
                return {"success": False, "message": "无法获取原始指令"}
        
        except Exception as e:
            return {"success": False, "message": f"重试失败: {e}"}
    
    def _exponential_backoff_retry(self, plan: RecoveryPlan,
                                  executor_callback: Callable) -> Dict[str, Any]:
        """指数退避重试策略"""
        
        attempt_count = len([a for a in plan.attempts if a.strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF])
        
        # 计算延迟时间
        delay = min(
            self.config["base_retry_delay"] * (self.config["backoff_multiplier"] ** attempt_count),
            self.config["max_retry_delay"]
        )
        
        self.logger.info(f"指数退避延迟: {delay}秒")
        time.sleep(delay)
        
        # 重试执行
        return self._immediate_retry(plan, executor_callback)
    
    def _alternative_path_recovery(self, plan: RecoveryPlan,
                                  executor_callback: Callable) -> Dict[str, Any]:
        """备选路径恢复策略"""
        
        original_instruction = plan.error.context.instruction
        if not original_instruction:
            return {"success": False, "message": "无法获取原始指令"}
        
        # 如果是元素未找到错误，尝试备选选择器
        if isinstance(plan.error, ElementNotFoundError):
            original_selector = plan.error.selector
            alternatives = self.alternative_path_manager.get_alternative_selectors(original_selector)
            
            for alt_selector in alternatives:
                try:
                    # 创建修改后的指令
                    modified_instruction = original_instruction.copy()
                    modified_instruction["selector"] = alt_selector
                    
                    self.logger.info(f"尝试备选选择器: {alt_selector}")
                    
                    result = executor_callback(modified_instruction)
                    if result.get("success", False):
                        # 注册成功的备选选择器
                        self.alternative_path_manager.register_alternative_selector(
                            original_selector, [alt_selector]
                        )
                        return result
                
                except Exception as e:
                    self.logger.debug(f"备选选择器失败: {alt_selector}, 错误: {e}")
                    continue
            
            return {"success": False, "message": "所有备选选择器都失败了"}
        
        # 其他类型的错误，尝试备选动作
        action_type = original_instruction.get("action")
        if action_type:
            try:
                result = self.alternative_path_manager.execute_fallback_action(
                    action_type, original_instruction
                )
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "message": f"备选动作失败: {e}"}
        
        return {"success": False, "message": "无法执行备选路径"}
    
    def _degraded_mode_recovery(self, plan: RecoveryPlan,
                               executor_callback: Callable) -> Dict[str, Any]:
        """降级模式恢复策略"""
        
        # 尝试简化的操作
        original_instruction = plan.error.context.instruction
        if not original_instruction:
            return {"success": False, "message": "无法获取原始指令"}
        
        action_type = original_instruction.get("action")
        
        # 根据动作类型提供降级方案
        if action_type == "click":
            # 降级为简单点击
            simplified_instruction = {
                "action": "click",
                "selector": original_instruction.get("selector"),
                "options": {"force": True, "timeout": 5000}
            }
            
        elif action_type == "fill":
            # 降级为逐字符输入
            simplified_instruction = {
                "action": "type",
                "selector": original_instruction.get("selector"),
                "value": original_instruction.get("value"),
                "options": {"delay": 100}
            }
        
        elif action_type == "extract":
            # 降级为简单文本提取
            simplified_instruction = {
                "action": "extract",
                "selector": "body",
                "extract_type": "text"
            }
        
        else:
            return {"success": False, "message": f"无法为动作 {action_type} 提供降级方案"}
        
        try:
            result = executor_callback(simplified_instruction)
            return result
        except Exception as e:
            return {"success": False, "message": f"降级模式失败: {e}"}
    
    def _user_intervention_recovery(self, plan: RecoveryPlan,
                                   executor_callback: Callable) -> Dict[str, Any]:
        """用户干预恢复策略"""
        
        self.stats["user_interventions"] += 1
        
        # 构建用户提示
        error_msg = plan.error.message
        suggestions = plan.error.recovery_suggestions
        
        prompt = f"操作失败: {error_msg}\n\n"
        if suggestions:
            prompt += "建议的解决方案:\n"
            for i, suggestion in enumerate(suggestions, 1):
                prompt += f"{i}. {suggestion}\n"
        
        prompt += "\n请选择操作: "
        options = ["重试", "跳过", "手动处理", "取消"]
        
        # 请求用户输入
        interaction_id = f"recovery_{plan.plan_id}"
        response = self.user_interaction_manager.request_user_input(
            interaction_id, prompt, options, 
            timeout=self.config["user_interaction_timeout"]
        )
        
        # 处理用户响应
        if response == "重试" or response == "yes":
            return self._immediate_retry(plan, executor_callback)
        
        elif response == "跳过":
            return {
                "success": True,
                "message": "用户选择跳过",
                "skipped": True
            }
        
        elif response == "手动处理":
            plan.user_feedback_required = True
            plan.status = RecoveryStatus.REQUIRES_USER_INPUT
            
            return {
                "success": False,
                "message": "需要用户手动处理",
                "requires_manual_intervention": True
            }
        
        else:  # 取消
            plan.status = RecoveryStatus.CANCELLED
            return {
                "success": False,
                "message": "用户取消操作",
                "cancelled": True
            }
    
    def _circuit_breaker_recovery(self, plan: RecoveryPlan,
                                 executor_callback: Callable) -> Dict[str, Any]:
        """熔断器恢复策略"""
        
        error_type = plan.error.__class__.__name__
        
        # 获取或创建熔断器
        if error_type not in self.circuit_breakers:
            self.circuit_breakers[error_type] = CircuitBreaker(
                failure_threshold=self.config["circuit_breaker_threshold"],
                recovery_timeout=self.config["circuit_breaker_timeout"]
            )
        
        circuit_breaker = self.circuit_breakers[error_type]
        
        try:
            # 通过熔断器执行
            result = circuit_breaker.call(self._immediate_retry, plan, executor_callback)
            return result
        
        except Exception as e:
            if "熔断器开启" in str(e):
                self.stats["circuit_breaker_trips"] += 1
                return {
                    "success": False,
                    "message": "熔断器开启，暂停执行",
                    "circuit_breaker_open": True
                }
            else:
                return {"success": False, "message": f"熔断器执行失败: {e}"}
    
    def get_recovery_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取恢复状态"""
        if plan_id in self.recovery_plans:
            return self.recovery_plans[plan_id].to_dict()
        return None
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        success_rate = (
            self.stats["successful_recoveries"] / self.stats["total_recoveries"]
            if self.stats["total_recoveries"] > 0 else 0.0
        )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "active_plans": len([p for p in self.recovery_plans.values() 
                               if p.status == RecoveryStatus.IN_PROGRESS]),
            "pending_user_interactions": len(self.user_interaction_manager.pending_interactions)
        }
    
    def cancel_recovery_plan(self, plan_id: str) -> bool:
        """取消恢复计划"""
        if plan_id in self.recovery_plans:
            plan = self.recovery_plans[plan_id]
            plan.status = RecoveryStatus.CANCELLED
            self.logger.info(f"恢复计划已取消: {plan_id}")
            return True
        return False
    
    def clear_recovery_history(self):
        """清除恢复历史"""
        self.recovery_plans.clear()
        self.stats = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "user_interventions": 0,
            "circuit_breaker_trips": 0
        }
        self.logger.info("恢复历史已清除")


# 全局恢复管理器实例
recovery_manager = RecoveryManager()


def get_recovery_manager() -> RecoveryManager:
    """获取全局恢复管理器"""
    return recovery_manager