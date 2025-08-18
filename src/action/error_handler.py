#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理器

负责统一封装动作执行过程中的异常、诊断原因并给出恢复建议。
"""

from __future__ import annotations

from typing import Any, Dict

from src.common.logger import get_logger


class ErrorHandler:
    """基础错误处理器实现"""

    def __init__(self):
        self._logger = get_logger()

    def handle_error(self, error: Exception, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        diagnosis = self.diagnose_error(error, instruction, context)
        recovery = self.suggest_recovery(diagnosis)
        result = {
            "success": False,
            "message": "执行失败",
            "error": str(error),
            "diagnosis": diagnosis,
            "recovery": recovery,
        }
        self._logger.error(f"执行错误: {error}")
        return result

    def diagnose_error(self, error: Exception, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        error_str = str(error).lower()
        action = instruction.get("action")
        probable_cause = "unknown"
        if any(k in error_str for k in ["timeout", "timed out", "超时"]):
            probable_cause = "timeout"
        elif any(k in error_str for k in ["no such", "not found", "locator", "selector"]):
            probable_cause = "selector_not_found"
        elif "visible" in error_str or "not visible" in error_str:
            probable_cause = "element_not_visible"
        return {
            "action": action,
            "probable_cause": probable_cause,
            "error": str(error),
        }

    def suggest_recovery(self, error_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        cause = error_diagnosis.get("probable_cause", "unknown")
        suggestions = []
        if cause == "timeout":
            suggestions = [
                {"action": "wait", "description": "增加等待时间或等待元素出现"},
                {"action": "refresh", "description": "刷新页面后重试"},
            ]
        elif cause == "selector_not_found":
            suggestions = [
                {"action": "wait", "description": "等待元素渲染"},
                {"action": "scroll", "description": "滚动以触发懒加载"},
                {"action": "extract", "description": "调整选择器策略（css/role/text/xpath）"},
            ]
        elif cause == "element_not_visible":
            suggestions = [
                {"action": "scroll", "description": "滚动到元素位置"},
                {"action": "wait", "description": "等待元素可见"},
            ]
        else:
            suggestions = [
                {"action": "screenshot", "description": "截屏以辅助诊断"},
                {"action": "refresh", "description": "刷新并重试"},
            ]
        return {"suggestions": suggestions}


