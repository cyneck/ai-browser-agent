#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件管理器

负责加载、管理和执行插件。
"""

import importlib
import importlib.util
import inspect
import os
import pkgutil
import json
import threading
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Type
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import weakref

from src.common.logger import get_logger
from src.plugins.base_website_plugin import BaseWebsitePlugin
from src.plugins.plugin_interface import (
    PluginInterface, PluginState, PluginType, PluginMetadata, 
    PluginContext, PluginPerformanceMetrics
)


class PluginPerformanceMonitor:
    """插件性能监控器"""
    
    def __init__(self):
        self.logger = get_logger()
        self._metrics: Dict[str, PluginPerformanceMetrics] = {}
        self._lock = threading.RLock()
        
    def start_execution(self, plugin_name: str) -> str:
        """开始执行监控"""
        execution_id = f"{plugin_name}_{int(time.time() * 1000)}"
        return execution_id
    
    def end_execution(self, plugin_name: str, execution_id: str, success: bool, error: str = None):
        """结束执行监控"""
        with self._lock:
            if plugin_name not in self._metrics:
                self._metrics[plugin_name] = PluginPerformanceMetrics()
            
            metrics = self._metrics[plugin_name]
            metrics.total_executions += 1
            
            if success:
                metrics.successful_executions += 1
            else:
                metrics.failed_executions += 1
                metrics.last_error = error
                metrics.last_error_time = datetime.now()
            
            metrics.last_execution_time = datetime.now()
    
    def get_metrics(self, plugin_name: str = None) -> Union[PluginPerformanceMetrics, Dict[str, PluginPerformanceMetrics]]:
        """获取性能指标"""
        with self._lock:
            if plugin_name:
                return self._metrics.get(plugin_name, PluginPerformanceMetrics())
            return self._metrics.copy()
    
    def reset_metrics(self, plugin_name: str = None):
        """重置性能指标"""
        with self._lock:
            if plugin_name:
                if plugin_name in self._metrics:
                    self._metrics[plugin_name] = PluginPerformanceMetrics()
            else:
                self._metrics.clear()


class PluginErrorHandler:
    """插件错误处理器"""
    
    def __init__(self, max_errors: int = 100):
        self.logger = get_logger()
        self.max_errors = max_errors
        self._errors: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
    def handle_error(self, plugin_name: str, error: Exception, context: Dict[str, Any] = None):
        """处理插件错误"""
        error_info = {
            'plugin_name': plugin_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        with self._lock:
            self._errors.append(error_info)
            # 保持错误列表大小
            if len(self._errors) > self.max_errors:
                self._errors.pop(0)
        
        self.logger.error(f"插件 {plugin_name} 发生错误: {error_info['error_message']}")
        
        return error_info
    
    def get_errors(self, plugin_name: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """获取错误记录"""
        with self._lock:
            errors = self._errors.copy()
            
            if plugin_name:
                errors = [e for e in errors if e['plugin_name'] == plugin_name]
            
            if limit:
                errors = errors[-limit:]
            
            return errors
    
    def clear_errors(self, plugin_name: str = None):
        """清除错误记录"""
        with self._lock:
            if plugin_name:
                self._errors = [e for e in self._errors if e['plugin_name'] != plugin_name]
            else:
                self._errors.clear()


class Plugin:
    """插件基类"""
    
    # 插件名称
    name = "base_plugin"
    
    # 插件描述
    description = "基础插件类"
    
    # 插件版本
    version = "0.1.0"
    
    # 插件作者
    author = "Unknown"
    
    # 插件支持的指令类型
    supported_actions = []
    
    def __init__(self):
        """初始化插件"""
        self.logger = get_logger()
    
    def execute(self, instruction: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件功能
        
        Args:
            instruction: 标准化的JSON格式指令
            session_state: 会话状态
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        raise NotImplementedError("插件必须实现execute方法")
    
    def can_handle(self, instruction: Dict[str, Any]) -> bool:
        """判断插件是否可以处理指定指令
        
        Args:
            instruction: 标准化的JSON格式指令
            
        Returns:
            bool: 是否可以处理
        """
        action = instruction.get("action")
        return action in self.supported_actions


class EnhancedPluginManager:
    """增强的插件管理器类"""
    
    def __init__(self, plugin_dir: Optional[str] = None, config_file: Optional[str] = None):
        """初始化插件管理器
        
        Args:
            plugin_dir: 插件目录路径，默认为当前文件所在目录
            config_file: 插件配置文件路径
        """
        self.logger = get_logger()
        self._lock = threading.RLock()
        
        # 设置插件目录
        if plugin_dir is None:
            self.plugin_dir = Path(__file__).parent
        else:
            self.plugin_dir = Path(plugin_dir)
        
        # 配置文件路径
        self.config_file = config_file or (self.plugin_dir / "plugin_config.json")
        
        # 插件存储
        self.plugins: Dict[str, PluginInterface] = {}  # 新式插件
        self.legacy_plugins: Dict[str, Plugin] = {}    # 旧式插件（兼容性）
        self.website_plugins: List[BaseWebsitePlugin] = []  # 网站插件
        
        # 插件配置
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # 插件依赖图
        self.dependency_graph: Dict[str, List[str]] = {}
        
        # 搜索引擎优先级配置
        self.search_engine_priority = ["google", "bing", "baidu"]
        
        # 动态加载相关
        self._loaded_modules: Dict[str, Any] = {}  # 已加载的模块
        self._plugin_files: Dict[str, Path] = {}   # 插件文件路径映射
        self._file_watchers: Dict[str, float] = {} # 文件修改时间监控
        
        # 性能监控
        self._performance_monitor = PluginPerformanceMonitor()
        self._error_handler = PluginErrorHandler()
        
        # 线程池用于异步操作
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="plugin_")
        
        # 插件生命周期回调
        self._lifecycle_callbacks: Dict[str, List[Callable]] = {
            'on_load': [],
            'on_unload': [],
            'on_activate': [],
            'on_deactivate': [],
            'on_error': []
        }
        
        # 加载配置和插件
        self.load_config()
        self.load_plugins()
    
    def load_config(self):
        """加载插件配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.plugin_configs = config_data.get('plugins', {})
                    self.search_engine_priority = config_data.get('search_engine_priority', self.search_engine_priority)
                    self.logger.info(f"加载插件配置: {self.config_file}")
            else:
                self.logger.info("插件配置文件不存在，使用默认配置")
        except Exception as e:
            self.logger.error(f"加载插件配置失败: {str(e)}")
    
    def save_config(self):
        """保存插件配置"""
        try:
            config_data = {
                'plugins': self.plugin_configs,
                'search_engine_priority': self.search_engine_priority,
                'last_updated': datetime.now().isoformat()
            }
            
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"保存插件配置: {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存插件配置失败: {str(e)}")
    
    def load_plugins(self):
        """加载插件目录中的所有插件"""
        self.logger.info(f"从 {self.plugin_dir} 加载插件")
        
        # 遍历插件目录中的所有Python文件
        for _, name, is_pkg in pkgutil.iter_modules([str(self.plugin_dir)]):
            if name.endswith(("_plugin", "_plugins")) and not is_pkg:
                self._load_plugin_module(name)
    
    def _load_plugin_module(self, module_name: str):
        """加载单个插件模块"""
        try:
            # 导入插件模块
            module = importlib.import_module(f"src.plugins.{module_name}")
            
            # 查找模块中的插件类
            for item_name, item in inspect.getmembers(module, inspect.isclass):
                if inspect.isabstract(item):
                    continue
                
                # 新式插件接口
                if issubclass(item, PluginInterface) and item != PluginInterface:
                    self._register_plugin(item)
                
                # 旧式插件（兼容性）
                elif issubclass(item, Plugin) and item != Plugin:
                    plugin = item()
                    self.legacy_plugins[plugin.name] = plugin
                    self.logger.info(f"加载旧式插件: {plugin.name} v{plugin.version}")
                
                # 网站插件
                elif issubclass(item, BaseWebsitePlugin) and item != BaseWebsitePlugin:
                    website_plugin = item()
                    self.website_plugins.append(website_plugin)
                    self.logger.info(f"加载网站插件: {item.__name__}")
                    
        except Exception as e:
            self.logger.error(f"加载插件模块 {module_name} 失败: {str(e)}")
    
    def _register_plugin(self, plugin_class: Type[PluginInterface]):
        """注册新式插件"""
        try:
            # 创建插件实例
            plugin = plugin_class()
            metadata = plugin.metadata
            
            # 检查依赖
            if not self._check_dependencies(metadata.dependencies):
                self.logger.warning(f"插件 {metadata.name} 依赖不满足，跳过加载")
                return
            
            # 获取插件配置
            plugin_config = self.plugin_configs.get(metadata.name, {})
            
            # 初始化插件
            if plugin.initialize(plugin_config):
                # 如果配置中启用了插件，则激活它
                if plugin_config.get('enabled', metadata.enabled):
                    plugin.activate()
                
                self.plugins[metadata.name] = plugin
                self.logger.info(f"注册插件: {metadata.name} v{metadata.version} ({metadata.plugin_type.value})")
            else:
                self.logger.error(f"插件 {metadata.name} 初始化失败")
                
        except Exception as e:
            self.logger.error(f"注册插件失败: {str(e)}")
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查插件依赖"""
        for dep in dependencies:
            if dep not in self.plugins and dep not in self.legacy_plugins:
                return False
        return True
    
    def get_plugin(self, name: str) -> Optional[Union[PluginInterface, Plugin]]:
        """获取指定名称的插件
        
        Args:
            name: 插件名称
            
        Returns:
            Optional[Union[PluginInterface, Plugin]]: 插件实例，如果不存在则返回None
        """
        return self.plugins.get(name) or self.legacy_plugins.get(name)
    
    def get_all_plugins(self) -> List[Union[PluginInterface, Plugin]]:
        """获取所有插件
        
        Returns:
            List[Union[PluginInterface, Plugin]]: 所有插件实例列表
        """
        return list(self.plugins.values()) + list(self.legacy_plugins.values())
    
    def enable_plugin(self, name: str) -> bool:
        """启用插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功启用
        """
        with self._lock:
            plugin = self.plugins.get(name)
            if plugin:
                if plugin.activate():
                    # 更新配置
                    if name not in self.plugin_configs:
                        self.plugin_configs[name] = {}
                    self.plugin_configs[name]['enabled'] = True
                    self.save_config()
                    return True
            return False
    
    def disable_plugin(self, name: str) -> bool:
        """禁用插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功禁用
        """
        with self._lock:
            plugin = self.plugins.get(name)
            if plugin:
                if plugin.deactivate():
                    # 更新配置
                    if name not in self.plugin_configs:
                        self.plugin_configs[name] = {}
                    self.plugin_configs[name]['enabled'] = False
                    self.save_config()
                    return True
            return False
    
    def reload_plugin(self, name: str) -> bool:
        """重新加载插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功重新加载
        """
        with self._lock:
            try:
                # 先卸载插件
                if not self.unload_plugin(name):
                    self.logger.warning(f"卸载插件 {name} 失败，继续重新加载")
                
                # 重新加载插件
                return self.load_plugin_by_name(name)
                
            except Exception as e:
                error_info = self._error_handler.handle_error(name, e, {'operation': 'reload'})
                self.logger.error(f"重新加载插件 {name} 失败: {str(e)}")
                return False
    
    def load_plugin_by_name(self, name: str) -> bool:
        """根据名称加载插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功加载
        """
        with self._lock:
            try:
                # 查找插件文件
                plugin_file = self._find_plugin_file(name)
                if not plugin_file:
                    self.logger.error(f"未找到插件文件: {name}")
                    return False
                
                return self.load_plugin_from_file(plugin_file)
                
            except Exception as e:
                error_info = self._error_handler.handle_error(name, e, {'operation': 'load_by_name'})
                return False
    
    def load_plugin_from_file(self, plugin_file: Path) -> bool:
        """从文件加载插件
        
        Args:
            plugin_file: 插件文件路径
            
        Returns:
            bool: 是否成功加载
        """
        with self._lock:
            try:
                module_name = plugin_file.stem
                
                # 检查是否已经加载
                if module_name in self._loaded_modules:
                    self.logger.info(f"插件模块 {module_name} 已经加载，先卸载")
                    self._unload_module(module_name)
                
                # 动态加载模块
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                if not spec or not spec.loader:
                    self.logger.error(f"无法创建模块规范: {plugin_file}")
                    return False
                
                module = importlib.util.module_from_spec(spec)
                
                # 执行模块
                spec.loader.exec_module(module)
                
                # 保存模块引用
                self._loaded_modules[module_name] = module
                self._plugin_files[module_name] = plugin_file
                self._file_watchers[str(plugin_file)] = plugin_file.stat().st_mtime
                
                # 注册插件类
                success = False
                for item_name, item in inspect.getmembers(module, inspect.isclass):
                    if inspect.isabstract(item):
                        continue
                    
                    # 新式插件接口
                    if issubclass(item, PluginInterface) and item != PluginInterface:
                        self._register_plugin(item)
                        success = True
                    
                    # 旧式插件（兼容性）
                    elif issubclass(item, Plugin) and item != Plugin:
                        plugin = item()
                        self.legacy_plugins[plugin.name] = plugin
                        self.logger.info(f"加载旧式插件: {plugin.name} v{plugin.version}")
                        success = True
                    
                    # 网站插件
                    elif issubclass(item, BaseWebsitePlugin) and item != BaseWebsitePlugin:
                        website_plugin = item()
                        self.website_plugins.append(website_plugin)
                        self.logger.info(f"加载网站插件: {item.__name__}")
                        success = True
                
                if success:
                    self._execute_lifecycle_callbacks('on_load', module_name)
                
                return success
                
            except Exception as e:
                error_info = self._error_handler.handle_error(plugin_file.stem, e, {'operation': 'load_from_file'})
                return False
    
    def unload_plugin(self, name: str) -> bool:
        """卸载插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功卸载
        """
        with self._lock:
            try:
                success = False
                
                # 卸载新式插件
                if name in self.plugins:
                    plugin = self.plugins[name]
                    if plugin.shutdown():
                        del self.plugins[name]
                        success = True
                        self.logger.info(f"卸载新式插件: {name}")
                
                # 卸载旧式插件
                if name in self.legacy_plugins:
                    del self.legacy_plugins[name]
                    success = True
                    self.logger.info(f"卸载旧式插件: {name}")
                
                # 卸载网站插件
                for i, plugin in enumerate(self.website_plugins):
                    if hasattr(plugin, 'name') and plugin.name == name:
                        self.website_plugins.pop(i)
                        success = True
                        self.logger.info(f"卸载网站插件: {name}")
                        break
                
                # 卸载模块
                module_name = self._find_module_name_by_plugin(name)
                if module_name:
                    self._unload_module(module_name)
                
                if success:
                    self._execute_lifecycle_callbacks('on_unload', name)
                
                return success
                
            except Exception as e:
                error_info = self._error_handler.handle_error(name, e, {'operation': 'unload'})
                return False
    
    def _unload_module(self, module_name: str):
        """卸载模块"""
        try:
            if module_name in self._loaded_modules:
                # 从sys.modules中移除
                full_module_name = f"src.plugins.{module_name}"
                if full_module_name in sys.modules:
                    del sys.modules[full_module_name]
                
                # 清理引用
                del self._loaded_modules[module_name]
                
                if module_name in self._plugin_files:
                    file_path = str(self._plugin_files[module_name])
                    if file_path in self._file_watchers:
                        del self._file_watchers[file_path]
                    del self._plugin_files[module_name]
                
                self.logger.info(f"卸载模块: {module_name}")
                
        except Exception as e:
            self.logger.error(f"卸载模块 {module_name} 失败: {str(e)}")
    
    def _find_plugin_file(self, name: str) -> Optional[Path]:
        """查找插件文件"""
        # 常见的插件文件名模式
        patterns = [
            f"{name}_plugin.py",
            f"{name}.py",
            f"enhanced_{name}_plugin.py",
            f"{name}_enhanced_plugin.py"
        ]
        
        for pattern in patterns:
            plugin_file = self.plugin_dir / pattern
            if plugin_file.exists():
                return plugin_file
        
        return None
    
    def _find_module_name_by_plugin(self, plugin_name: str) -> Optional[str]:
        """根据插件名称查找模块名称"""
        for module_name, module in self._loaded_modules.items():
            # 检查模块中是否包含指定名称的插件
            for item_name, item in inspect.getmembers(module, inspect.isclass):
                if hasattr(item, 'name') and item.name == plugin_name:
                    return module_name
                if hasattr(item, 'metadata') and item.metadata.name == plugin_name:
                    return module_name
        
        return None
    
    def update_plugin_config(self, name: str, config: Dict[str, Any]) -> bool:
        """更新插件配置
        
        Args:
            name: 插件名称
            config: 新的配置
            
        Returns:
            bool: 是否成功更新
        """
        with self._lock:
            try:
                plugin = self.plugins.get(name)
                if plugin:
                    # 验证配置
                    if not self._validate_plugin_config(name, config):
                        self.logger.error(f"插件 {name} 配置验证失败")
                        return False
                    
                    # 备份旧配置
                    old_config = self.plugin_configs.get(name, {}).copy()
                    
                    # 更新插件配置
                    if plugin.update_config(config):
                        # 保存到配置文件
                        self.plugin_configs[name] = config
                        self.save_config()
                        
                        self.logger.info(f"插件 {name} 配置已更新")
                        return True
                    else:
                        self.logger.error(f"插件 {name} 配置更新失败")
                        return False
                else:
                    # 即使插件未加载，也保存配置
                    if self._validate_plugin_config(name, config):
                        self.plugin_configs[name] = config
                        self.save_config()
                        self.logger.info(f"保存插件 {name} 配置（插件未加载）")
                        return True
                    return False
                    
            except Exception as e:
                error_info = self._error_handler.handle_error(name, e, {'operation': 'update_config'})
                return False
    
    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """获取插件配置
        
        Args:
            name: 插件名称
            
        Returns:
            插件配置字典
        """
        return self.plugin_configs.get(name, {})
    
    def set_plugin_parameter(self, name: str, key: str, value: Any) -> bool:
        """设置插件参数
        
        Args:
            name: 插件名称
            key: 参数键
            value: 参数值
            
        Returns:
            bool: 是否成功设置
        """
        with self._lock:
            if name not in self.plugin_configs:
                self.plugin_configs[name] = {}
            
            self.plugin_configs[name][key] = value
            
            # 如果插件已加载，更新其配置
            plugin = self.plugins.get(name)
            if plugin:
                return plugin.update_config(self.plugin_configs[name])
            
            # 保存配置
            self.save_config()
            return True
    
    def get_plugin_parameter(self, name: str, key: str, default=None) -> Any:
        """获取插件参数
        
        Args:
            name: 插件名称
            key: 参数键
            default: 默认值
            
        Returns:
            参数值
        """
        config = self.plugin_configs.get(name, {})
        return config.get(key, default)
    
    def _validate_plugin_config(self, name: str, config: Dict[str, Any]) -> bool:
        """验证插件配置
        
        Args:
            name: 插件名称
            config: 配置字典
            
        Returns:
            bool: 配置是否有效
        """
        try:
            plugin = self.plugins.get(name)
            if plugin and hasattr(plugin, 'metadata') and plugin.metadata.config_schema:
                # 使用插件的配置模式验证
                schema = plugin.metadata.config_schema
                return self._validate_config_against_schema(config, schema)
            
            # 基础验证
            if not isinstance(config, dict):
                return False
            
            # 检查必需的字段
            required_fields = ['enabled']
            for field in required_fields:
                if field in config and not isinstance(config[field], bool):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {str(e)}")
            return False
    
    def _validate_config_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """根据模式验证配置"""
        # 简单的模式验证实现
        try:
            for key, expected_type in schema.items():
                if key in config:
                    if not isinstance(config[key], expected_type):
                        return False
            return True
        except Exception:
            return False
    
    def get_plugin_status(self, name: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取插件状态
        
        Args:
            name: 插件名称，如果为None则返回所有插件状态
            
        Returns:
            插件状态信息
        """
        if name:
            plugin = self.plugins.get(name)
            if plugin:
                status = plugin.get_status()
                # 添加性能监控数据
                metrics = self._performance_monitor.get_metrics(name)
                status['performance'] = {
                    'total_executions': metrics.total_executions,
                    'successful_executions': metrics.successful_executions,
                    'failed_executions': metrics.failed_executions,
                    'success_rate': (
                        metrics.successful_executions / metrics.total_executions
                        if metrics.total_executions > 0 else 0
                    ),
                    'average_execution_time': metrics.average_execution_time,
                    'last_execution_time': (
                        metrics.last_execution_time.isoformat()
                        if metrics.last_execution_time else None
                    )
                }
                # 添加错误信息
                recent_errors = self._error_handler.get_errors(name, limit=5)
                status['recent_errors'] = recent_errors
                return status
            return {"error": f"插件 {name} 不存在"}
        else:
            statuses = []
            for plugin in self.plugins.values():
                status = self.get_plugin_status(plugin.metadata.name)
                statuses.append(status)
            return statuses
    
    def get_plugin_performance_metrics(self, name: str = None) -> Union[PluginPerformanceMetrics, Dict[str, PluginPerformanceMetrics]]:
        """获取插件性能指标
        
        Args:
            name: 插件名称，如果为None则返回所有插件指标
            
        Returns:
            性能指标
        """
        return self._performance_monitor.get_metrics(name)
    
    def get_plugin_errors(self, name: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """获取插件错误记录
        
        Args:
            name: 插件名称，如果为None则返回所有插件错误
            limit: 限制返回的错误数量
            
        Returns:
            错误记录列表
        """
        return self._error_handler.get_errors(name, limit)
    
    def clear_plugin_errors(self, name: str = None):
        """清除插件错误记录
        
        Args:
            name: 插件名称，如果为None则清除所有错误
        """
        self._error_handler.clear_errors(name)
    
    def reset_plugin_metrics(self, name: str = None):
        """重置插件性能指标
        
        Args:
            name: 插件名称，如果为None则重置所有指标
        """
        self._performance_monitor.reset_metrics(name)
    
    def add_lifecycle_callback(self, event: str, callback: Callable):
        """添加插件生命周期回调
        
        Args:
            event: 事件名称 ('on_load', 'on_unload', 'on_activate', 'on_deactivate', 'on_error')
            callback: 回调函数
        """
        if event in self._lifecycle_callbacks:
            self._lifecycle_callbacks[event].append(callback)
    
    def remove_lifecycle_callback(self, event: str, callback: Callable):
        """移除插件生命周期回调"""
        if event in self._lifecycle_callbacks and callback in self._lifecycle_callbacks[event]:
            self._lifecycle_callbacks[event].remove(callback)
    
    def _execute_lifecycle_callbacks(self, event: str, *args, **kwargs):
        """执行生命周期回调"""
        for callback in self._lifecycle_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"生命周期回调执行失败: {str(e)}")
    
    def monitor_plugin_files(self) -> Dict[str, bool]:
        """监控插件文件变化
        
        Returns:
            Dict[str, bool]: 文件路径到是否变化的映射
        """
        changes = {}
        
        for file_path, last_mtime in self._file_watchers.items():
            try:
                current_mtime = Path(file_path).stat().st_mtime
                if current_mtime != last_mtime:
                    changes[file_path] = True
                    self._file_watchers[file_path] = current_mtime
                else:
                    changes[file_path] = False
            except Exception as e:
                self.logger.error(f"监控文件 {file_path} 失败: {str(e)}")
                changes[file_path] = False
        
        return changes
    
    def auto_reload_changed_plugins(self) -> List[str]:
        """自动重新加载已变化的插件
        
        Returns:
            List[str]: 重新加载的插件名称列表
        """
        reloaded = []
        changes = self.monitor_plugin_files()
        
        for file_path, changed in changes.items():
            if changed:
                # 查找对应的插件名称
                plugin_file = Path(file_path)
                module_name = plugin_file.stem
                
                # 查找使用此模块的插件
                plugins_to_reload = []
                for plugin_name, plugin in self.plugins.items():
                    if self._find_module_name_by_plugin(plugin_name) == module_name:
                        plugins_to_reload.append(plugin_name)
                
                # 重新加载插件
                for plugin_name in plugins_to_reload:
                    if self.reload_plugin(plugin_name):
                        reloaded.append(plugin_name)
                        self.logger.info(f"自动重新加载插件: {plugin_name}")
        
        return reloaded
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """根据类型获取插件
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            指定类型的插件列表
        """
        return [
            plugin for plugin in self.plugins.values()
            if plugin.metadata.plugin_type == plugin_type
        ]
    
    def find_plugin_for_instruction(self, instruction: Dict[str, Any]) -> Optional[Union[PluginInterface, Plugin]]:
        """查找可以处理指定指令的插件
        
        Args:
            instruction: 标准化的JSON格式指令
            
        Returns:
            Optional[Union[PluginInterface, Plugin]]: 可以处理指令的插件实例，如果不存在则返回None
        """
        # 优先查找新式插件
        for plugin in self.plugins.values():
            if plugin.can_handle(instruction):
                return plugin
        
        # 回退到旧式插件
        for plugin in self.legacy_plugins.values():
            if plugin.can_handle(instruction):
                return plugin
        
        return None
    
    def execute_instruction(self, instruction: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """执行指令
        
        Args:
            instruction: 标准化的JSON格式指令
            session_state: 会话状态
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 查找可以处理指令的插件
        plugin = self.find_plugin_for_instruction(instruction)
        
        if plugin:
            plugin_name = getattr(plugin, 'metadata', plugin).name if hasattr(plugin, 'metadata') else plugin.name
            execution_id = self._performance_monitor.start_execution(plugin_name)
            start_time = time.time()
            
            try:
                self.logger.info(f"使用插件 {plugin_name} 执行指令")
                
                # 新式插件使用上下文
                if isinstance(plugin, PluginInterface):
                    context = PluginContext(session_state)
                    result = plugin.execute(instruction, context)
                else:
                    # 旧式插件直接传递session_state
                    result = plugin.execute(instruction, session_state)
                
                # 记录成功执行
                execution_time = time.time() - start_time
                self._performance_monitor.end_execution(plugin_name, execution_id, True)
                
                # 添加执行时间到结果中
                if isinstance(result, dict):
                    result['execution_time'] = execution_time
                    result['plugin_name'] = plugin_name
                
                return result
                    
            except Exception as e:
                # 记录失败执行
                execution_time = time.time() - start_time
                self._performance_monitor.end_execution(plugin_name, execution_id, False, str(e))
                
                # 记录错误
                error_info = self._error_handler.handle_error(
                    plugin_name, e, 
                    {'instruction': instruction, 'execution_time': execution_time}
                )
                
                # 执行错误回调
                self._execute_lifecycle_callbacks('on_error', plugin_name, e, instruction)
                
                self.logger.error(f"插件 {plugin_name} 执行指令失败: {str(e)}")
                return {
                    "success": False,
                    "message": f"插件执行失败: {plugin_name}",
                    "error": str(e),
                    "execution_time": execution_time,
                    "plugin_name": plugin_name,
                    "error_id": error_info.get('timestamp')
                }
        else:
            self.logger.warning(f"没有找到可以处理指令的插件: {instruction.get('action')}")
            return {
                "success": False,
                "message": "没有找到可以处理指令的插件",
                "error": f"不支持的操作: {instruction.get('action')}"
            }

    def get_website_plugin(self, url: str) -> Optional[BaseWebsitePlugin]:
        """
        根据URL查找并返回对应的网站插件。
        
        Args:
            url: 当前页面的URL。
            
        Returns:
            Optional[BaseWebsitePlugin]: 匹配的网站插件实例，如果不存在则返回None。
        """
        for plugin in self.website_plugins:
            if plugin.can_handle_url(url):
                return plugin
        return None

    def get_all_site_name_mappings(self) -> Dict[str, str]:
        """
        聚合所有网站插件的中文名称到URL的映射。
        
        Returns:
            Dict[str, str]: 聚合后的映射字典。
        """
        all_mappings = {}
        for plugin in self.website_plugins:
            all_mappings.update(plugin.get_site_name_mapping())
        return all_mappings
    
    def shutdown_all_plugins(self):
        """关闭所有插件"""
        with self._lock:
            for plugin in self.plugins.values():
                try:
                    plugin.shutdown()
                except Exception as e:
                    self.logger.error(f"关闭插件失败: {str(e)}")
            
            self.plugins.clear()
            self.legacy_plugins.clear()
            self.website_plugins.clear()


# 兼容性类，保持向后兼容
class PluginManager(EnhancedPluginManager):
    """插件管理器类（兼容性包装）"""
    
    def __init__(self, plugin_dir: Optional[str] = None):
        """初始化插件管理器
        
        Args:
            plugin_dir: 插件目录路径，默认为当前文件所在目录
        """
        super().__init__(plugin_dir)
    
    def set_search_engine_priority(self, engines: List[str]):
        """设置搜索引擎优先级
        
        Args:
            engines: 搜索引擎名称列表，按优先级排序
        """
        self.search_engine_priority = engines
    
    def get_search_engine_priority(self) -> List[str]:
        """获取当前搜索引擎优先级"""
        return self.search_engine_priority
    
    def build_instruction_with_fallback(self, user_text: str, target_url: str) -> Optional[Dict[str, Any]]:
        """
        为指定网站构建指令，如果网站存在访问限制则使用搜索引擎优先级配置。
        
        Args:
            user_text: 用户输入的自然语言文本
            target_url: 目标网站URL
            
        Returns:
            构建的指令，如果需要回退策略则包含fallback信息
        """
        plugin = self.get_website_plugin(target_url)
        if not plugin:
            return None
            
        # 检查是否存在访问限制
        if plugin.has_access_restrictions():
            # 提取搜索关键词
            query = self._extract_search_keywords_from_text(user_text)
            
            # 使用搜索引擎优先级配置构建回退策略
            engines = self.get_search_engine_priority()
            if engines:
                # 使用第一个引擎作为主要策略
                primary_engine = engines[0]
                primary_strategy = {
                    "action": "search",
                    "engine": primary_engine,
                    "value": query,
                    "description": f"使用{primary_engine}搜索: {query}"
                }
                
                # 构建替代策略
                alternative_strategies = []
                for engine in engines[1:]:
                    alternative_strategies.append(f"使用{engine}搜索: {query}")
                
                return {
                    "steps": [primary_strategy],
                    "description": f"网络限制回退: {primary_strategy['description']}",
                    "fallback_info": {
                        "reason": f"该网站存在访问限制",
                        "primary_strategy": primary_strategy["description"],
                        "alternative_strategies": alternative_strategies
                    }
                }
        
        # 正常情况下，如果是纯导航指令（没有搜索意图），返回None让上层处理
        if not self._has_search_intent(user_text):
            return None
            
        # 只有在有搜索意图时才构建搜索指令
        query = self._extract_search_keywords_from_text(user_text)
        search_steps = plugin.build_search_action(query)
        if search_steps:
            return {
                "steps": [{"action": "navigate", "value": target_url, "description": f"导航到 {target_url}"}] + search_steps,
                "description": f"在网站上搜索: {query}"
            }
        
        return None
    
    def _has_search_intent(self, user_text: str) -> bool:
        """
        检测用户文本是否包含搜索意图。
        
        Args:
            user_text: 用户输入的自然语言文本
            
        Returns:
            如果包含搜索意图则返回True
        """
        import re
        return bool(re.search(r"(搜索|查询|找|查找|search)", user_text, re.IGNORECASE))
    
    def _extract_search_keywords_from_text(self, user_text: str) -> str:
        """
        从用户文本中提取搜索关键词。
        
        Args:
            user_text: 用户输入的自然语言文本
            
        Returns:
            提取的搜索关键词
        """
        import re
        
        # 常见搜索模式
        patterns = [
            r"搜索[\s'\"]*([^'\"\uff0c\u3002]+)",
            r"查找[\s'\"]*([^'\"\uff0c\u3002]+)",
            r"查询[\s'\"]*([^'\"\uff0c\u3002]+)",
            r"在.+?搜索[\s'\"]*([^'\"\uff0c\u3002]+)",
            r"打开.+?，查询(.+)",
            r"去.+?找(.+)",
            r"在.+?查找(.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_text)
            if match:
                keyword = match.group(1).strip()
                if len(keyword) > 1:
                    return keyword
        
        # 如果没有匹配到特定模式，移除常见动词后返回
        cleaned = re.sub(r"(打开|访问|进入|搜索|查找|点击|输入|在|上|的|并|然后|请|帮我|网站|查询)", "", user_text)
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else user_text.strip()