#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强错误处理器

负责统一封装动作执行过程中的异常、诊断原因并给出恢复建议。
支持分层异常处理、智能错误诊断和自动恢复机制。
"""

from __future__ import annotations

import time
import json
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from src.common.logger import get_logger, get_structured_logger
from src.common.performance_monitor import get_performance_monitor
from src.common.exceptions import (
    BrowserAgentError, ErrorContext, ErrorCategory, ErrorSeverity,
    create_error_from_exception, get_error_category_from_string,
    TimeoutError, ElementNotFoundError, ElementNotInteractableError,
    ActionExecutionError, SafetyValidationError, NetworkError
)


@dataclass
class RecoveryAction:
    """恢复动作定义"""
    action_type: str
    description: str
    parameters: Dict[str, Any]
    priority: int = 1  # 优先级，数字越小优先级越高
    max_attempts: int = 3
    timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorReport:
    """错误报告"""
    error_id: str
    timestamp: datetime
    error: BrowserAgentError
    context: ErrorContext
    recovery_attempts: List[Dict[str, Any]]
    resolution_status: str  # "pending", "resolved", "failed"
    user_feedback: Optional[str] = None
    recovery_plan_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error.to_dict(),
            "context": self.context.to_dict(),
            "recovery_attempts": self.recovery_attempts,
            "resolution_status": self.resolution_status,
            "user_feedback": self.user_feedback,
            "recovery_plan_id": self.recovery_plan_id
        }


class RetryStrategy:
    """重试策略"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def get_delay(self, attempt: int) -> float:
        """计算指数退避延迟"""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int, error: BrowserAgentError) -> bool:
        """判断是否应该重试"""
        if attempt >= self.max_attempts:
            return False
        
        # 某些错误类型不适合重试
        if error.severity == ErrorSeverity.CRITICAL:
            return False
        
        if error.category in [ErrorCategory.VALIDATION, ErrorCategory.PERMISSION]:
            return False
        
        return True


class ErrorHandler:
    """增强错误处理器实现"""

    def __init__(self):
        self._logger = get_logger()
        self._structured_logger = get_structured_logger()
        self._perf_monitor = get_performance_monitor()
        
        # 错误统计
        self._error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recovery_success_rate": 0.0,
            "last_reset": datetime.now()
        }
        
        # 错误报告存储
        self._error_reports: List[ErrorReport] = []
        self._max_reports = 1000  # 最大保存的错误报告数量
        
        # 恢复策略映射
        self._recovery_strategies = self._initialize_recovery_strategies()
        
        # 重试策略
        self._retry_strategy = RetryStrategy()

    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, List[RecoveryAction]]:
        """初始化恢复策略映射"""
        return {
            ErrorCategory.TIMEOUT: [
                RecoveryAction("wait", "增加等待时间", {"timeout": 10.0}, priority=1),
                RecoveryAction("refresh", "刷新页面", {}, priority=2),
                RecoveryAction("navigate", "重新导航", {}, priority=3)
            ],
            ErrorCategory.BROWSER: [
                RecoveryAction("wait", "等待元素出现", {"timeout": 5.0}, priority=1),
                RecoveryAction("scroll", "滚动到元素位置", {}, priority=2),
                RecoveryAction("alternative_selector", "尝试备选选择器", {}, priority=3),
                RecoveryAction("screenshot", "截屏诊断", {}, priority=4)
            ],
            ErrorCategory.NETWORK: [
                RecoveryAction("retry", "重试网络请求", {"delay": 2.0}, priority=1),
                RecoveryAction("check_connection", "检查网络连接", {}, priority=2),
                RecoveryAction("use_proxy", "尝试使用代理", {}, priority=3)
            ],
            ErrorCategory.LLM: [
                RecoveryAction("retry", "重试LLM调用", {"delay": 1.0}, priority=1),
                RecoveryAction("fallback_model", "使用备用模型", {}, priority=2),
                RecoveryAction("simplify_prompt", "简化提示词", {}, priority=3)
            ],
            ErrorCategory.PARSING: [
                RecoveryAction("reanalyze", "重新分析页面", {}, priority=1),
                RecoveryAction("alternative_parser", "使用备选解析器", {}, priority=2),
                RecoveryAction("manual_extraction", "手动提取信息", {}, priority=3)
            ]
        }

    def handle_error(self, error: Exception, instruction: Dict[str, Any], 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        """处理错误的主入口方法"""
        
        # 转换为项目特定异常
        if not isinstance(error, BrowserAgentError):
            error_context = self._build_error_context(instruction, context)
            error = create_error_from_exception(error, error_context)
        
        # 更新统计信息
        self._update_error_stats(error)
        
        # 记录结构化日志
        self._log_error(error, instruction, context)
        
        # 生成错误报告
        error_report = self._create_error_report(error, instruction, context)
        
        # 诊断错误
        diagnosis = self._diagnose_error(error, instruction, context)
        
        # 生成恢复建议
        recovery_suggestions = self._generate_recovery_suggestions(error, diagnosis)
        
        # 自动创建恢复计划（对于可恢复的错误）
        recovery_plan_info = None
        if error.severity != ErrorSeverity.CRITICAL and error.category != ErrorCategory.VALIDATION:
            recovery_plan_result = self.create_recovery_plan(error, context)
            if recovery_plan_result.get("success", False):
                recovery_plan_info = {
                    "plan_id": recovery_plan_result["plan_id"],
                    "strategies": recovery_plan_result["strategies"]
                }
                # 将计划ID关联到错误报告
                error_report.recovery_plan_id = recovery_plan_result["plan_id"]
        
        # 构建响应
        result = {
            "success": False,
            "message": error.message,
            "error_id": error_report.error_id,
            "error_type": error.__class__.__name__,
            "category": error.category.value,
            "severity": error.severity.value,
            "diagnosis": diagnosis,
            "recovery_suggestions": recovery_suggestions,
            "recovery_plan": recovery_plan_info,
            "context": error.context.to_dict() if error.context else {},
            "timestamp": error.timestamp.isoformat()
        }
        
        return result

    def _build_error_context(self, instruction: Dict[str, Any], 
                           context: Dict[str, Any]) -> ErrorContext:
        """构建错误上下文"""
        error_context = ErrorContext()
        
        # 设置指令上下文
        error_context.set_instruction_context(instruction)
        
        # 从context中提取信息
        if "page_url" in context:
            error_context.set_page_context(context["page_url"], context.get("page_title"))
        
        if "operation_id" in context:
            error_context.set_operation_context(context["operation_id"], context.get("user_input"))
        
        if "browser_state" in context:
            error_context.set_browser_state(context["browser_state"])
        
        if "system_state" in context:
            error_context.set_system_state(context["system_state"])
        
        # 添加额外数据
        for key, value in context.items():
            if key not in ["page_url", "page_title", "operation_id", "user_input", 
                          "browser_state", "system_state"]:
                error_context.add_data(key, value)
        
        return error_context

    def _update_error_stats(self, error: BrowserAgentError):
        """更新错误统计信息"""
        self._error_stats["total_errors"] += 1
        
        # 按类别统计
        category = error.category.value
        if category not in self._error_stats["errors_by_category"]:
            self._error_stats["errors_by_category"][category] = 0
        self._error_stats["errors_by_category"][category] += 1
        
        # 按严重程度统计
        severity = error.severity.value
        if severity not in self._error_stats["errors_by_severity"]:
            self._error_stats["errors_by_severity"][severity] = 0
        self._error_stats["errors_by_severity"][severity] += 1

    def _log_error(self, error: BrowserAgentError, instruction: Dict[str, Any], 
                  context: Dict[str, Any]):
        """记录错误日志"""
        
        # 记录标准日志
        self._logger.error(
            f"错误处理 - 类型: {error.__class__.__name__}, "
            f"类别: {error.category.value}, "
            f"严重程度: {error.severity.value}, "
            f"消息: {error.message}"
        )
        
        # 记录结构化日志
        self._structured_logger.error_performance(
            "error_occurred",
            {
                "error_type": error.__class__.__name__,
                "category": error.category.value,
                "severity": error.severity.value,
                "message": error.message,
                "instruction": instruction,
                "context": context,
                "recovery_suggestions": error.recovery_suggestions
            }
        )

    def _create_error_report(self, error: BrowserAgentError, 
                           instruction: Dict[str, Any], context: Dict[str, Any]) -> ErrorReport:
        """创建错误报告"""
        error_id = f"ERR_{int(time.time() * 1000)}_{len(self._error_reports)}"
        
        report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.now(),
            error=error,
            context=error.context or ErrorContext(),
            recovery_attempts=[],
            resolution_status="pending"
        )
        
        # 添加到报告列表
        self._error_reports.append(report)
        
        # 保持报告数量在限制内
        if len(self._error_reports) > self._max_reports:
            self._error_reports = self._error_reports[-self._max_reports:]
        
        return report

    def _diagnose_error(self, error: BrowserAgentError, instruction: Dict[str, Any], 
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """诊断错误原因"""
        
        diagnosis = {
            "error_type": error.__class__.__name__,
            "category": error.category.value,
            "severity": error.severity.value,
            "probable_causes": [],
            "affected_components": [],
            "impact_assessment": "unknown"
        }
        
        # 根据错误类型进行具体诊断
        if isinstance(error, TimeoutError):
            diagnosis["probable_causes"] = [
                "网络延迟过高",
                "页面加载缓慢",
                "元素渲染延迟",
                "JavaScript执行阻塞"
            ]
            diagnosis["affected_components"] = ["browser", "network"]
            diagnosis["impact_assessment"] = "medium"
        
        elif isinstance(error, ElementNotFoundError):
            diagnosis["probable_causes"] = [
                "选择器不正确",
                "元素尚未渲染",
                "页面结构发生变化",
                "元素被动态加载"
            ]
            diagnosis["affected_components"] = ["perception", "browser"]
            diagnosis["impact_assessment"] = "high"
        
        elif isinstance(error, ElementNotInteractableError):
            diagnosis["probable_causes"] = [
                "元素被其他元素遮挡",
                "元素不在视口内",
                "元素处于禁用状态",
                "页面正在加载中"
            ]
            diagnosis["affected_components"] = ["action", "browser"]
            diagnosis["impact_assessment"] = "medium"
        
        elif isinstance(error, NetworkError):
            diagnosis["probable_causes"] = [
                "网络连接中断",
                "DNS解析失败",
                "代理配置错误",
                "目标服务器不可达"
            ]
            diagnosis["affected_components"] = ["network", "browser"]
            diagnosis["impact_assessment"] = "high"
        
        # 添加上下文相关的诊断信息
        if error.context:
            if error.context.page_url:
                diagnosis["page_url"] = error.context.page_url
            if error.context.instruction:
                diagnosis["failed_instruction"] = error.context.instruction
        
        return diagnosis

    def _generate_recovery_suggestions(self, error: BrowserAgentError, 
                                     diagnosis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成恢复建议"""
        
        suggestions = []
        
        # 从错误对象获取内置建议
        if error.recovery_suggestions:
            for suggestion in error.recovery_suggestions:
                suggestions.append({
                    "type": "built_in",
                    "description": suggestion,
                    "priority": 1,
                    "automated": False
                })
        
        # 根据错误类别获取策略建议
        if error.category in self._recovery_strategies:
            for action in self._recovery_strategies[error.category]:
                suggestions.append({
                    "type": "strategy",
                    "action": action.action_type,
                    "description": action.description,
                    "parameters": action.parameters,
                    "priority": action.priority,
                    "automated": True,
                    "max_attempts": action.max_attempts,
                    "timeout": action.timeout
                })
        
        # 根据诊断结果添加特定建议
        if "网络" in str(diagnosis.get("probable_causes", [])):
            suggestions.append({
                "type": "diagnostic",
                "description": "检查网络连接状态",
                "priority": 1,
                "automated": False
            })
        
        if "选择器" in str(diagnosis.get("probable_causes", [])):
            suggestions.append({
                "type": "diagnostic",
                "description": "使用页面分析工具重新生成选择器",
                "priority": 2,
                "automated": True
            })
        
        # 按优先级排序
        suggestions.sort(key=lambda x: x.get("priority", 999))
        
        return suggestions

    def attempt_recovery(self, error_id: str, recovery_action: Dict[str, Any], 
                        executor_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """尝试执行恢复动作"""
        
        # 查找错误报告
        report = None
        for r in self._error_reports:
            if r.error_id == error_id:
                report = r
                break
        
        if not report:
            return {
                "success": False,
                "message": f"未找到错误报告: {error_id}"
            }
        
        # 记录恢复尝试
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "action": recovery_action,
            "result": None
        }
        
        try:
            # 如果提供了执行器回调，尝试自动恢复
            if executor_callback and recovery_action.get("automated", False):
                result = executor_callback(recovery_action)
                attempt["result"] = result
                
                if result.get("success", False):
                    report.resolution_status = "resolved"
                    self._logger.info(f"错误 {error_id} 自动恢复成功")
                    return {
                        "success": True,
                        "message": "自动恢复成功",
                        "result": result
                    }
            
            # 手动恢复建议
            return {
                "success": False,
                "message": "需要手动执行恢复动作",
                "suggestion": recovery_action["description"]
            }
            
        except Exception as e:
            attempt["result"] = {"success": False, "error": str(e)}
            self._logger.error(f"恢复尝试失败: {e}")
            return {
                "success": False,
                "message": f"恢复尝试失败: {e}"
            }
        
        finally:
            report.recovery_attempts.append(attempt)

    def create_recovery_plan(self, error: BrowserAgentError, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """创建智能恢复计划"""
        try:
            from src.action.recovery_manager import get_recovery_manager
            
            recovery_manager = get_recovery_manager()
            plan = recovery_manager.create_recovery_plan(error, context)
            
            self._logger.info(f"创建恢复计划: {plan.plan_id}")
            
            return {
                "success": True,
                "plan_id": plan.plan_id,
                "strategies": [s.value for s in plan.strategies],
                "message": "恢复计划已创建"
            }
            
        except Exception as e:
            self._logger.error(f"创建恢复计划失败: {e}")
            return {
                "success": False,
                "message": f"创建恢复计划失败: {e}"
            }

    def execute_recovery_plan(self, plan_id: str, 
                            executor_callback: Callable) -> Dict[str, Any]:
        """执行智能恢复计划"""
        try:
            from src.action.recovery_manager import get_recovery_manager
            
            recovery_manager = get_recovery_manager()
            result = recovery_manager.execute_recovery_plan(plan_id, executor_callback)
            
            # 更新错误报告状态
            if result.get("success", False):
                for report in self._error_reports:
                    if hasattr(report, 'recovery_plan_id') and report.recovery_plan_id == plan_id:
                        report.resolution_status = "resolved"
                        break
            
            return result
            
        except Exception as e:
            self._logger.error(f"执行恢复计划失败: {e}")
            return {
                "success": False,
                "message": f"执行恢复计划失败: {e}"
            }

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        
        # 计算恢复成功率
        total_attempts = sum(len(r.recovery_attempts) for r in self._error_reports)
        successful_recoveries = sum(
            1 for r in self._error_reports 
            if r.resolution_status == "resolved"
        )
        
        recovery_rate = (
            successful_recoveries / len(self._error_reports) 
            if self._error_reports else 0.0
        )
        
        self._error_stats["recovery_success_rate"] = recovery_rate
        
        return {
            **self._error_stats,
            "total_reports": len(self._error_reports),
            "pending_reports": len([r for r in self._error_reports if r.resolution_status == "pending"]),
            "resolved_reports": len([r for r in self._error_reports if r.resolution_status == "resolved"]),
            "failed_reports": len([r for r in self._error_reports if r.resolution_status == "failed"])
        }

    def get_error_reports(self, limit: int = 50, 
                         category: Optional[str] = None,
                         severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取错误报告列表"""
        
        reports = self._error_reports.copy()
        
        # 按类别过滤
        if category:
            reports = [r for r in reports if r.error.category.value == category]
        
        # 按严重程度过滤
        if severity:
            reports = [r for r in reports if r.error.severity.value == severity]
        
        # 按时间倒序排序
        reports.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 限制数量
        reports = reports[:limit]
        
        return [r.to_dict() for r in reports]

    def clear_error_history(self):
        """清除错误历史"""
        self._error_reports.clear()
        self._error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recovery_success_rate": 0.0,
            "last_reset": datetime.now()
        }
        self._logger.info("错误历史已清除")

    def export_error_reports(self, file_path: str):
        """导出错误报告到文件"""
        data = {
            "statistics": self.get_error_statistics(),
            "reports": [r.to_dict() for r in self._error_reports],
            "exported_at": datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self._logger.info(f"错误报告已导出到: {file_path}")

    # 保持向后兼容性的方法
    def diagnose_error(self, error: Exception, instruction: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """诊断错误（向后兼容方法）"""
        if isinstance(error, BrowserAgentError):
            return self._diagnose_error(error, instruction, context)
        else:
            error_context = self._build_error_context(instruction, context)
            browser_error = create_error_from_exception(error, error_context)
            return self._diagnose_error(browser_error, instruction, context)

    def suggest_recovery(self, error_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """建议恢复方案（向后兼容方法）"""
        # 从诊断信息重建错误对象
        category_str = error_diagnosis.get("category", "unknown")
        try:
            category = ErrorCategory(category_str)
        except ValueError:
            category = ErrorCategory.UNKNOWN
        
        # 生成恢复建议
        if category in self._recovery_strategies:
            suggestions = []
            for action in self._recovery_strategies[category]:
                suggestions.append({
                    "action": action.action_type,
                    "description": action.description
                })
            return {"suggestions": suggestions}
        else:
            return {"suggestions": [
                {"action": "screenshot", "description": "截屏以辅助诊断"},
                {"action": "refresh", "description": "刷新并重试"}
            ]}


