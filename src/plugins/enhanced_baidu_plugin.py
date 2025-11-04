#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的百度搜索插件

使用新的插件接口实现的百度搜索优化插件。
"""

from typing import Dict, Any, List, Optional
from src.plugins.plugin_interface import (
    PluginInterface, PluginMetadata, PluginType, PluginContext
)


class EnhancedBaiduPlugin(PluginInterface):
    """增强的百度搜索插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="enhanced_baidu",
            version="2.0.0",
            description="增强的百度搜索插件，支持多种搜索模式和百度知道、百科等服务",
            author="AI Browser Agent Team",
            plugin_type=PluginType.WEBSITE,
            supported_actions=[
                "baidu_search", "baidu_image_search", "baidu_video_search",
                "baidu_news_search", "baidu_zhidao", "baidu_baike", "extract_baidu_results"
            ],
            config_schema={
                "search_region": {"type": "string", "default": ""},
                "time_filter": {"type": "string", "default": ""},
                "enable_suggestions": {"type": "boolean", "default": True},
                "prefer_mobile": {"type": "boolean", "default": False}
            }
        )
    
    def _on_initialize(self) -> bool:
        """插件初始化"""
        # 设置默认配置
        default_config = {
            "search_region": "",
            "time_filter": "",
            "enable_suggestions": True,
            "prefer_mobile": False
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        self.logger.info("百度插件初始化完成")
        return True
    
    def _execute_internal(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件内部逻辑"""
        action = instruction.get("action")
        
        if action == "baidu_search":
            return self._perform_search(instruction, context)
        elif action == "baidu_image_search":
            return self._perform_image_search(instruction, context)
        elif action == "baidu_video_search":
            return self._perform_video_search(instruction, context)
        elif action == "baidu_news_search":
            return self._perform_news_search(instruction, context)
        elif action == "baidu_zhidao":
            return self._perform_zhidao_search(instruction, context)
        elif action == "baidu_baike":
            return self._perform_baike_search(instruction, context)
        elif action == "extract_baidu_results":
            return self._extract_search_results(instruction, context)
        else:
            return {
                "success": False,
                "message": f"不支持的操作: {action}"
            }
    
    def _perform_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行基础百度搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "搜索查询不能为空"
            }
        
        context.log_info(f"执行百度搜索: {query}")
        
        # 选择搜索URL
        base_url = "https://m.baidu.com" if self.config.get("prefer_mobile", False) else "https://www.baidu.com"
        
        # 构建搜索步骤
        search_steps = [
            {
                "action": "navigate",
                "value": base_url,
                "description": "导航到百度首页"
            },
            {
                "action": "wait",
                "selector": "input[name='wd'], #kw",
                "timeout": 5000,
                "description": "等待搜索框出现"
            },
            {
                "action": "fill",
                "selector": "input[name='wd'], #kw",
                "value": query,
                "description": f"输入搜索查询: {query}"
            },
            {
                "action": "key",
                "selector": "input[name='wd'], #kw",
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
            "action": "extract_baidu_results",
            "description": "提取百度搜索结果"
        })
        
        return {
            "success": True,
            "message": f"百度搜索指令已生成: {query}",
            "steps": search_steps,
            "metadata": {
                "search_engine": "baidu",
                "query": query,
                "search_type": "basic",
                "mobile_mode": self.config.get("prefer_mobile", False)
            }
        }
    
    def _perform_image_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行百度图片搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "图片搜索查询不能为空"
            }
        
        context.log_info(f"执行百度图片搜索: {query}")
        
        return {
            "success": True,
            "message": f"百度图片搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://image.baidu.com/search/index?tn=baiduimage&word={query}",
                    "description": f"导航到百度图片搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待图片搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".imgitem img, .main_img img",
                    "description": "提取图片搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "baidu",
                "query": query,
                "search_type": "image"
            }
        }
    
    def _perform_video_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行百度视频搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "视频搜索查询不能为空"
            }
        
        context.log_info(f"执行百度视频搜索: {query}")
        
        return {
            "success": True,
            "message": f"百度视频搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.baidu.com/s?wd={query}&tn=baiduhome_pg&ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&word={query}&rsp=0&f4s=1&rsv_pq=&rsv_t=&rqlang=cn&rsv_enter=1&rsv_dl=tb&rsv_sug3=1&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&inputT=&rsv_sug4=",
                    "description": f"导航到百度视频搜索: {query}"
                },
                {
                    "action": "click",
                    "selector": "a[href*='video'], .s-tab-item[data-key='video']",
                    "description": "点击视频标签",
                    "optional": True
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待视频搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".video-list .c-result, .result",
                    "description": "提取视频搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "baidu",
                "query": query,
                "search_type": "video"
            }
        }
    
    def _perform_news_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行百度新闻搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "新闻搜索查询不能为空"
            }
        
        context.log_info(f"执行百度新闻搜索: {query}")
        
        return {
            "success": True,
            "message": f"百度新闻搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://news.baidu.com/ns?word={query}&tn=news&from=news&cl=2&pn=0&rn=20&ct=1",
                    "description": f"导航到百度新闻搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待新闻搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".result, .c-result",
                    "description": "提取新闻搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "baidu",
                "query": query,
                "search_type": "news"
            }
        }
    
    def _perform_zhidao_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行百度知道搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "百度知道搜索查询不能为空"
            }
        
        context.log_info(f"执行百度知道搜索: {query}")
        
        return {
            "success": True,
            "message": f"百度知道搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://zhidao.baidu.com/search?word={query}",
                    "description": f"导航到百度知道搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待百度知道搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".list .dl, .result-list .result-item",
                    "description": "提取百度知道搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "baidu",
                "query": query,
                "search_type": "zhidao"
            }
        }
    
    def _perform_baike_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行百度百科搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "百度百科搜索查询不能为空"
            }
        
        context.log_info(f"执行百度百科搜索: {query}")
        
        return {
            "success": True,
            "message": f"百度百科搜索指令已生成: {query}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://baike.baidu.com/search?word={query}",
                    "description": f"导航到百度百科搜索: {query}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待百度百科搜索结果加载"
                },
                {
                    "action": "extract",
                    "selector": ".search-list .result, .lemma-summary",
                    "description": "提取百度百科搜索结果"
                }
            ],
            "metadata": {
                "search_engine": "baidu",
                "query": query,
                "search_type": "baike"
            }
        }
    
    def _extract_search_results(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """提取百度搜索结果"""
        context.log_info("提取百度搜索结果")
        
        return {
            "success": True,
            "message": "百度搜索结果提取指令已生成",
            "steps": [
                {
                    "action": "extract",
                    "selector": ".result, .c-result",
                    "description": "提取搜索结果条目"
                },
                {
                    "action": "extract",
                    "selector": ".op-stockinfo, .c-group-wrapper",
                    "description": "提取特殊结果卡片"
                },
                {
                    "action": "extract",
                    "selector": ".rrecom-btn-parent, .rs",
                    "description": "提取相关搜索建议"
                }
            ],
            "metadata": {
                "extraction_type": "baidu_search_results"
            }
        }
    
    def can_handle_url(self, url: str) -> bool:
        """判断是否可以处理指定URL"""
        return "baidu.com" in url
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 验证时间过滤器
        time_filter = config.get("time_filter", "")
        valid_filters = ["", "day", "week", "month", "year"]
        if time_filter and time_filter not in valid_filters:
            self.logger.warning(f"未知的时间过滤器: {time_filter}")
        
        return True