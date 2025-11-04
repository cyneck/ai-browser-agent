#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的Google搜索插件

使用新的插件接口实现的Google搜索优化插件。
"""

from typing import Dict, Any, List, Optional
from src.plugins.plugin_interface import (
    PluginInterface, PluginMetadata, PluginType, PluginContext
)


class EnhancedGooglePlugin(PluginInterface):
    """增强的Google搜索插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="enhanced_google",
            version="2.0.0",
            description="增强的Google搜索插件，支持多种搜索策略和结果提取",
            author="AI Browser Agent Team",
            plugin_type=PluginType.WEBSITE,
            supported_actions=[
                "google_search", "google_advanced_search", "google_image_search",
                "google_news_search", "extract_search_results"
            ],
            config_schema={
                "default_region": {"type": "string", "default": ""},
                "safe_search": {"type": "string", "default": "moderate"},
                "results_per_page": {"type": "integer", "default": 10},
                "enable_instant_answers": {"type": "boolean", "default": True}
            }
        )
    
    def _on_initialize(self) -> bool:
        """插件初始化"""
        # 设置默认配置
        default_config = {
            "default_region": "",
            "safe_search": "moderate",
            "results_per_page": 10,
            "enable_instant_answers": True
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        self.logger.info("Google插件初始化完成")
        return True
    
    def _execute_internal(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件内部逻辑"""
        action = instruction.get("action")
        
        if action == "google_search":
            return self._perform_search(instruction, context)
        elif action == "google_advanced_search":
            return self._perform_advanced_search(instruction, context)
        elif action == "google_image_search":
            return self._perform_image_search(instruction, context)
        elif action == "google_news_search":
            return self._perform_news_search(instruction, context)
        elif action == "extract_search_results":
            return self._extract_search_results(instruction, context)
        else:
            return {
                "success": False,
                "message": f"不支持的操作: {action}"
            }
    
    def _perform_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行基础Google搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "搜索查询不能为空"
            }
        
        context.log_info(f"执行Google搜索: {query}")
        
        # 构建搜索步骤
        search_steps = [
            {
                "action": "navigate",
                "value": "https://www.google.com",
                "description": "导航到Google首页"
            },
            {
                "action": "wait",
                "selector": "textarea[name='q'], input[name='q']",
                "timeout": 5000,
                "description": "等待搜索框出现"
            },
            {
                "action": "fill",
                "selector": "textarea[name='q'], input[name='q']",
                "value": query,
                "description": f"输入搜索查询: {query}"
            },
            {
                "action": "key",
                "selector": "textarea[name='q'], input[name='q']",
                "value": "Enter",
                "description": "按回车键执行搜索"
            },
            {
                "action": "wait",
                "value": 3000,
                "description": "等待搜索结果加载"
            }
        ]
        
        # 如果启用了即时答案，添加提取步骤
        if self.config.get("enable_instant_answers", True):
            search_steps.append({
                "action": "extract_search_results",
                "description": "提取搜索结果和即时答案"
            })
        
        return {
            "success": True,
            "message": f"Google搜索指令已生成: {query}",
            "steps": search_steps,
            "metadata": {
                "search_engine": "google",
                "query": query,
                "search_type": "basic"
            }
        }
    
    def _perform_advanced_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行高级Google搜索"""
        query = instruction.get("value", "")
        options = instruction.get("options", {})
        
        # 构建高级搜索URL
        search_params = []
        if query:
            search_params.append(f"q={query}")
        
        # 添加高级搜索参数
        if options.get("site"):
            search_params.append(f"site:{options['site']}")
        if options.get("filetype"):
            search_params.append(f"filetype:{options['filetype']}")
        if options.get("date_range"):
            search_params.append(f"tbs=qdr:{options['date_range']}")
        if options.get("language"):
            search_params.append(f"lr=lang_{options['language']}")
        
        search_url = f"https://www.google.com/search?{'&'.join(search_params)}"
        
        context.log_info(f"执行Google高级搜索: {search_url}")
        
        return {
            "success": True,
            "message": "Google高级搜索指令已生成",
            "steps": [
                {
                    "action": "navigate",
                    "value": search_url,
                    "description": "导航到Google高级搜索结果"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待搜索结果加载"
                },
                {
                    "action": "extract_search_results",
                    "description": "提取高级搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "google",
                "query": query,
                "search_type": "advanced",
                "options": options
            }
        }
    
    def _perform_image_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行Google图片搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "图片搜索查询不能为空"
            }
        
        context.log_info(f"执行Google图片搜索: {query}")
        
        return {
            "success": True,
            "message": f"Google图片搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.google.com/search?q={query}&tbm=isch",
                    "description": f"导航到Google图片搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待图片搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": "img[data-src], img[src]",
                    "description": "提取图片搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "google",
                "query": query,
                "search_type": "image"
            }
        }
    
    def _perform_news_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行Google新闻搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "新闻搜索查询不能为空"
            }
        
        context.log_info(f"执行Google新闻搜索: {query}")
        
        return {
            "success": True,
            "message": f"Google新闻搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.google.com/search?q={query}&tbm=nws",
                    "description": f"导航到Google新闻搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待新闻搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": "article, .g",
                    "description": "提取新闻搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "google",
                "query": query,
                "search_type": "news"
            }
        }
    
    def _extract_search_results(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """提取Google搜索结果"""
        context.log_info("提取Google搜索结果")
        
        return {
            "success": True,
            "message": "Google搜索结果提取指令已生成",
            "steps": [
                {
                    "action": "extract",
                    "selector": "#search .g",
                    "description": "提取搜索结果条目"
                },
                {
                    "action": "extract",
                    "selector": ".kp-blk, .knowledge-panel",
                    "description": "提取知识面板信息"
                },
                {
                    "action": "extract",
                    "selector": ".related-question-pair",
                    "description": "提取相关问题"
                }
            ],
            "metadata": {
                "extraction_type": "google_search_results"
            }
        }
    
    def can_handle_url(self, url: str) -> bool:
        """判断是否可以处理指定URL"""
        return "google." in url
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 验证安全搜索设置
        safe_search = config.get("safe_search", "moderate")
        if safe_search not in ["off", "moderate", "strict"]:
            self.logger.error(f"无效的安全搜索设置: {safe_search}")
            return False
        
        # 验证每页结果数
        results_per_page = config.get("results_per_page", 10)
        if not isinstance(results_per_page, int) or results_per_page < 1 or results_per_page > 100:
            self.logger.error(f"无效的每页结果数: {results_per_page}")
            return False
        
        return True