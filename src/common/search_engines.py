#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索引擎优先级配置

定义搜索引擎的优先级顺序和相关配置。
"""

from typing import List, Dict, Any


# 搜索引擎优先级配置
# 优先级基于以下因素：
# 1. 全球使用率和覆盖范围
# 2. 搜索结果质量
# 3. 对中文内容的支持程度
# 4. 系统可用性和稳定性
SEARCH_ENGINE_PRIORITY = [
    {
        "name": "bing",
        "display_name": "必应",
        "url": "https://www.bing.com",
        "search_box_selector": "input[name='q']",
        "submit_method": "enter_key",  # 使用回车键提交，更稳定
        "description": "必应搜索引擎"
    },
    {
        "name": "google",
        "display_name": "Google",
        "url": "https://www.google.com",
        "search_box_selector": "textarea[name='q'], input[name='q']",
        "submit_method": "enter_key",
        "description": "Google搜索引擎"
    },
    {
        "name": "baidu",
        "display_name": "百度",
        "url": "https://www.baidu.com",
        "search_box_selector": "#kw",
        "submit_method": "click",  # 百度更倾向于点击按钮
        "description": "百度搜索引擎"
    }
]


def get_search_engine_by_name(name: str) -> Dict[str, Any]:
    """
    根据名称获取搜索引擎配置
    
    Args:
        name: 搜索引擎名称
        
    Returns:
        搜索引擎配置字典
    """
    for engine in SEARCH_ENGINE_PRIORITY:
        if engine["name"] == name:
            return engine
    return SEARCH_ENGINE_PRIORITY[0]  # 默认返回第一个


def get_search_engines_in_priority_order() -> List[Dict[str, Any]]:
    """
    获取按优先级排序的搜索引擎列表
    
    Returns:
        搜索引擎配置列表
    """
    return SEARCH_ENGINE_PRIORITY


def get_primary_search_engine() -> Dict[str, Any]:
    """
    获取主要搜索引擎（优先级最高的）
    
    Returns:
        搜索引擎配置字典
    """
    return SEARCH_ENGINE_PRIORITY[0]


def build_search_fallback_strategy(site_name: str, query: str) -> List[Dict[str, Any]]:
    """
    构建通用的搜索引擎回退策略
    
    Args:
        site_name: 网站名称（如"小红书"）
        query: 搜索查询词
        
    Returns:
        包含多个搜索引擎策略的列表
    """
    strategies = []
    
    for engine in SEARCH_ENGINE_PRIORITY:
        steps = [
            {"action": "navigate", "value": engine["url"], "description": f"导航到{engine['display_name']}"},
            {"action": "wait", "selector": engine["search_box_selector"], "timeout": 5000, "description": f"等待{engine['display_name']}搜索框"},
            {"action": "fill", "selector": engine["search_box_selector"], "value": f"site:{site_name.lower()} {query}", "description": f"搜索{site_name}站内内容: {query}"},
        ]
        
        # 根据搜索引擎的推荐提交方式添加步骤
        if engine["submit_method"] == "enter_key":
            steps.append({"action": "key", "selector": engine["search_box_selector"], "value": "Enter", "description": "按回车键执行搜索"})
        else:
            # 百度使用点击按钮的方式
            steps.append({"action": "click", "selector": "#su", "description": f"点击{engine['display_name']}搜索按钮"})
        
        strategies.append({
            "description": f"策略: 通过{engine['display_name']}搜索{site_name}内容",
            "steps": steps
        })
    
    return strategies