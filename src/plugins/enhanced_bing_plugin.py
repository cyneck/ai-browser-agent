#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的Bing搜索插件

使用新的插件接口实现的Bing搜索优化插件。
"""

from typing import Dict, Any, List, Optional
from src.plugins.plugin_interface import (
    PluginInterface, PluginMetadata, PluginType, PluginContext
)


class EnhancedBingPlugin(PluginInterface):
    """增强的Bing搜索插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="enhanced_bing",
            version="2.0.0",
            description="增强的Bing搜索插件，支持多种搜索模式和AI聊天功能",
            author="AI Browser Agent Team",
            plugin_type=PluginType.WEBSITE,
            supported_actions=[
                "bing_search", "bing_image_search", "bing_video_search",
                "bing_news_search", "bing_chat", "extract_bing_results"
            ],
            config_schema={
                "market": {"type": "string", "default": "zh-CN"},
                "safe_search": {"type": "string", "default": "moderate"},
                "enable_copilot": {"type": "boolean", "default": True},
                "conversation_style": {"type": "string", "default": "balanced"}
            }
        )
    
    def _on_initialize(self) -> bool:
        """插件初始化"""
        # 设置默认配置
        default_config = {
            "market": "zh-CN",
            "safe_search": "moderate",
            "enable_copilot": True,
            "conversation_style": "balanced"
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        self.logger.info("Bing插件初始化完成")
        return True
    
    def _execute_internal(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件内部逻辑"""
        action = instruction.get("action")
        
        if action == "bing_search":
            return self._perform_search(instruction, context)
        elif action == "bing_image_search":
            return self._perform_image_search(instruction, context)
        elif action == "bing_video_search":
            return self._perform_video_search(instruction, context)
        elif action == "bing_news_search":
            return self._perform_news_search(instruction, context)
        elif action == "bing_chat":
            return self._perform_chat(instruction, context)
        elif action == "extract_bing_results":
            return self._extract_search_results(instruction, context)
        else:
            return {
                "success": False,
                "message": f"不支持的操作: {action}"
            }
    
    def _perform_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行基础Bing搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "搜索查询不能为空"
            }
        
        context.log_info(f"执行Bing搜索: {query}")
        
        # 构建搜索步骤
        search_steps = [
            {
                "action": "navigate",
                "value": "https://www.bing.com",
                "description": "导航到Bing首页"
            },
            {
                "action": "wait",
                "selector": "input[name='q'], #sb_form_q",
                "timeout": 5000,
                "description": "等待搜索框出现"
            },
            {
                "action": "fill",
                "selector": "input[name='q'], #sb_form_q",
                "value": query,
                "description": f"输入搜索查询: {query}"
            },
            {
                "action": "key",
                "selector": "input[name='q'], #sb_form_q",
                "value": "Enter",
                "description": "按回车键执行搜索"
            },
            {
                "action": "wait",
                "value": 3000,
                "description": "等待搜索结果加载"
            }
        ]
        
        # 添加结果提取步骤
        search_steps.append({
            "action": "extract_bing_results",
            "description": "提取Bing搜索结果"
        })
        
        return {
            "success": True,
            "message": f"Bing搜索指令已生成: {query}",
            "steps": search_steps,
            "metadata": {
                "search_engine": "bing",
                "query": query,
                "search_type": "basic"
            }
        }
    
    def _perform_image_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行Bing图片搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "图片搜索查询不能为空"
            }
        
        context.log_info(f"执行Bing图片搜索: {query}")
        
        return {
            "success": True,
            "message": f"Bing图片搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.bing.com/images/search?q={query}",
                    "description": f"导航到Bing图片搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待图片搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".iusc img, .mimg img",
                    "description": "提取图片搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "bing",
                "query": query,
                "search_type": "image"
            }
        }
    
    def _perform_video_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行Bing视频搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "视频搜索查询不能为空"
            }
        
        context.log_info(f"执行Bing视频搜索: {query}")
        
        return {
            "success": True,
            "message": f"Bing视频搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.bing.com/videos/search?q={query}",
                    "description": f"导航到Bing视频搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待视频搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".dg_u, .mc_vtvc",
                    "description": "提取视频搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "bing",
                "query": query,
                "search_type": "video"
            }
        }
    
    def _perform_news_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行Bing新闻搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "新闻搜索查询不能为空"
            }
        
        context.log_info(f"执行Bing新闻搜索: {query}")
        
        return {
            "success": True,
            "message": f"Bing新闻搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.bing.com/news/search?q={query}",
                    "description": f"导航到Bing新闻搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待新闻搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".news-card, .na_cnt",
                    "description": "提取新闻搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "bing",
                "query": query,
                "search_type": "news"
            }
        }
    
    def _perform_chat(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行Bing Chat (Copilot)对话"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "聊天查询不能为空"
            }
        
        if not self.config.get("enable_copilot", True):
            return {
                "success": False,
                "message": "Copilot功能未启用"
            }
        
        context.log_info(f"执行Bing Chat: {query}")
        
        conversation_style = self.config.get("conversation_style", "balanced")
        
        return {
            "success": True,
            "message": f"Bing Chat指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": "https://www.bing.com/chat",
                    "description": "导航到Bing Chat"
                },
                {
                    "action": "wait",
                    "selector": "#searchbox, .as_input",
                    "timeout": 10000,
                    "description": "等待聊天输入框出现"
                },
                {
                    "action": "click",
                    "selector": f"[data-style='{conversation_style}'], .tone-{conversation_style}",
                    "description": f"选择对话风格: {conversation_style}",
                    "optional": True
                },
                {
                    "action": "fill",
                    "selector": "#searchbox, .as_input",
                    "value": query,
                    "description": f"输入聊天查询: {query}"
                },
                {
                    "action": "key",
                    "selector": "#searchbox, .as_input",
                    "value": "Enter",
                    "description": "发送聊天消息"
                },
                {
                    "action": "wait",
                    "value": 5000,
                    "description": "等待AI回复"
                },
                {
                    "action": "extract",
                    "selector": ".ac-textBlock, .response-message",
                    "description": "提取AI回复内容"
                }
            ],
            "metadata": {
                "search_engine": "bing",
                "query": query,
                "search_type": "chat",
                "conversation_style": conversation_style
            }
        }
    
    def _extract_search_results(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """提取Bing搜索结果"""
        context.log_info("提取Bing搜索结果")
        
        return {
            "success": True,
            "message": "Bing搜索结果提取指令已生成",
            "steps": [
                {
                    "action": "extract",
                    "selector": ".b_algo",
                    "description": "提取搜索结果条目"
                },
                {
                    "action": "extract",
                    "selector": ".b_ans, .b_entityTP",
                    "description": "提取即时答案和实体信息"
                },
                {
                    "action": "extract",
                    "selector": ".b_rs",
                    "description": "提取相关搜索建议"
                }
            ],
            "metadata": {
                "extraction_type": "bing_search_results"
            }
        }
    
    def can_handle_url(self, url: str) -> bool:
        """判断是否可以处理指定URL"""
        return "bing.com" in url
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 验证市场设置
        market = config.get("market", "zh-CN")
        valid_markets = ["zh-CN", "en-US", "en-GB", "ja-JP", "ko-KR", "fr-FR", "de-DE", "es-ES"]
        if market not in valid_markets:
            self.logger.warning(f"未知的市场设置: {market}")
        
        # 验证对话风格
        conversation_style = config.get("conversation_style", "balanced")
        valid_styles = ["creative", "balanced", "precise"]
        if conversation_style not in valid_styles:
            self.logger.error(f"无效的对话风格: {conversation_style}")
            return False
        
        return True