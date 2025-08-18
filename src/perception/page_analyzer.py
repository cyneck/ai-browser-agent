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
    
    def __init__(self):
        """初始化页面分析器"""
        self.logger = get_logger()
    
    def analyze(self, page: Page) -> Dict[str, Any]:
        """分析页面内容，生成页面意图图谱
        
        Args:
            page: Playwright页面对象
            
        Returns:
            Dict[str, Any]: 页面意图图谱，包含页面的结构化信息
        """
        try:
            # 获取页面基本信息
            url = page.url
            title = page.title()
            
            self.logger.info(f"分析页面: {title} ({url})")
            
            # 提取页面元素信息
            elements_info = self._extract_elements_info(page)
            
            # 提取页面文本内容
            text_content = self._extract_text_content(page)
            
            # 识别页面主要功能区域
            functional_areas = self._identify_functional_areas(page)
            
            # 构建页面意图图谱
            page_intent_graph = {
                "url": url,
                "title": title,
                "elements": elements_info,
                "text_content": text_content,
                "functional_areas": functional_areas,
                "page_type": self._determine_page_type(url, title, elements_info)
            }
            
            self.logger.info("页面分析完成")
            return page_intent_graph
        except Exception as e:
            self.logger.error(f"分析页面时发生错误: {str(e)}")
            # 返回基本信息
            return {
                "url": page.url,
                "title": page.title() if page.url != "about:blank" else "空白页面",
                "elements": [],
                "text_content": "",
                "functional_areas": [],
                "page_type": "unknown",
                "error": str(e)
            }
    
    def _extract_elements_info(self, page: Page) -> List[Dict[str, Any]]:
        """提取页面元素信息
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[Dict[str, Any]]: 页面元素信息列表
        """
        # 使用JavaScript提取页面元素信息
        elements_info = page.evaluate("""
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
        """)
        
        return elements_info
    
    def _extract_text_content(self, page: Page) -> str:
        """提取页面文本内容
        
        Args:
            page: Playwright页面对象
            
        Returns:
            str: 页面文本内容
        """
        # 使用JavaScript提取页面文本内容
        text_content = page.evaluate("""
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
        """)
        
        return text_content
    
    def _identify_functional_areas(self, page: Page) -> List[Dict[str, Any]]:
        """识别页面主要功能区域
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[Dict[str, Any]]: 功能区域信息列表
        """
        # 使用JavaScript识别页面主要功能区域
        functional_areas = page.evaluate("""
            () => {
                // 定义可能的功能区域选择器
                const areaSelectors = {
                    'header': 'header, .header, #header, [role="banner"]',
                    'navigation': 'nav, .nav, #nav, [role="navigation"]',
                    'search': '.search, #search, [role="search"], form[action*="search"]',
                    'main': 'main, .main, #main, [role="main"]',
                    'content': '.content, #content, article, .article',
                    'sidebar': 'aside, .sidebar, #sidebar, [role="complementary"]',
                    'footer': 'footer, .footer, #footer, [role="contentinfo"]',
                    'login': '.login, #login, form[action*="login"]',
                    'signup': '.signup, #signup, form[action*="register"], form[action*="signup"]',
                    'cart': '.cart, #cart, [class*="cart"], [id*="cart"]',
                    'product': '.product, #product, [class*="product"], [id*="product"]'
                };
                
                // 识别功能区域
                const areas = [];
                for (const [areaType, selector] of Object.entries(areaSelectors)) {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        // 获取区域位置
                        const rect = el.getBoundingClientRect();
                        
                        // 只添加可见的区域
                        if (rect.width > 0 && rect.height > 0) {
                            areas.push({
                                type: areaType,
                                selector: selector,
                                position: {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                },
                                elements: Array.from(el.querySelectorAll('a, button, input')).length
                            });
                        }
                    }
                }
                
                return areas;
            }
        """)
        
        return functional_areas
    
    def _determine_page_type(self, url: str, title: str, elements: List[Dict[str, Any]]) -> str:
        """确定页面类型
        
        Args:
            url: 页面URL
            title: 页面标题
            elements: 页面元素信息
            
        Returns:
            str: 页面类型
        """
        # 基于URL、标题和元素特征确定页面类型
        url_lower = url.lower()
        title_lower = title.lower()
        
        # 检查是否是登录页面
        if "login" in url_lower or "signin" in url_lower or "登录" in title_lower or "登入" in title_lower:
            return "login"
        
        # 检查是否是注册页面
        if "register" in url_lower or "signup" in url_lower or "注册" in title_lower:
            return "signup"
        
        # 检查是否是搜索结果页面
        if "search" in url_lower or "搜索" in title_lower or "查询" in title_lower:
            return "search_results"
        
        # 检查是否是商品详情页面
        if "product" in url_lower or "item" in url_lower or "detail" in url_lower or "商品" in title_lower or "详情" in title_lower:
            return "product_detail"
        
        # 检查是否是购物车页面
        if "cart" in url_lower or "购物车" in title_lower:
            return "shopping_cart"
        
        # 检查是否是结算页面
        if "checkout" in url_lower or "payment" in url_lower or "结算" in title_lower or "支付" in title_lower:
            return "checkout"
        
        # 检查是否是首页
        if url.endswith("/") or url.endswith("/index.html") or "首页" in title_lower or "主页" in title_lower:
            return "homepage"
        
        # 默认为通用页面
        return "generic"