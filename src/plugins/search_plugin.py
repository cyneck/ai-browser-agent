#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索插件

提供搜索引擎相关功能的插件。
"""

import re
from typing import Dict, Any, List, Optional

from src.plugins.plugin_manager import Plugin


class SearchPlugin(Plugin):
    """搜索插件类"""
    
    # 插件名称
    name = "search_plugin"
    
    # 插件描述
    description = "提供搜索引擎相关功能"
    
    # 插件版本
    version = "0.1.0"
    
    # 插件作者
    author = "AI Browser Agent Team"
    
    # 插件支持的指令类型
    supported_actions = ["search"]
    
    # 支持的搜索引擎
    supported_engines = {
        "google": "https://www.google.com/search?q={}",
        "baidu": "https://www.baidu.com/s?wd={}",
        "bing": "https://www.bing.com/search?q={}",
        "duckduckgo": "https://duckduckgo.com/?q={}"
    }
    
    def execute(self, instruction: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索功能
        
        Args:
            instruction: 标准化的JSON格式指令
            session_state: 会话状态
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 获取搜索引擎和关键词
            engine = instruction.get("engine", "google").lower()
            query = instruction.get("value", "")
            
            if not query:
                return {
                    "success": False,
                    "message": "搜索关键词不能为空",
                    "error": "缺少搜索关键词"
                }
            
            # 检查搜索引擎是否支持
            if engine not in self.supported_engines:
                return {
                    "success": False,
                    "message": f"不支持的搜索引擎: {engine}",
                    "error": f"支持的搜索引擎: {', '.join(self.supported_engines.keys())}"
                }
            
            # 构建搜索URL
            search_url = self.supported_engines[engine].format(query)
            
            # 创建导航指令
            navigate_instruction = {
                "action": "navigate",
                "value": search_url,
                "description": f"使用{engine}搜索: {query}"
            }
            
            # 更新会话状态
            if "search_history" not in session_state:
                session_state["search_history"] = []
            
            session_state["search_history"].append({
                "engine": engine,
                "query": query,
                "url": search_url,
                "timestamp": session_state.get("timestamp", 0)
            })
            
            # 返回导航指令和成功信息
            return {
                "success": True,
                "message": f"准备使用{engine}搜索: {query}",
                "instruction": navigate_instruction
            }
        except Exception as e:
            self.logger.error(f"执行搜索操作失败: {str(e)}")
            return {
                "success": False,
                "message": "执行搜索操作失败",
                "error": str(e)
            }