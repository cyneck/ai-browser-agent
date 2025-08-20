#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面分析器

负责分析网页内容，提取页面结构和语义信息，生成页面意图图谱。
"""

import json
from typing import Dict, Any, List, Optional

from playwright.sync_api import Page

from src.common.logger import get_logger


class PageAnalyzer:
    """页面分析器类，负责提取网页的结构化信息"""
    
    def __init__(self, page: Page):
        """初始化页面分析器
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.logger = get_logger()
    
    def analyze(self) -> Dict[str, Any]:
        """分析页面内容，生成页面意图图谱
        Returns:
            Dict[str, Any]: 页面意图图谱，包含页面的结构化信息；若页面为空或未初始化，返回空结构
        """
        try:
            # 先安全获取URL和标题
            url = ""
            title = ""
            try:
                url = getattr(self.page, "url", "") or ""
            except Exception:
                url = ""
            try:
                title = self.page.title()
            except Exception:
                title = ""

            # 如果是空白页或未初始化，直接返回无效分析
            if not url or url == "about:blank":
                return {
                    "is_valid": False,
                    "url": url,
                    "title": title or "空白页面",
                    "elements": [],
                    "text_content": "",
                    "functional_areas": [],
                    "page_type": "blank",
                    "aria_snapshot": None
                }
            
            self.logger.info(f"分析页面: {title} ({url})")
            
            # 提取页面元素信息
            elements_info = self._extract_elements_info()
            
            # 提取页面文本内容
            text_content = self._extract_text_content()
            
            # 识别页面主要功能区域
            functional_areas = self._identify_functional_areas()
            
            # 获取轻量 ARIA 快照
            try:
                aria_snapshot = self.page.accessibility.snapshot()
            except Exception:
                aria_snapshot = None
            
            # 构建页面意图图谱
            page_intent_graph = {
                "is_valid": True,
                "url": url,
                "title": title,
                "elements": elements_info,
                "text_content": text_content,
                "functional_areas": functional_areas,
                "page_type": self._determine_page_type(),
                "aria_snapshot": aria_snapshot
            }
            
            self.logger.info("页面分析完成")
            return page_intent_graph
        except Exception as e:
            self.logger.error(f"分析页面时发生错误: {str(e)}")
            # 返回基本信息（无效分析）
            safe_title = ""
            try:
                safe_title = self.page.title()
            except Exception:
                safe_title = "空白页面"
            safe_url = ""
            try:
                safe_url = getattr(self.page, "url", "") or ""
            except Exception:
                safe_url = ""
            return {
                "is_valid": False,
                "url": safe_url,
                "title": safe_title,
                "elements": [],
                "text_content": "",
                "functional_areas": [],
                "page_type": "unknown",
                "aria_snapshot": None,
                "error": str(e)
            }

    def get_aria_snapshot(self) -> Optional[Dict[str, Any]]:
        """获取页面的Aria Snapshot
        Returns:
            Optional[Dict[str, Any]]: 页面的Aria Snapshot，如果获取失败则返回None
        """
        try:
            snapshot = self.page.accessibility.snapshot()
            self.logger.info("成功获取Aria Snapshot")
            return snapshot
        except Exception as e:
            self.logger.error(f"获取Aria Snapshot时发生错误: {str(e)}")
            return None
    
    def _extract_elements_info(self) -> List[Dict[str, Any]]:
        """提取页面元素信息
        Returns:
            List[Dict[str, Any]]: 页面元素信息列表
        """
        try:
            elements_info = self.page.evaluate(
                """
                () => {
                    // 获取所有可交互元素
                    const interactiveElements = Array.from(document.querySelectorAll(
                        'a, button, input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="tab"]'
                    ));
                    
                    // 提取元素信息
                    return interactiveElements.map(el => {
                        // 获取元素文本
                        const text = el.innerText || el.textContent || '';
                        
                        // 获取元素类型
                        let type = el.tagName.toLowerCase();
                        if (el.hasAttribute('role')) {
                            type = el.getAttribute('role');
                        }
                        if (el.tagName.toLowerCase() === 'input') {
                            type = el.type || 'input';
                        }
                        
                        // 获取元素属性
                        const attributes = {};
                        Array.from(el.attributes).forEach(attr => {
                            attributes[attr.name] = attr.value;
                        });
                        
                        // 获取元素位置
                        const rect = el.getBoundingClientRect();
                        const position = {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            visible: rect.width > 0 && rect.height > 0
                        };
                        
                        // 构建选择器
                        let selector = '';
                        if (el.id) {
                            selector = `#${el.id}`;
                        } else if (el.className && typeof el.className === 'string') {
                            const classes = el.className.split(' ').filter(c => c.trim());
                            if (classes.length > 0) {
                                selector = `.${classes.join('.')}`;
                            }
                        }
                        
                        // 如果没有ID或类，使用标签名和属性
                        if (!selector) {
                            selector = el.tagName.toLowerCase();
                            if (el.name) {
                                selector += `[name="${el.name}"]`;
                            } else if (el.type && el.tagName.toLowerCase() === 'input') {
                                selector += `[type="${el.type}"]`;
                            }
                        }
                        
                        // 返回元素信息
                        return {
                            type,
                            text: text.trim(),
                            attributes,
                            position,
                            selector,
                            isInteractive: true
                        };
                    });
                }
                """
            )
            return elements_info or []
        except Exception:
            return []
    
    def _extract_text_content(self) -> str:
        """提取页面文本内容
        Returns:
            str: 页面文本内容
        """
        try:
            text_content = self.page.evaluate(
                """
                () => {
                    // 获取body元素
                    const body = document.body;
                    
                    // 创建一个函数来递归提取文本
                    function extractText(element, depth = 0) {
                        if (!element) return '';
                        
                        // 忽略脚本和样式元素
                        if (element.tagName === 'SCRIPT' || element.tagName === 'STYLE') {
                            return '';
                        }
                        
                        // 如果是文本节点，返回其文本内容
                        if (element.nodeType === Node.TEXT_NODE) {
                            const text = element.textContent.trim();
                            return text ? text + '\n' : '';
                        }
                        
                        // 如果是元素节点，递归提取其子节点的文本
                        let text = '';
                        for (const child of element.childNodes) {
                            text += extractText(child, depth + 1);
                        }
                        
                        return text;
                    }
                    
                    // 提取body的文本
                    return extractText(body).trim();
                }
                """
            )
            return text_content or ""
        except Exception:
            return ""
    
    def _identify_functional_areas(self) -> List[Dict[str, Any]]:
        """识别页面主要功能区域
        Returns:
            List[Dict[str, Any]]: 功能区域信息列表
        """
        functional_areas: List[Dict[str, Any]] = []
        try:
            # 识别搜索框
            search_inputs = self.page.query_selector_all('input[type="text"], input[type="search"]')
            for input_el in search_inputs:
                try:
                    if input_el.is_visible():
                        functional_areas.append({"type": "search_box", "selector": "input[type='text']"})
                        break  # 假设只有一个主要搜索框
                except Exception:
                    continue
            
            # 识别导航栏
            nav_elements = self.page.query_selector_all('nav, [role="navigation"]')
            if nav_elements:
                functional_areas.append({"type": "navigation_bar", "selector": "nav"})
                
            # 识别主要内容区
            main_content_elements = self.page.query_selector_all('main, article, #main, .main-content')
            if main_content_elements:
                functional_areas.append({"type": "main_content", "selector": "main"})
        except Exception:
            # 忽略识别错误，返回当前已识别的区域
            pass
        
        return functional_areas

    def _determine_page_type(self) -> str:
        """根据URL、标题和元素信息判断页面类型
        Returns:
            str: 页面类型（如"search_results", "product_page", "article", "generic"等）
        """
        try:
            url = getattr(self.page, "url", "") or ""
            title = ""
            try:
                title = self.page.title()
            except Exception:
                title = ""
            elements_info = self._extract_elements_info()
            
            if "search" in url.lower() or "s?wd=" in url.lower() or "q=" in url.lower():
                return "search_results"
            
            if "product" in url.lower() or "item" in url.lower() or "detail" in url.lower():
                return "product_page"
                
            if "article" in url.lower() or "blog" in url.lower() or "news" in url.lower():
                return "article_page"
                
            # 检查是否存在明显的表单元素
            if any(e.get('type') == 'form' for e in elements_info):
                return "form_page"
        except Exception:
            return "unknown"
        
        return "generic"