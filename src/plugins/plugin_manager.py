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
from src.plugins.base_website_plugin import BaseWebsitePlugin


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
        # 网站插件列表
        self.website_plugins: List[BaseWebsitePlugin] = []
        
        # 加载插件
        self.load_plugins()
    
    def load_plugins(self):
        """加载插件目录中的所有插件"""
        self.logger.info(f"从 {self.plugin_dir} 加载插件")
        
        # 遍历插件目录中的所有Python文件
        for _, name, is_pkg in pkgutil.iter_modules([str(self.plugin_dir)]):
            if name.endswith(("_plugin", "_plugins")) and not is_pkg: # 确保只加载文件，不加载子包
                try:
                    # 导入插件模块
                    module = importlib.import_module(f"src.plugins.{name}")
                    
                    # 查找模块中的Plugin子类和BaseWebsitePlugin子类
                    for item_name, item in inspect.getmembers(module, inspect.isclass):
                        if inspect.isabstract(item): # 忽略抽象基类
                            continue
                        if issubclass(item, Plugin) and item != Plugin:
                            # 实例化插件并添加到插件字典
                            plugin = item()
                            self.plugins[plugin.name] = plugin
                            self.logger.info(f"加载通用插件: {plugin.name} v{plugin.version}")
                        elif issubclass(item, BaseWebsitePlugin) and item != BaseWebsitePlugin:
                            # 实例化网站插件并添加到网站插件列表
                            website_plugin = item()
                            self.website_plugins.append(website_plugin)
                            self.logger.info(f"加载网站插件: {item.__name__}")
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
    
    def build_instruction_with_fallback(self, user_text: str, target_url: str) -> Optional[Dict[str, Any]]:
        """
        为指定网站构建指令，如果网站存在访问限制则使用回退策略。
        
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
            
            # 获取回退策略
            fallback_strategies = plugin.build_fallback_strategies(query)
            if fallback_strategies:
                # 使用第一个策略作为主要策略
                primary_strategy = fallback_strategies[0]
                return {
                    "steps": primary_strategy["steps"],
                    "description": f"网络限制回退: {primary_strategy['description']}",
                    "fallback_info": {
                        "reason": f"该网站存在访问限制",
                        "primary_strategy": primary_strategy["description"],
                        "alternative_strategies": [s["description"] for s in fallback_strategies[1:]]
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