#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强日志模块

提供统一的日志记录功能，支持控制台和文件输出，包含详细的调试信息和性能监控。
"""

import logging
import logging.handlers
import os
import json
import traceback
import threading
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import inspect


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogCategory(Enum):
    """日志分类枚举"""
    SYSTEM = "system"
    PERFORMANCE = "performance"
    ERROR = "error"
    USER_ACTION = "user_action"
    BROWSER_ACTION = "browser_action"
    LLM_CALL = "llm_call"
    NETWORK = "network"
    DEBUG = "debug"
    SECURITY = "security"


@dataclass
class LogContext:
    """日志上下文信息"""
    session_id: Optional[str] = None
    operation_id: Optional[str] = None
    user_id: Optional[str] = None
    page_url: Optional[str] = None
    component: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[int] = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}
        
        # 自动获取调用信息
        if not self.function_name or not self.line_number:
            frame = inspect.currentframe()
            try:
                # 向上查找调用栈，跳过日志相关的帧
                caller_frame = frame.f_back.f_back.f_back
                if caller_frame:
                    self.function_name = caller_frame.f_code.co_name
                    self.line_number = caller_frame.f_lineno
            finally:
                del frame
        
        # 获取线程ID
        if not self.thread_id:
            self.thread_id = threading.get_ident()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DebugInfo:
    """调试信息收集器"""
    
    def __init__(self):
        self.enabled = False
        self.debug_data = {}
        self.screenshots = []
        self.page_sources = []
        self.network_logs = []
        self.console_logs = []
    
    def enable_debug_mode(self):
        """启用调试模式"""
        self.enabled = True
    
    def disable_debug_mode(self):
        """禁用调试模式"""
        self.enabled = False
    
    def add_screenshot(self, screenshot_path: str, description: str = ""):
        """添加截图信息"""
        if self.enabled:
            self.screenshots.append({
                "timestamp": datetime.now().isoformat(),
                "path": screenshot_path,
                "description": description
            })
    
    def add_page_source(self, source: str, url: str = ""):
        """添加页面源码"""
        if self.enabled:
            self.page_sources.append({
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "source": source[:10000]  # 限制长度
            })
    
    def add_network_log(self, request_info: Dict[str, Any]):
        """添加网络日志"""
        if self.enabled:
            self.network_logs.append({
                "timestamp": datetime.now().isoformat(),
                **request_info
            })
    
    def add_console_log(self, log_entry: Dict[str, Any]):
        """添加控制台日志"""
        if self.enabled:
            self.console_logs.append({
                "timestamp": datetime.now().isoformat(),
                **log_entry
            })
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """获取调试摘要"""
        return {
            "debug_enabled": self.enabled,
            "screenshots_count": len(self.screenshots),
            "page_sources_count": len(self.page_sources),
            "network_logs_count": len(self.network_logs),
            "console_logs_count": len(self.console_logs),
            "debug_data": self.debug_data
        }
    
    def export_debug_info(self, file_path: str):
        """导出调试信息"""
        debug_info = {
            "export_time": datetime.now().isoformat(),
            "screenshots": self.screenshots,
            "page_sources": self.page_sources,
            "network_logs": self.network_logs,
            "console_logs": self.console_logs,
            "debug_data": self.debug_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)
    
    def clear(self):
        """清除调试信息"""
        self.debug_data.clear()
        self.screenshots.clear()
        self.page_sources.clear()
        self.network_logs.clear()
        self.console_logs.clear()


class EnhancedFormatter(logging.Formatter):
    """增强的日志格式化器"""
    
    def __init__(self, include_context: bool = True, include_stack: bool = False):
        self.include_context = include_context
        self.include_stack = include_stack
        
        # 基础格式
        base_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        super().__init__(base_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    def format(self, record: logging.LogRecord) -> str:
        # 基础格式化
        formatted = super().format(record)
        
        # 添加上下文信息
        if self.include_context and hasattr(record, 'context'):
            context = record.context
            if isinstance(context, LogContext):
                context_str = self._format_context(context)
                formatted += f" | {context_str}"
        
        # 添加堆栈信息
        if self.include_stack and record.levelno >= logging.ERROR:
            if record.exc_info:
                formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted
    
    def _format_context(self, context: LogContext) -> str:
        """格式化上下文信息"""
        parts = []
        
        if context.session_id:
            parts.append(f"session:{context.session_id[:8]}")
        
        if context.operation_id:
            parts.append(f"op:{context.operation_id}")
        
        if context.component:
            parts.append(f"comp:{context.component}")
        
        if context.function_name:
            parts.append(f"func:{context.function_name}")
        
        if context.page_url:
            parts.append(f"url:{context.page_url[:50]}")
        
        return " | ".join(parts)


class StructuredLogger:
    """增强的结构化日志记录器"""
    
    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self.logger = logger
        self.debug_info = DebugInfo()
        self._context_stack = []
    
    def push_context(self, context: LogContext):
        """推入上下文"""
        self._context_stack.append(context)
    
    def pop_context(self) -> Optional[LogContext]:
        """弹出上下文"""
        return self._context_stack.pop() if self._context_stack else None
    
    def get_current_context(self) -> Optional[LogContext]:
        """获取当前上下文"""
        return self._context_stack[-1] if self._context_stack else None
    
    def log_structured(self, level: int, category: LogCategory, 
                      message: str, data: Dict[str, Any] = None,
                      context: LogContext = None, **kwargs):
        """记录结构化日志"""
        
        # 使用当前上下文或提供的上下文
        if context is None:
            context = self.get_current_context() or LogContext()
        
        # 构建日志条目
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": logging.getLevelName(level),
            "category": category.value,
            "message": message,
            "logger_name": self.name,
            "context": context.to_dict(),
            "data": data or {},
            **kwargs
        }
        
        # 创建日志记录
        record = logging.LogRecord(
            name=self.logger.name,
            level=level,
            pathname="",
            lineno=0,
            msg=json.dumps(log_entry, ensure_ascii=False),
            args=(),
            exc_info=None
        )
        record.context = context
        
        self.logger.handle(record)
    
    def debug(self, message: str, data: Dict[str, Any] = None, 
             context: LogContext = None, **kwargs):
        """记录调试日志"""
        self.log_structured(logging.DEBUG, LogCategory.DEBUG, message, data, context, **kwargs)
    
    def info(self, message: str, data: Dict[str, Any] = None,
            context: LogContext = None, **kwargs):
        """记录信息日志"""
        self.log_structured(logging.INFO, LogCategory.SYSTEM, message, data, context, **kwargs)
    
    def warning(self, message: str, data: Dict[str, Any] = None,
               context: LogContext = None, **kwargs):
        """记录警告日志"""
        self.log_structured(logging.WARNING, LogCategory.SYSTEM, message, data, context, **kwargs)
    
    def error(self, message: str, data: Dict[str, Any] = None,
             context: LogContext = None, error: Exception = None, **kwargs):
        """记录错误日志"""
        if error:
            data = data or {}
            data.update({
                "error_type": error.__class__.__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        
        self.log_structured(logging.ERROR, LogCategory.ERROR, message, data, context, **kwargs)
    
    def critical(self, message: str, data: Dict[str, Any] = None,
                context: LogContext = None, **kwargs):
        """记录严重错误日志"""
        self.log_structured(logging.CRITICAL, LogCategory.ERROR, message, data, context, **kwargs)
    
    # 特定类别的日志方法
    def log_performance(self, level: int, event_type: str, 
                       data: Dict[str, Any], context: LogContext = None, **kwargs):
        """记录性能日志"""
        self.log_structured(level, LogCategory.PERFORMANCE, event_type, data, context, **kwargs)
    
    def log_user_action(self, action: str, data: Dict[str, Any] = None,
                       context: LogContext = None, **kwargs):
        """记录用户动作日志"""
        self.log_structured(logging.INFO, LogCategory.USER_ACTION, action, data, context, **kwargs)
    
    def log_browser_action(self, action: str, data: Dict[str, Any] = None,
                          context: LogContext = None, **kwargs):
        """记录浏览器动作日志"""
        self.log_structured(logging.INFO, LogCategory.BROWSER_ACTION, action, data, context, **kwargs)
    
    def log_llm_call(self, provider: str, model: str, data: Dict[str, Any] = None,
                    context: LogContext = None, **kwargs):
        """记录LLM调用日志"""
        message = f"LLM调用: {provider}/{model}"
        self.log_structured(logging.INFO, LogCategory.LLM_CALL, message, data, context, **kwargs)
    
    def log_network_request(self, method: str, url: str, data: Dict[str, Any] = None,
                           context: LogContext = None, **kwargs):
        """记录网络请求日志"""
        message = f"网络请求: {method} {url}"
        self.log_structured(logging.INFO, LogCategory.NETWORK, message, data, context, **kwargs)
    
    def log_security_event(self, event: str, data: Dict[str, Any] = None,
                          context: LogContext = None, **kwargs):
        """记录安全事件日志"""
        self.log_structured(logging.WARNING, LogCategory.SECURITY, event, data, context, **kwargs)
    
    # 调试相关方法
    def enable_debug_mode(self):
        """启用调试模式"""
        self.debug_info.enable_debug_mode()
        self.info("调试模式已启用")
    
    def disable_debug_mode(self):
        """禁用调试模式"""
        self.debug_info.disable_debug_mode()
        self.info("调试模式已禁用")
    
    def add_debug_screenshot(self, screenshot_path: str, description: str = ""):
        """添加调试截图"""
        self.debug_info.add_screenshot(screenshot_path, description)
        self.debug(f"添加调试截图: {description}", {"path": screenshot_path})
    
    def add_debug_page_source(self, source: str, url: str = ""):
        """添加调试页面源码"""
        self.debug_info.add_page_source(source, url)
        self.debug(f"添加页面源码: {url}")
    
    def export_debug_info(self, file_path: str):
        """导出调试信息"""
        self.debug_info.export_debug_info(file_path)
        self.info(f"调试信息已导出: {file_path}")
    
    # 向后兼容的方法
    def info_performance(self, event_type: str, data: Dict[str, Any], **kwargs):
        """记录性能信息日志（向后兼容）"""
        self.log_performance(logging.INFO, event_type, data, **kwargs)
    
    def warning_performance(self, event_type: str, data: Dict[str, Any], **kwargs):
        """记录性能警告日志（向后兼容）"""
        self.log_performance(logging.WARNING, event_type, data, **kwargs)
    
    def error_performance(self, event_type: str, data: Dict[str, Any], **kwargs):
        """记录性能错误日志（向后兼容）"""
        self.log_performance(logging.ERROR, event_type, data, **kwargs)


def setup_logger(level: int = logging.INFO, log_file: Optional[str] = None,
                enable_debug: bool = False, max_file_size: int = 10*1024*1024,
                backup_count: int = 5) -> logging.Logger:
    """
    设置增强的日志记录器
    
    Args:
        level: 日志级别，默认为INFO
        log_file: 日志文件路径，如果为None则只输出到控制台
        enable_debug: 是否启用调试模式
        max_file_size: 日志文件最大大小（字节）
        backup_count: 备份文件数量
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger("ai_browser_agent")
    logger.setLevel(level)
    
    # 清除已有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 设置控制台格式化器
    console_formatter = EnhancedFormatter(
        include_context=enable_debug,
        include_stack=enable_debug
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加控制台处理器
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # 设置文件格式化器
        file_formatter = EnhancedFormatter(
            include_context=True,
            include_stack=True
        )
        file_handler.setFormatter(file_formatter)
        
        # 添加文件处理器
        logger.addHandler(file_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """
    获取日志记录器
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    return logging.getLogger("ai_browser_agent")


def get_structured_logger(name: str = "ai_browser_agent") -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name, get_logger())
        