#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能监控模块

提供系统性能指标的收集、分析和报告功能，包括：
- 执行时间追踪
- 内存使用监控
- API调用统计
- 浏览器操作性能分析
- 实时性能指标展示
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os
from src.common.logger import get_logger


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float
    operation_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    api_calls: int
    api_response_time: float
    success: bool
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class LLMMetrics:
    """LLM调用指标"""
    timestamp: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time: float
    model_name: str
    cost_estimate: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class BrowserActionMetrics:
    """浏览器操作指标"""
    timestamp: float
    action_type: str
    selector: Optional[str]
    execution_time: float
    page_load_time: float
    success: bool
    error_message: Optional[str] = None
    screenshot_size: Optional[int] = None


class PerformanceMonitor:
    """性能监控器主类"""
    
    def __init__(self):
        self.logger = get_logger()
        self.metrics_history: List[PerformanceMetrics] = []
        self.llm_metrics_history: List[LLMMetrics] = []
        self.browser_metrics_history: List[BrowserActionMetrics] = []
        self.current_operation: Optional[str] = None
        self.start_time: Optional[float] = None
        self._lock = threading.Lock()
        
        # 性能阈值配置
        self.thresholds = {
            "max_execution_time": 30.0,
            "max_memory_usage_mb": 500.0,
            "max_api_response_time": 10.0,
            "max_browser_action_time": 5.0
        }
        
        # 统计计数器
        self.counters = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_api_calls": 0,
            "total_llm_calls": 0,
            "total_browser_actions": 0
        }
    
    def start_operation(self, operation_name: str) -> float:
        """开始记录操作"""
        with self._lock:
            self.current_operation = operation_name
            self.start_time = time.time()
            self.counters["total_operations"] += 1
            self.logger.info(f"开始操作: {operation_name}")
            return self.start_time
    
    def end_operation(self, success: bool = True, error_message: Optional[str] = None) -> PerformanceMetrics:
        """结束记录操作并生成性能指标"""
        with self._lock:
            if not self.start_time or not self.current_operation:
                raise ValueError("没有活动的操作可以结束")
            
            end_time = time.time()
            execution_time = end_time - self.start_time
            
            # 获取系统资源使用情况
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()
            
            # 创建性能指标
            metrics = PerformanceMetrics(
                timestamp=end_time,
                operation_name=self.current_operation,
                execution_time=execution_time,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                api_calls=self.counters["total_api_calls"],
                api_response_time=0.0,  # 将在API监控中更新
                success=success,
                error_message=error_message,
                additional_data={
                    "process_id": process.pid,
                    "thread_id": threading.get_ident()
                }
            )
            
            # 更新统计
            self.metrics_history.append(metrics)
            if success:
                self.counters["successful_operations"] += 1
            else:
                self.counters["failed_operations"] += 1
            
            # 检查性能阈值
            self._check_performance_thresholds(metrics)
            
            # 重置状态
            self.current_operation = None
            self.start_time = None
            
            self.logger.info(
                f"操作结束: {metrics.operation_name} - "
                f"耗时: {execution_time:.2f}s, "
                f"内存: {memory_usage:.1f}MB, "
                f"成功: {success}"
            )
            
            return metrics
    
    def record_llm_call(self, prompt_tokens: int, completion_tokens: int, 
                       response_time: float, model_name: str, 
                       success: bool = True, error_message: Optional[str] = None) -> LLMMetrics:
        """记录LLM调用指标"""
        with self._lock:
            total_tokens = prompt_tokens + completion_tokens
            
            # 估算成本 (基于GPT-4定价)
            cost_per_1k_tokens = 0.03 if "gpt-4" in model_name.lower() else 0.002
            cost_estimate = (total_tokens / 1000) * cost_per_1k_tokens
            
            metrics = LLMMetrics(
                timestamp=time.time(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time=response_time,
                model_name=model_name,
                cost_estimate=cost_estimate,
                success=success,
                error_message=error_message
            )
            
            self.llm_metrics_history.append(metrics)
            self.counters["total_llm_calls"] += 1
            
            self.logger.info(
                f"LLM调用记录: {model_name} - "
                f"tokens: {total_tokens}, "
                f"时间: {response_time:.2f}s, "
                f"成本: ${cost_estimate:.4f}"
            )
            
            return metrics
    
    def record_browser_action(self, action_type: str, selector: Optional[str],
                            execution_time: float, page_load_time: float,
                            success: bool = True, error_message: Optional[str] = None,
                            screenshot_size: Optional[int] = None) -> BrowserActionMetrics:
        """记录浏览器操作指标"""
        with self._lock:
            metrics = BrowserActionMetrics(
                timestamp=time.time(),
                action_type=action_type,
                selector=selector,
                execution_time=execution_time,
                page_load_time=page_load_time,
                success=success,
                error_message=error_message,
                screenshot_size=screenshot_size
            )
            
            self.browser_metrics_history.append(metrics)
            self.counters["total_browser_actions"] += 1
            
            self.logger.info(
                f"浏览器操作记录: {action_type} - "
                f"执行时间: {execution_time:.2f}s, "
                f"页面加载: {page_load_time:.2f}s, "
                f"成功: {success}"
            )
            
            return metrics
    
    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值并发出警告"""
        warnings = []
        
        if metrics.execution_time > self.thresholds["max_execution_time"]:
            warnings.append(f"执行时间超标: {metrics.execution_time:.2f}s")
        
        if metrics.memory_usage_mb > self.thresholds["max_memory_usage_mb"]:
            warnings.append(f"内存使用超标: {metrics.memory_usage_mb:.1f}MB")
        
        if warnings:
            self.logger.warning(
                f"性能警告 - 操作: {metrics.operation_name}, "
                f"警告: {'; '.join(warnings)}"
            )
    
    def get_llm_metrics(self) -> Dict[str, Any]:
        """获取LLM性能指标"""
        with self._lock:
            if not self.llm_metrics_history:
                return {
                    "total_calls": 0,
                    "avg_response_time": 0.0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "success_rate": 0.0
                }
            
            total_calls = len(self.llm_metrics_history)
            successful_calls = sum(1 for m in self.llm_metrics_history if m.success)
            avg_response_time = sum(m.response_time for m in self.llm_metrics_history) / total_calls
            total_tokens = sum(m.total_tokens for m in self.llm_metrics_history)
            total_cost = sum(m.cost_estimate for m in self.llm_metrics_history)
            
            return {
                "total_calls": total_calls,
                "avg_response_time": avg_response_time,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "success_rate": successful_calls / total_calls if total_calls > 0 else 0.0
            }
    
    def get_browser_metrics(self) -> Dict[str, Any]:
        """获取浏览器操作指标"""
        with self._lock:
            if not self.browser_metrics_history:
                return {
                    "total_actions": 0,
                    "avg_execution_time": 0.0,
                    "avg_page_load_time": 0.0,
                    "success_rate": 0.0
                }
            
            total_actions = len(self.browser_metrics_history)
            successful_actions = sum(1 for m in self.browser_metrics_history if m.success)
            avg_execution_time = sum(m.execution_time for m in self.browser_metrics_history) / total_actions
            avg_page_load_time = sum(m.page_load_time for m in self.browser_metrics_history) / total_actions
            
            return {
                "total_actions": total_actions,
                "avg_execution_time": avg_execution_time,
                "avg_page_load_time": avg_page_load_time,
                "success_rate": successful_actions / total_actions if total_actions > 0 else 0.0
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        with self._lock:
            if not self.metrics_history:
                return {
                    "avg_memory_usage_mb": 0.0,
                    "avg_cpu_usage_percent": 0.0,
                    "peak_memory_usage_mb": 0.0
                }
            
            total_ops = len(self.metrics_history)
            avg_memory = sum(m.memory_usage_mb for m in self.metrics_history) / total_ops
            avg_cpu = sum(m.cpu_usage_percent for m in self.metrics_history) / total_ops
            peak_memory = max(m.memory_usage_mb for m in self.metrics_history)
            
            return {
                "avg_memory_usage_mb": avg_memory,
                "avg_cpu_usage_percent": avg_cpu,
                "peak_memory_usage_mb": peak_memory
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        with self._lock:
            # 计算基本统计
            total_ops = len(self.metrics_history)
            successful_ops = sum(1 for m in self.metrics_history if m.success) if self.metrics_history else 0
            avg_execution_time = (
                sum(m.execution_time for m in self.metrics_history) / total_ops
                if total_ops > 0 else 0.0
            )
            avg_memory_usage = (
                sum(m.memory_usage_mb for m in self.metrics_history) / total_ops
                if total_ops > 0 else 0.0
            )
            
            # 计算LLM统计
            total_llm_cost = sum(m.cost_estimate for m in self.llm_metrics_history)
            avg_llm_response_time = (
                sum(m.response_time for m in self.llm_metrics_history) / len(self.llm_metrics_history)
                if self.llm_metrics_history else 0
            )
            
            # 计算浏览器操作统计
            avg_browser_time = (
                sum(m.execution_time for m in self.browser_metrics_history) / len(self.browser_metrics_history)
                if self.browser_metrics_history else 0
            )
            
            return {
                "total_operations": total_ops,
                "successful_operations": successful_ops,
                "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
                "avg_execution_time": avg_execution_time,
                "avg_memory_usage_mb": avg_memory_usage,
                "total_llm_calls": len(self.llm_metrics_history),
                "total_llm_cost": total_llm_cost,
                "avg_llm_response_time": avg_llm_response_time,
                "avg_response_time": avg_llm_response_time,  # Add this alias for test compatibility
                "total_browser_actions": len(self.browser_metrics_history),
                "avg_browser_action_time": avg_browser_time,
                "counters": self.counters.copy()
            }
    
    def export_metrics(self, file_path: str):
        """导出性能指标到JSON文件"""
        with self._lock:
            data = {
                "performance_metrics": [asdict(m) for m in self.metrics_history],
                "llm_metrics": [asdict(m) for m in self.llm_metrics_history],
                "browser_metrics": [asdict(m) for m in self.browser_metrics_history],
                "summary": self.get_summary(),
                "exported_at": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"性能指标已导出到: {file_path}")
    
    def clear_history(self):
        """清除历史数据"""
        with self._lock:
            self.metrics_history.clear()
            self.llm_metrics_history.clear()
            self.browser_metrics_history.clear()
            # Reset counters
            for key in self.counters:
                self.counters[key] = 0
            self.logger.info("性能监控历史数据已清除")
    
    def reset(self):
        """重置性能监控器状态"""
        self.clear_history()


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return performance_monitor