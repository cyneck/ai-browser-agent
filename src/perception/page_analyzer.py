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
        """分析页面内容，生成页面意图图谱"""
        try:
            url = self._safe_get_url()
            title = self._safe_get_title()
            
            # 如果是空白页，直接返回无效分析
            if not url or url == "about:blank":
                return self._create_blank_page_data(url, title)
            
            self.logger.info(f"分析页面: {title} ({url})")
            
            # 构建页面意图图谱
            page_intent_graph = {
                "is_valid": True,
                "url": url,
                "title": title,
                "elements": self._extract_elements_info(),
                "text_content": self._extract_text_content(),
                "functional_areas": self._identify_functional_areas(),
                "page_type": self._determine_page_type(),
                "aria_snapshot": self._safe_get_aria_snapshot()
            }
            
            self.logger.info("页面分析完成")
            return page_intent_graph
        except Exception as e:
            self.logger.error(f"分析页面时发生错误: {str(e)}")
            return self._create_error_page_data(str(e))
    
    def _safe_get_url(self) -> str:
        """安全获取URL"""
        try:
            return getattr(self.page, "url", "") or ""
        except Exception:
            return ""
    
    def _safe_get_title(self) -> str:
        """安全获取标题"""
        try:
            return self.page.title()
        except Exception:
            return "空白页面"
    
    def _safe_get_aria_snapshot(self) -> Optional[Dict[str, Any]]:
        """安全获取ARIA快照"""
        try:
            return self.page.accessibility.snapshot()
        except Exception:
            return None
    
    def _create_blank_page_data(self, url: str, title: str) -> Dict[str, Any]:
        """创建空白页面数据"""
        return {
            "is_valid": False,
            "url": url,
            "title": title,
            "elements": [],
            "text_content": "",
            "functional_areas": [],
            "page_type": "blank",
            "aria_snapshot": None
        }
    
    def _create_error_page_data(self, error: str) -> Dict[str, Any]:
        """创建错误页面数据"""
        return {
            "is_valid": False,
            "url": self._safe_get_url(),
            "title": self._safe_get_title(),
            "elements": [],
            "text_content": "",
            "functional_areas": [],
            "page_type": "unknown",
            "aria_snapshot": None,
            "error": error
        }

    def get_aria_snapshot(self) -> Optional[Dict[str, Any]]:
        """获取页面的Aria Snapshot"""
        return self._safe_get_aria_snapshot()
    
    def _extract_elements_info(self) -> List[Dict[str, Any]]:
        """提取页面元素信息
        Returns:
            List[Dict[str, Any]]: 页面元素信息列表
        """
        try:
            elements_info = self.page.evaluate(
                r"""
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
                r"""
                () => {
                    // 获取body元素
                    const body = document.body;
                    if (!body) return '';
                    
                    // 使用更简单的方法提取所有文本内容
                    let text = body.innerText || body.textContent || '';
                    
                    // 清理多余的空格和换行
                    text = text.replace(/\s+/g, ' ').trim();
                    
                    return text;
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
        """根据URL判断页面类型"""
        try:
            url = self._safe_get_url().lower()
            if "search" in url or "s?wd=" in url or "q=" in url:
                return "search_results"
            if "product" in url or "item" in url or "detail" in url:
                return "product_page"
            if "article" in url or "blog" in url or "news" in url:
                return "article_page"
            return "generic"
        except Exception:
            return "unknown"