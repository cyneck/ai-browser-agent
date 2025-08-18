#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件管理器

负责加载、管理和执行插件。
"""

import importlib
import inspect
import os
import pkgutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Type

from src.common.logger import get_logger


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


class PluginManager:
    """插件管理器类"""
    
    def __init__(self, plugin_dir: Optional[str] = None):
        """初始化插件管理器
        
        Args:
            plugin_dir: 插件目录路径，默认为当前文件所在目录
        """
        self.logger = get_logger()
        
        # 设置插件目录
        if plugin_dir is None:
            self.plugin_dir = Path(__file__).parent
        else:
            self.plugin_dir = Path(plugin_dir)
        
        # 插件字典，键为插件名称，值为插件实例
        self.plugins: Dict[str, Plugin] = {}
        
        # 加载插件
        self.load_plugins()
    
    def load_plugins(self):
        """加载插件目录中的所有插件"""
        self.logger.info(f"从 {self.plugin_dir} 加载插件")
        
        # 遍历插件目录中的所有Python文件
        for _, name, is_pkg in pkgutil.iter_modules([str(self.plugin_dir)]):
            if name.endswith("_plugin"):
                try:
                    # 导入插件模块
                    module = importlib.import_module(f"src.plugins.{name}")
                    
                    # 查找模块中的Plugin子类
                    for item_name, item in inspect.getmembers(module, inspect.isclass):
                        if issubclass(item, Plugin) and item != Plugin:
                            # 实例化插件并添加到插件字典
                            plugin = item()
                            self.plugins[plugin.name] = plugin
                            self.logger.info(f"加载插件: {plugin.name} v{plugin.version}")
                except Exception as e:
                    self.logger.error(f"加载插件 {name} 失败: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取指定名称的插件
        
        Args:
            name: 插件名称
            
        Returns:
            Optional[Plugin]: 插件实例，如果不存在则返回None
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """获取所有插件
        
        Returns:
            List[Plugin]: 所有插件实例列表
        """
        return list(self.plugins.values())
    
    def find_plugin_for_instruction(self, instruction: Dict[str, Any]) -> Optional[Plugin]:
        """查找可以处理指定指令的插件
        
        Args:
            instruction: 标准化的JSON格式指令
            
        Returns:
            Optional[Plugin]: 可以处理指令的插件实例，如果不存在则返回None
        """
        for plugin in self.plugins.values():
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
            try:
                self.logger.info(f"使用插件 {plugin.name} 执行指令")
                return plugin.execute(instruction, session_state)
            except Exception as e:
                self.logger.error(f"插件 {plugin.name} 执行指令失败: {str(e)}")
                return {
                    "success": False,
                    "message": f"插件执行失败: {plugin.name}",
                    "error": str(e)
                }
        else:
            self.logger.warning(f"没有找到可以处理指令的插件: {instruction.get('action')}")
            return {
                "success": False,
                "message": "没有找到可以处理指令的插件",
                "error": f"不支持的操作: {instruction.get('action')}"
            }