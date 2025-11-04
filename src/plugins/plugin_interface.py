#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件接口定义

定义了插件系统的核心接口和生命周期管理。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
import time

from src.common.logger import get_logger


class PluginState(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNLOADING = "unloading"


class PluginType(Enum):
    """插件类型枚举"""
    WEBSITE = "website"          # 网站特定插件
    ACTION = "action"            # 动作扩展插件
    PROCESSOR = "processor"      # 数据处理插件
    INTEGRATION = "integration"  # 第三方集成插件
    UTILITY = "utility"          # 工具类插件


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    supported_actions: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    min_agent_version: str = "1.0.0"
    max_agent_version: str = "*"
    enabled: bool = True
    priority: int = 100  # 优先级，数值越小优先级越高


@dataclass
class PluginPerformanceMetrics:
    """插件性能指标"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_execution_time: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


class PluginContext:
    """插件执行上下文"""
    
    def __init__(self, session_state: Dict[str, Any], page_data: Dict[str, Any] = None):
        self.session_state = session_state
        self.page_data = page_data or {}
        self.execution_id = f"exec_{int(time.time() * 1000)}"
        self.start_time = datetime.now()
        self.logger = get_logger()
        self._data = {}
    
    def get_data(self, key: str, default=None):
        """获取上下文数据"""
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any):
        """设置上下文数据"""
        self._data[key] = value
    
    def log_info(self, message: str):
        """记录信息日志"""
        self.logger.info(f"[{self.execution_id}] {message}")
    
    def log_error(self, message: str):
        """记录错误日志"""
        self.logger.error(f"[{self.execution_id}] {message}")


class PluginInterface(ABC):
    """插件接口基类"""
    
    def __init__(self):
        """初始化插件"""
        self.logger = get_logger()
        self.state = PluginState.UNLOADED
        self.config = {}
        self.metrics = PluginPerformanceMetrics()
        self._lock = threading.RLock()
        self._hooks = {
            'before_execute': [],
            'after_execute': [],
            'on_error': [],
            'on_config_change': []
        }
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            with self._lock:
                if self.state != PluginState.UNLOADED:
                    self.logger.warning(f"插件 {self.metadata.name} 已经初始化")
                    return True
                
                self.state = PluginState.LOADING
                self.config = config or {}
                
                # 验证配置
                if not self._validate_config(self.config):
                    self.state = PluginState.ERROR
                    return False
                
                # 执行插件特定的初始化
                if not self._on_initialize():
                    self.state = PluginState.ERROR
                    return False
                
                self.state = PluginState.LOADED
                self.logger.info(f"插件 {self.metadata.name} 初始化成功")
                return True
                
        except Exception as e:
            self.state = PluginState.ERROR
            self.logger.error(f"插件 {self.metadata.name} 初始化失败: {str(e)}")
            return False
    
    def activate(self) -> bool:
        """激活插件"""
        try:
            with self._lock:
                if self.state != PluginState.LOADED:
                    self.logger.warning(f"插件 {self.metadata.name} 状态不正确，无法激活")
                    return False
                
                if self._on_activate():
                    self.state = PluginState.ACTIVE
                    self.logger.info(f"插件 {self.metadata.name} 已激活")
                    return True
                else:
                    self.state = PluginState.ERROR
                    return False
                    
        except Exception as e:
            self.state = PluginState.ERROR
            self.logger.error(f"插件 {self.metadata.name} 激活失败: {str(e)}")
            return False
    
    def deactivate(self) -> bool:
        """停用插件"""
        try:
            with self._lock:
                if self.state != PluginState.ACTIVE:
                    return True
                
                if self._on_deactivate():
                    self.state = PluginState.INACTIVE
                    self.logger.info(f"插件 {self.metadata.name} 已停用")
                    return True
                else:
                    return False
                    
        except Exception as e:
            self.logger.error(f"插件 {self.metadata.name} 停用失败: {str(e)}")
            return False
    
    def shutdown(self) -> bool:
        """关闭插件"""
        try:
            with self._lock:
                if self.state == PluginState.UNLOADED:
                    return True
                
                self.state = PluginState.UNLOADING
                
                if self._on_shutdown():
                    self.state = PluginState.UNLOADED
                    self.logger.info(f"插件 {self.metadata.name} 已关闭")
                    return True
                else:
                    self.state = PluginState.ERROR
                    return False
                    
        except Exception as e:
            self.state = PluginState.ERROR
            self.logger.error(f"插件 {self.metadata.name} 关闭失败: {str(e)}")
            return False
    
    def execute(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件功能
        
        Args:
            instruction: 标准化的JSON格式指令
            context: 插件执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if self.state != PluginState.ACTIVE:
            return {
                "success": False,
                "message": f"插件 {self.metadata.name} 未激活",
                "error": f"插件状态: {self.state.value}"
            }
        
        start_time = time.time()
        
        try:
            # 执行前置钩子
            self._execute_hooks('before_execute', instruction, context)
            
            # 更新指标
            with self._lock:
                self.metrics.total_executions += 1
                self.metrics.last_execution_time = datetime.now()
            
            # 执行插件逻辑
            result = self._execute_internal(instruction, context)
            
            # 更新成功指标
            execution_time = time.time() - start_time
            with self._lock:
                self.metrics.successful_executions += 1
                self.metrics.total_execution_time += execution_time
                self.metrics.average_execution_time = (
                    self.metrics.total_execution_time / self.metrics.total_executions
                )
            
            # 执行后置钩子
            self._execute_hooks('after_execute', instruction, context, result)
            
            return result
            
        except Exception as e:
            # 更新失败指标
            execution_time = time.time() - start_time
            with self._lock:
                self.metrics.failed_executions += 1
                self.metrics.total_execution_time += execution_time
                self.metrics.average_execution_time = (
                    self.metrics.total_execution_time / self.metrics.total_executions
                )
                self.metrics.last_error = str(e)
                self.metrics.last_error_time = datetime.now()
            
            # 执行错误钩子
            self._execute_hooks('on_error', instruction, context, e)
            
            context.log_error(f"插件执行失败: {str(e)}")
            
            return {
                "success": False,
                "message": f"插件 {self.metadata.name} 执行失败",
                "error": str(e)
            }
    
    def can_handle(self, instruction: Dict[str, Any]) -> bool:
        """判断插件是否可以处理指定指令
        
        Args:
            instruction: 标准化的JSON格式指令
            
        Returns:
            bool: 是否可以处理
        """
        if self.state != PluginState.ACTIVE:
            return False
        
        action = instruction.get("action")
        return action in self.metadata.supported_actions
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """更新插件配置
        
        Args:
            config: 新的配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not self._validate_config(config):
                return False
            
            old_config = self.config.copy()
            self.config.update(config)
            
            # 执行配置变更钩子
            self._execute_hooks('on_config_change', old_config, self.config)
            
            self.logger.info(f"插件 {self.metadata.name} 配置已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"插件 {self.metadata.name} 配置更新失败: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件状态信息"""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "state": self.state.value,
            "type": self.metadata.plugin_type.value,
            "enabled": self.metadata.enabled,
            "metrics": {
                "total_executions": self.metrics.total_executions,
                "successful_executions": self.metrics.successful_executions,
                "failed_executions": self.metrics.failed_executions,
                "success_rate": (
                    self.metrics.successful_executions / self.metrics.total_executions
                    if self.metrics.total_executions > 0 else 0
                ),
                "average_execution_time": self.metrics.average_execution_time,
                "last_execution_time": (
                    self.metrics.last_execution_time.isoformat()
                    if self.metrics.last_execution_time else None
                ),
                "last_error": self.metrics.last_error,
                "last_error_time": (
                    self.metrics.last_error_time.isoformat()
                    if self.metrics.last_error_time else None
                )
            }
        }
    
    def add_hook(self, event: str, callback: Callable):
        """添加钩子函数
        
        Args:
            event: 事件名称 ('before_execute', 'after_execute', 'on_error', 'on_config_change')
            callback: 回调函数
        """
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def remove_hook(self, event: str, callback: Callable):
        """移除钩子函数"""
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
    
    # 抽象方法，子类需要实现
    @abstractmethod
    def _execute_internal(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件内部逻辑"""
        pass
    
    # 生命周期钩子方法，子类可以重写
    def _on_initialize(self) -> bool:
        """插件初始化时调用"""
        return True
    
    def _on_activate(self) -> bool:
        """插件激活时调用"""
        return True
    
    def _on_deactivate(self) -> bool:
        """插件停用时调用"""
        return True
    
    def _on_shutdown(self) -> bool:
        """插件关闭时调用"""
        return True
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 基础验证，子类可以重写
        return True
    
    def _execute_hooks(self, event: str, *args, **kwargs):
        """执行钩子函数"""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"钩子函数执行失败: {str(e)}")