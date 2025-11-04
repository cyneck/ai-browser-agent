#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理集成模块

提供统一的错误处理接口，集成异常处理框架、智能恢复管理器和用户反馈机制。
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from src.common.logger import get_logger, get_structured_logger
from src.common.exceptions import (
    BrowserAgentError, ErrorContext, ErrorCategory, ErrorSeverity,
    create_error_from_exception
)
from src.action.error_handler import ErrorHandler
from src.action.recovery_manager import get_recovery_manager


class IntegratedErrorHandler:
    """集成错误处理器
    
    统一管理错误处理、恢复计划和用户反馈的完整流程。
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.structured_logger = get_structured_logger()
        self.error_handler = ErrorHandler()
        self.recovery_manager = get_recovery_manager()
        
        # 错误处理统计
        self.stats = {
            "total_errors_handled": 0,
            "auto_recovered_errors": 0,
            "user_intervention_required": 0,
            "unrecoverable_errors": 0,
            "recovery_success_rate": 0.0
        }
    
    def handle_error_with_recovery(self, error: Exception, instruction: Dict[str, Any],
                                 context: Dict[str, Any], 
                                 executor_callback: Optional[Callable] = None,
                                 auto_recovery: bool = True) -> Dict[str, Any]:
        """处理错误并尝试自动恢复
        
        Args:
            error: 发生的异常
            instruction: 执行的指令
            context: 执行上下文
            executor_callback: 执行器回调函数，用于自动恢复
            auto_recovery: 是否启用自动恢复
            
        Returns:
            Dict[str, Any]: 处理结果，包含错误信息和恢复状态
        """
        
        self.stats["total_errors_handled"] += 1
        
        # 1. 基础错误处理
        error_result = self.error_handler.handle_error(error, instruction, context)
        
        # 2. 如果启用自动恢复且有恢复计划
        if auto_recovery and error_result.get("recovery_plan"):
            plan_id = error_result["recovery_plan"]["plan_id"]
            
            self.logger.info(f"开始自动恢复流程，计划ID: {plan_id}")
            
            # 执行恢复计划
            if executor_callback:
                recovery_result = self.error_handler.execute_recovery_plan(
                    plan_id, executor_callback
                )
                
                if recovery_result.get("success", False):
                    self.stats["auto_recovered_errors"] += 1
                    self.logger.info(f"自动恢复成功: {plan_id}")
                    
                    # 更新结果
                    error_result.update({
                        "auto_recovery_attempted": True,
                        "auto_recovery_success": True,
                        "recovery_result": recovery_result,
                        "final_status": "recovered"
                    })
                    
                    # 记录成功恢复的结构化日志
                    self.logger.info(
                        f"自动错误恢复成功 - 错误ID: {error_result['error_id']}, "
                        f"恢复计划ID: {plan_id}, "
                        f"策略: {recovery_result.get('strategy_used')}, "
                        f"尝试次数: {recovery_result.get('attempts', 0)}"
                    )
                    
                else:
                    self.stats["user_intervention_required"] += 1
                    self.logger.warning(f"自动恢复失败: {plan_id}")
                    
                    error_result.update({
                        "auto_recovery_attempted": True,
                        "auto_recovery_success": False,
                        "recovery_result": recovery_result,
                        "final_status": "requires_intervention"
                    })
            else:
                # 没有执行器回调，无法自动恢复
                error_result.update({
                    "auto_recovery_attempted": False,
                    "final_status": "manual_recovery_required",
                    "message": error_result["message"] + " (需要手动恢复)"
                })
        
        else:
            # 不可恢复的错误或未启用自动恢复
            if error_result.get("severity") == "critical":
                self.stats["unrecoverable_errors"] += 1
                error_result["final_status"] = "unrecoverable"
            else:
                error_result["final_status"] = "manual_recovery_available"
        
        # 更新恢复成功率
        if self.stats["total_errors_handled"] > 0:
            self.stats["recovery_success_rate"] = (
                self.stats["auto_recovered_errors"] / self.stats["total_errors_handled"]
            )
        
        return error_result
    
    def get_error_report(self, error_id: str) -> Optional[Dict[str, Any]]:
        """获取错误报告"""
        # 直接从错误处理器的内部报告列表查找
        for report in self.error_handler._error_reports:
            if report.error_id == error_id:
                return report.to_dict()
        return None
    
    def provide_user_feedback(self, error_id: str, feedback: str) -> Dict[str, Any]:
        """提供用户反馈"""
        try:
            # 查找错误报告
            for report in self.error_handler._error_reports:
                if report.error_id == error_id:
                    report.user_feedback = feedback
                    report.resolution_status = "user_feedback_provided"
                    
                    self.logger.info(f"收到用户反馈: {error_id}")
                    
                    return {
                        "success": True,
                        "message": "用户反馈已记录"
                    }
            
            return {
                "success": False,
                "message": f"未找到错误报告: {error_id}"
            }
            
        except Exception as e:
            self.logger.error(f"记录用户反馈失败: {e}")
            return {
                "success": False,
                "message": f"记录用户反馈失败: {e}"
            }
    
    def get_recovery_suggestions(self, error_id: str) -> List[Dict[str, Any]]:
        """获取恢复建议"""
        report = self.get_error_report(error_id)
        if report:
            return report.get("recovery_suggestions", [])
        return []
    
    def retry_with_suggestion(self, error_id: str, suggestion_index: int,
                            executor_callback: Callable) -> Dict[str, Any]:
        """使用建议重试操作"""
        
        suggestions = self.get_recovery_suggestions(error_id)
        if suggestion_index >= len(suggestions):
            return {
                "success": False,
                "message": "建议索引超出范围"
            }
        
        suggestion = suggestions[suggestion_index]
        
        try:
            # 如果是自动化建议，尝试执行
            if suggestion.get("automated", False):
                result = executor_callback(suggestion)
                
                # 记录重试结果
                self.logger.info(f"使用建议重试: {error_id}, 结果: {result.get('success', False)}")
                
                return result
            else:
                return {
                    "success": False,
                    "message": "该建议需要手动执行",
                    "suggestion": suggestion["description"]
                }
                
        except Exception as e:
            self.logger.error(f"重试失败: {e}")
            return {
                "success": False,
                "message": f"重试失败: {e}"
            }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误处理统计信息"""
        
        # 合并基础统计和恢复统计
        base_stats = self.error_handler.get_error_statistics()
        recovery_stats = self.recovery_manager.get_recovery_statistics()
        
        return {
            **base_stats,
            **recovery_stats,
            "integrated_stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_comprehensive_report(self, file_path: str):
        """导出综合错误报告"""
        
        data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "report_type": "comprehensive_error_report"
            },
            "statistics": self.get_error_statistics(),
            "error_reports": self.error_handler.get_error_reports(limit=1000),
            "recovery_plans": [
                plan.to_dict() for plan in self.recovery_manager.recovery_plans.values()
            ]
        }
        
        import json
        from datetime import datetime
        
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        self.logger.info(f"综合错误报告已导出: {file_path}")
    
    def clear_all_history(self):
        """清除所有错误历史"""
        self.error_handler.clear_error_history()
        self.recovery_manager.clear_recovery_history()
        
        self.stats = {
            "total_errors_handled": 0,
            "auto_recovered_errors": 0,
            "user_intervention_required": 0,
            "unrecoverable_errors": 0,
            "recovery_success_rate": 0.0
        }
        
        self.logger.info("所有错误处理历史已清除")


# 全局集成错误处理器实例
_integrated_error_handler = None


def get_integrated_error_handler() -> IntegratedErrorHandler:
    """获取全局集成错误处理器"""
    global _integrated_error_handler
    if _integrated_error_handler is None:
        _integrated_error_handler = IntegratedErrorHandler()
    return _integrated_error_handler


def handle_error_with_recovery(error: Exception, instruction: Dict[str, Any],
                             context: Dict[str, Any], 
                             executor_callback: Optional[Callable] = None,
                             auto_recovery: bool = True) -> Dict[str, Any]:
    """便捷函数：处理错误并尝试自动恢复"""
    handler = get_integrated_error_handler()
    return handler.handle_error_with_recovery(
        error, instruction, context, executor_callback, auto_recovery
    )