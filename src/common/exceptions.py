#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一异常处理框架

定义项目特定的异常类型层次结构，提供分层异常处理机制和异常上下文信息收集系统。
"""

from __future__ import annotations

import traceback
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误分类枚举"""
    BROWSER = "browser"
    NETWORK = "network"
    PARSING = "parsing"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    LLM = "llm"
    PLUGIN = "plugin"
    UNKNOWN = "unknown"


class ErrorContext:
    """错误上下文信息收集器"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.operation_id: Optional[str] = None
        self.user_input: Optional[str] = None
        self.page_url: Optional[str] = None
        self.page_title: Optional[str] = None
        self.instruction: Optional[Dict[str, Any]] = None
        self.browser_state: Optional[Dict[str, Any]] = None
        self.system_state: Optional[Dict[str, Any]] = None
        self.session_id: Optional[str] = None
        self.additional_data: Dict[str, Any] = {}
    
    def set_operation_context(self, operation_id: str, user_input: str = None):
        """设置操作上下文"""
        self.operation_id = operation_id
        self.user_input = user_input
    
    def set_page_context(self, url: str = None, title: str = None):
        """设置页面上下文"""
        self.page_url = url
        self.page_title = title
    
    def set_instruction_context(self, instruction: Dict[str, Any]):
        """设置指令上下文"""
        self.instruction = instruction
    
    def set_browser_state(self, state: Dict[str, Any]):
        """设置浏览器状态"""
        self.browser_state = state
    
    def set_system_state(self, state: Dict[str, Any]):
        """设置系统状态"""
        self.system_state = state
    
    def add_data(self, key: str, value: Any):
        """添加额外数据"""
        self.additional_data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation_id": self.operation_id,
            "user_input": self.user_input,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "instruction": self.instruction,
            "browser_state": self.browser_state,
            "system_state": self.system_state,
            "session_id": self.session_id,
            "additional_data": self.additional_data
        }


class BrowserAgentError(Exception):
    """浏览器代理基础异常类"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[ErrorContext] = None,
                 original_error: Optional[Exception] = None,
                 recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.original_error = original_error
        self.recovery_suggestions = recovery_suggestions or []
        self.traceback_str = traceback.format_exc() if original_error else None
        self.timestamp = datetime.now()
    
    def add_recovery_suggestion(self, suggestion: str):
        """添加恢复建议"""
        self.recovery_suggestions.append(suggestion)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于日志记录和API响应"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict(),
            "original_error": str(self.original_error) if self.original_error else None,
            "recovery_suggestions": self.recovery_suggestions,
            "traceback": self.traceback_str
        }


# 感知层异常
class PerceptionError(BrowserAgentError):
    """感知层异常基类"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.PARSING, **kwargs)


class PageAnalysisError(PerceptionError):
    """页面分析异常"""
    pass


class ElementNotFoundError(BrowserAgentError):
    """元素未找到异常"""
    
    def __init__(self, selector: str, **kwargs):
        message = f"无法找到元素: {selector}"
        super().__init__(message, category=ErrorCategory.BROWSER, **kwargs)
        self.selector = selector
        self.add_recovery_suggestion("尝试等待元素加载")
        self.add_recovery_suggestion("检查选择器是否正确")
        self.add_recovery_suggestion("滚动页面以触发懒加载")


class PageLoadError(PerceptionError):
    """页面加载异常"""
    
    def __init__(self, url: str, **kwargs):
        message = f"页面加载失败: {url}"
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)
        self.url = url
        self.add_recovery_suggestion("检查网络连接")
        self.add_recovery_suggestion("重试页面加载")
        self.add_recovery_suggestion("检查URL是否正确")


# 推理层异常
class ReasoningError(BrowserAgentError):
    """推理层异常基类"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.LLM, **kwargs)


class IntentClassificationError(ReasoningError):
    """意图分类异常"""
    
    def __init__(self, user_input: str, **kwargs):
        message = f"无法识别用户意图: {user_input}"
        super().__init__(message, **kwargs)
        self.user_input = user_input
        self.add_recovery_suggestion("请提供更明确的指令")
        self.add_recovery_suggestion("尝试使用不同的表达方式")


class InstructionBuildError(ReasoningError):
    """指令构建异常"""
    
    def __init__(self, intent: str, **kwargs):
        message = f"无法构建执行指令: {intent}"
        super().__init__(message, **kwargs)
        self.intent = intent
        self.add_recovery_suggestion("检查页面状态是否正确")
        self.add_recovery_suggestion("尝试简化操作步骤")


class LLMError(ReasoningError):
    """LLM调用异常"""
    
    def __init__(self, provider: str, model: str, **kwargs):
        message = f"LLM调用失败: {provider}/{model}"
        super().__init__(message, **kwargs)
        self.provider = provider
        self.model = model
        self.add_recovery_suggestion("检查API密钥配置")
        self.add_recovery_suggestion("检查网络连接")
        self.add_recovery_suggestion("尝试使用备用模型")


# 执行层异常
class ActionError(BrowserAgentError):
    """执行层异常基类"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.BROWSER, **kwargs)


class ActionExecutionError(ActionError):
    """动作执行异常"""
    
    def __init__(self, action: str, **kwargs):
        message = f"动作执行失败: {action}"
        super().__init__(message, **kwargs)
        self.action = action


class ElementNotInteractableError(ActionError):
    """元素不可交互异常"""
    
    def __init__(self, selector: str, **kwargs):
        message = f"元素不可交互: {selector}"
        super().__init__(message, **kwargs)
        self.selector = selector
        self.add_recovery_suggestion("等待元素变为可交互状态")
        self.add_recovery_suggestion("滚动到元素位置")
        self.add_recovery_suggestion("检查元素是否被其他元素遮挡")


class TimeoutError(BrowserAgentError):
    """超时异常"""
    
    def __init__(self, operation: str, timeout: float, **kwargs):
        message = f"操作超时: {operation} (超时时间: {timeout}s)"
        super().__init__(message, category=ErrorCategory.TIMEOUT, **kwargs)
        self.operation = operation
        self.timeout = timeout
        self.add_recovery_suggestion("增加超时时间")
        self.add_recovery_suggestion("检查网络连接")
        self.add_recovery_suggestion("等待页面完全加载")


class SafetyValidationError(ActionError):
    """安全验证异常"""
    
    def __init__(self, validation_type: str, **kwargs):
        message = f"安全验证失败: {validation_type}"
        super().__init__(message, category=ErrorCategory.VALIDATION, 
                        severity=ErrorSeverity.HIGH, **kwargs)
        self.validation_type = validation_type
        self.add_recovery_suggestion("检查输入参数的安全性")
        self.add_recovery_suggestion("使用更安全的操作方式")


# 配置和系统异常
class ConfigurationError(BrowserAgentError):
    """配置异常"""
    
    def __init__(self, config_key: str, **kwargs):
        message = f"配置错误: {config_key}"
        super().__init__(message, category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.HIGH, **kwargs)
        self.config_key = config_key
        self.add_recovery_suggestion("检查配置文件")
        self.add_recovery_suggestion("验证环境变量设置")


class PermissionError(BrowserAgentError):
    """权限异常"""
    
    def __init__(self, resource: str, **kwargs):
        message = f"权限不足: {resource}"
        super().__init__(message, category=ErrorCategory.PERMISSION,
                        severity=ErrorSeverity.HIGH, **kwargs)
        self.resource = resource
        self.add_recovery_suggestion("检查文件/目录权限")
        self.add_recovery_suggestion("以管理员权限运行")


class PluginError(BrowserAgentError):
    """插件异常"""
    
    def __init__(self, plugin_name: str, **kwargs):
        message = f"插件错误: {plugin_name}"
        super().__init__(message, category=ErrorCategory.PLUGIN, **kwargs)
        self.plugin_name = plugin_name
        self.add_recovery_suggestion("检查插件配置")
        self.add_recovery_suggestion("尝试禁用插件")
        self.add_recovery_suggestion("更新插件版本")


# 网络相关异常
class NetworkError(BrowserAgentError):
    """网络异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)
        self.add_recovery_suggestion("检查网络连接")
        self.add_recovery_suggestion("检查代理设置")
        self.add_recovery_suggestion("重试操作")


class APIError(NetworkError):
    """API调用异常"""
    
    def __init__(self, api_name: str, status_code: Optional[int] = None, **kwargs):
        message = f"API调用失败: {api_name}"
        if status_code:
            message += f" (状态码: {status_code})"
        super().__init__(message, **kwargs)
        self.api_name = api_name
        self.status_code = status_code


# 异常工厂函数
def create_error_from_exception(exc: Exception, context: Optional[ErrorContext] = None) -> BrowserAgentError:
    """从标准异常创建项目特定异常"""
    
    # 如果已经是项目异常，直接返回
    if isinstance(exc, BrowserAgentError):
        return exc
    
    exc_str = str(exc).lower()
    exc_type = type(exc).__name__
    
    # 根据异常类型和消息内容判断异常类别
    if "timeout" in exc_str or "timed out" in exc_str:
        return TimeoutError("操作超时", original_error=exc, context=context)
    
    elif "not found" in exc_str or "no such" in exc_str or "locator" in exc_str:
        # 尝试提取选择器信息
        selector = "unknown"
        if hasattr(exc, 'selector'):
            selector = exc.selector
        return ElementNotFoundError(selector, original_error=exc, context=context)
    
    elif "not visible" in exc_str or "not interactable" in exc_str:
        selector = "unknown"
        if hasattr(exc, 'selector'):
            selector = exc.selector
        return ElementNotInteractableError(selector, original_error=exc, context=context)
    
    elif "network" in exc_str or "connection" in exc_str:
        return NetworkError(str(exc), original_error=exc, context=context)
    
    elif "permission" in exc_str or "access denied" in exc_str:
        return PermissionError("unknown", original_error=exc, context=context)
    
    elif "config" in exc_str or "configuration" in exc_str:
        return ConfigurationError("unknown", original_error=exc, context=context)
    
    else:
        # 默认创建通用异常
        return BrowserAgentError(
            str(exc), 
            original_error=exc, 
            context=context,
            category=ErrorCategory.UNKNOWN
        )


def get_error_category_from_string(error_str: str) -> ErrorCategory:
    """从错误字符串推断错误类别"""
    error_str = error_str.lower()
    
    if any(keyword in error_str for keyword in ["timeout", "timed out", "超时"]):
        return ErrorCategory.TIMEOUT
    elif any(keyword in error_str for keyword in ["not found", "locator", "selector", "元素"]):
        return ErrorCategory.BROWSER
    elif any(keyword in error_str for keyword in ["network", "connection", "网络", "连接"]):
        return ErrorCategory.NETWORK
    elif any(keyword in error_str for keyword in ["permission", "access", "权限"]):
        return ErrorCategory.PERMISSION
    elif any(keyword in error_str for keyword in ["config", "configuration", "配置"]):
        return ErrorCategory.CONFIGURATION
    elif any(keyword in error_str for keyword in ["llm", "api", "model"]):
        return ErrorCategory.LLM
    elif any(keyword in error_str for keyword in ["plugin", "插件"]):
        return ErrorCategory.PLUGIN
    elif any(keyword in error_str for keyword in ["parse", "parsing", "解析"]):
        return ErrorCategory.PARSING
    elif any(keyword in error_str for keyword in ["validation", "validate", "验证"]):
        return ErrorCategory.VALIDATION
    else:
        return ErrorCategory.UNKNOWN