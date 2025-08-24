#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化指令构建器 - 仅使用启发式逻辑
用于演示目的，无需LLM API
"""

import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus

from src.common.logger import get_logger


class SimpleInstructionBuilder:
    """简化指令构建器类，仅使用内置启发式逻辑"""

    def __init__(self):
        """初始化指令构建器"""
        self.logger = get_logger()

    def build(self, user_instruction: str, page_data: Dict[str, Any],
              session_state: Dict[str, Any]) -> Dict[str, Any]:
        """构建标准化的JSON格式指令"""
        try:
            self.logger.info(f"构建指令（启发式模式）: {user_instruction}")

            # 若页面无效/空白，优先从指令中提取 URL 或生成 Bing 搜索前置步骤
            if not page_data or not page_data.get("is_valid", True) or page_data.get("page_type") == "blank":
                nav_only = self._maybe_build_navigation_first(user_instruction)
                if nav_only:
                    return nav_only
                # 如果没有明确URL，则使用 Bing 前置检索
                bing_pre_search = self._build_bing_pre_search(user_instruction)
                if bing_pre_search:
                    return bing_pre_search

            # 在已加载页面上，尝试已知站点的启发式动作（如搜索框操作）
            known = self._maybe_build_known_site_action(user_instruction, page_data)
            if known:
                return known

            # 如果无法使用启发式处理，返回基本操作
            return self._build_basic_action(user_instruction, page_data)

        except Exception as e:
            self.logger.error(f"构建指令时发生错误: {str(e)}")
            # 返回错误指令
            return {
                "action": "error",
                "error": str(e),
                "original_instruction": user_instruction
            }

    def _detect_navigation_intent_and_url(self, user_instruction: str) -> Optional[str]:
        """识别导航意图并提取规范化 URL"""
        # 1) 显式 URL（http/https）
        m = re.search(r"https?://[A-Za-z0-9.-]+(?:\.[A-Za-z]{2,24})(?:/[^\s]*)?", user_instruction)
        if m:
            return m.group(0)
        # 2) 裸域（仅ASCII域名与TLD），避免把中文词缀合入
        m2 = re.search(r"(?<![A-Za-z0-9.-])([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24})(?![A-Za-z0-9.-])",
                       user_instruction)
        if m2:
            return "https://" + m2.group(1)
        return None

    def _maybe_build_navigation_first(self, user_instruction: str) -> Optional[Dict[str, Any]]:
        """在页面为空时，尝试仅生成导航步骤（URL 直达）"""
        url = self._detect_navigation_intent_and_url(user_instruction)
        if not url:
            return None
        return {
            "steps": [
                {"action": "navigate", "value": url, "description": f"导航到 {url}"},
                {"action": "wait", "value": 2000, "description": "等待页面就绪(2秒)"}
            ],
            "description": f"前置导航到 {url} 并等待页面加载"
        }

    def _build_bing_pre_search(self, user_instruction: str) -> Dict[str, Any]:
        """当无法直达 URL 时，先在 Bing 搜索预检索站点/意图"""
        query = quote_plus(user_instruction.strip())
        url = f"https://www.bing.com/search?q={query}"
        return {
            "steps": [
                {"action": "navigate", "value": url, "description": f"在Bing搜索：{user_instruction}"},
                {"action": "wait", "value": 2000, "description": "等待搜索结果加载(2秒)"}
            ],
            "description": "前置导航到Bing进行检索"
        }

    def _intent_is_search(self, instruction: str) -> bool:
        return bool(re.search(r"(搜索|查询|找|search|查找)", instruction, re.IGNORECASE))

    def _extract_query_from_instruction(self, instruction: str) -> str:
        # 尝试提取搜索关键词
        patterns = [
            r"(?:搜索|查询|找|search)[\s\"']*([^\"']+)",
            r"\"([^\"]+)\"",
            r"'([^']+)'",
            r"(北京秋天|北京|秋天)"
        ]
        
        for pattern in patterns:
            m = re.search(pattern, instruction, re.IGNORECASE)
            if m:
                return m.group(1).strip().strip("'\"")
        
        # 如果没有匹配到特定模式，返回整个指令去除常见动词
        cleaned = re.sub(r"(搜索|查询|找|search|打开|访问)", "", instruction).strip()
        return cleaned if cleaned else instruction.strip()

    def _maybe_build_known_site_action(self, user_instruction: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """在已知站点（如百度/Bing/Google）上生成搜索动作的启发式步骤"""
        try:
            if not self._intent_is_search(user_instruction):
                return None
            
            url = (page_data or {}).get("url") or ""
            host = ""
            if url:
                m = re.search(r"://([^/]+)/?", url)
                if m:
                    host = m.group(1).lower()
            
            if not host:
                return None
            
            query = self._extract_query_from_instruction(user_instruction)
            steps: List[Dict[str, Any]] = []
            
            # 百度
            if "baidu.com" in host:
                steps = [
                    {"action": "wait", "selector": "id=kw", "timeout": 5000, "description": "等待搜索框出现"},
                    {"action": "fill", "selector": "id=kw", "value": query, "description": f"在百度搜索框输入 '{query}'"},
                    {"action": "click", "selector": "id=su", "description": "点击百度搜索按钮"}
                ]
            # Bing
            elif "bing.com" in host:
                steps = [
                    {"action": "wait", "selector": "input[name=q]", "timeout": 5000, "description": "等待搜索框出现"},
                    {"action": "fill", "selector": "input[name=q]", "value": query, "description": f"在Bing搜索框输入 '{query}'"},
                    {"action": "click", "selector": "#sb_form_go", "description": "点击Bing搜索按钮"}
                ]
            # Google
            elif "google." in host:
                steps = [
                    {"action": "wait", "selector": "textarea[name=q]", "timeout": 5000, "description": "等待搜索框出现"},
                    {"action": "fill", "selector": "textarea[name=q]", "value": query, "description": f"在Google搜索框输入 '{query}'"},
                    {"action": "click", "selector": "input[name=btnK]", "description": "点击Google搜索按钮"}
                ]
            else:
                return None
            
            return {"steps": steps, "description": f"站内搜索: {query}"}
        except Exception:
            return None

    def _build_basic_action(self, user_instruction: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建基本操作指令"""
        instruction_lower = user_instruction.lower()
        
        # 截图操作
        if any(word in instruction_lower for word in ["截图", "screenshot", "截取", "保存图片"]):
            return {
                "action": "screenshot",
                "description": "截取当前页面截图"
            }
        
        # 返回操作
        if any(word in instruction_lower for word in ["返回", "back", "上一页"]):
            return {
                "action": "back",
                "description": "返回上一页"
            }
        
        # 前进操作
        if any(word in instruction_lower for word in ["前进", "forward", "下一页"]):
            return {
                "action": "forward",
                "description": "前进到下一页"
            }
        
        # 刷新操作
        if any(word in instruction_lower for word in ["刷新", "refresh", "重新加载"]):
            return {
                "action": "refresh",
                "description": "刷新当前页面"
            }
        
        # 点击操作
        if any(word in instruction_lower for word in ["点击", "click", "选择"]):
            # 尝试提取简单的选择器
            selectors = [
                "第一个搜索结果",
                "第一个结果", 
                "搜索结果",
                "链接",
                "按钮"
            ]
            
            for selector_hint in selectors:
                if selector_hint in user_instruction:
                    if "第一个" in user_instruction and "搜索结果" in user_instruction:
                        return {
                            "action": "click",
                            "selector": ".result:first-child a, .c-container:first-child h3 a, h3:first-child a",
                            "description": "点击第一个搜索结果"
                        }
            
            # 通用点击
            return {
                "action": "click",
                "selector": "a:first-child, button:first-child",
                "description": "点击页面上的第一个可点击元素"
            }
        
        # 获取信息操作
        if any(word in instruction_lower for word in ["获取", "提取", "分析", "信息"]):
            return {
                "action": "extract",
                "description": "提取当前页面信息"
            }
        
        # 默认等待操作
        return {
            "action": "wait",
            "value": 2000,
            "description": "等待页面加载完成"
        }