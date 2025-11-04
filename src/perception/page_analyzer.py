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
from src.perception.page_monitor import PageMonitor


class PageAnalyzer:
    """页面分析器类，负责提取网页的结构化信息"""
    
    def __init__(self, page: Page):
        """初始化页面分析器
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.logger = get_logger()
        self.page_monitor = PageMonitor(page)
    
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
        """提取页面元素信息，支持更多交互元素类型识别
        Returns:
            List[Dict[str, Any]]: 页面元素信息列表，包含增强的可见性、可操作性检测和智能选择器生成
        """
        try:
            elements_info = self.page.evaluate(
                """
                () => {
                    // 扩展的可交互元素选择器，支持更多元素类型
                    const interactiveElements = Array.from(document.querySelectorAll(
                        // 基础交互元素
                        'a, button, input, select, textarea, label, ' +
                        // ARIA角色元素
                        '[role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="tab"], ' +
                        '[role="menuitem"], [role="option"], [role="slider"], [role="spinbutton"], ' +
                        '[role="switch"], [role="textbox"], [role="combobox"], [role="listbox"], ' +
                        '[role="tree"], [role="grid"], [role="dialog"], [role="alertdialog"], ' +
                        '[role="banner"], [role="navigation"], [role="main"], [role="complementary"], ' +
                        '[role="contentinfo"], [role="search"], [role="form"], [role="region"], ' +
                        '[role="article"], [role="section"], [role="group"], [role="list"], ' +
                        '[role="listitem"], [role="table"], [role="row"], [role="cell"], ' +
                        '[role="columnheader"], [role="rowheader"], [role="tooltip"], ' +
                        '[role="status"], [role="alert"], [role="log"], [role="marquee"], ' +
                        '[role="timer"], [role="progressbar"], [role="scrollbar"], ' +
                        '[role="separator"], [role="presentation"], [role="img"], ' +
                        // 事件处理元素
                        '[onclick], [onmousedown], [onmouseup], [onkeydown], [onkeyup], ' +
                        '[onchange], [oninput], [onfocus], [onblur], [onsubmit], ' +
                        '[ondblclick], [oncontextmenu], [ondrag], [ondrop], ' +
                        // 可聚焦和可编辑元素
                        '[tabindex], [contenteditable="true"], [contenteditable=""], ' +
                        // 媒体和嵌入元素
                        'img[alt], img[title], video, audio, iframe, embed, object, canvas, svg, ' +
                        // 表单相关元素
                        'form, fieldset, legend, optgroup, option, datalist, output, progress, meter, ' +
                        // 交互式内容元素
                        'details, summary, [draggable="true"], [dropzone], ' +
                        // 自定义元素和组件
                        '[data-testid], [data-cy], [data-test], [data-automation], ' +
                        '[class*="btn"], [class*="button"], [class*="link"], [class*="menu"], ' +
                        '[class*="tab"], [class*="modal"], [class*="dialog"], [class*="dropdown"], ' +
                        '[class*="toggle"], [class*="switch"], [class*="slider"], [class*="input"], ' +
                        '[class*="select"], [class*="checkbox"], [class*="radio"], ' +
                        // 可点击的容器元素
                        'div[onclick], span[onclick], li[onclick], td[onclick], th[onclick], ' +
                        'div[role], span[role], li[role], td[role], th[role]'
                    ));
                    
                    // 增强的元素可见性检测函数
                    function isElementVisible(el) {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        // 基础可见性检查
                        const basicVisible = (
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            parseFloat(style.opacity) > 0 &&
                            rect.width > 0 &&
                            rect.height > 0
                        );
                        
                        if (!basicVisible) return false;
                        
                        // 检查元素是否在视口内或附近（考虑滚动）
                        const inViewportOrNear = (
                            rect.top < window.innerHeight + 100 &&  // 允许100px的缓冲区
                            rect.bottom > -100 &&
                            rect.left < window.innerWidth + 100 &&
                            rect.right > -100
                        );
                        
                        // 检查是否被其他元素遮挡（仅对小元素进行检查以提高性能）
                        let notObscured = true;
                        if (rect.width < 200 && rect.height < 200) {
                            const centerX = rect.left + rect.width / 2;
                            const centerY = rect.top + rect.height / 2;
                            const elementAtPoint = document.elementFromPoint(centerX, centerY);
                            notObscured = elementAtPoint === el || el.contains(elementAtPoint);
                        }
                        
                        // 检查父元素的overflow属性
                        let parent = el.parentElement;
                        let withinParentBounds = true;
                        while (parent && parent !== document.body) {
                            const parentStyle = window.getComputedStyle(parent);
                            if (parentStyle.overflow === 'hidden' || parentStyle.overflowX === 'hidden' || parentStyle.overflowY === 'hidden') {
                                const parentRect = parent.getBoundingClientRect();
                                if (rect.right < parentRect.left || rect.left > parentRect.right ||
                                    rect.bottom < parentRect.top || rect.top > parentRect.bottom) {
                                    withinParentBounds = false;
                                    break;
                                }
                            }
                            parent = parent.parentElement;
                        }
                        
                        return inViewportOrNear && notObscured && withinParentBounds;
                    }
                    
                    // 增强的元素可操作性检测函数
                    function isElementInteractable(el) {
                        const style = window.getComputedStyle(el);
                        
                        // 基础可操作性检查
                        const basicInteractable = (
                            !el.disabled &&
                            !el.readOnly &&
                            style.pointerEvents !== 'none' &&
                            (!el.hasAttribute('aria-disabled') || el.getAttribute('aria-disabled') !== 'true')
                        );
                        
                        if (!basicInteractable) return false;
                        
                        // 检查表单元素的特殊状态
                        if (el.tagName.toLowerCase() === 'input') {
                            const inputType = el.type.toLowerCase();
                            // 隐藏的input元素通常不可交互
                            if (inputType === 'hidden') return false;
                            // 只读的input元素
                            if (el.hasAttribute('readonly')) return false;
                        }
                        
                        // 检查是否在禁用的fieldset中
                        let parent = el.parentElement;
                        while (parent) {
                            if (parent.tagName.toLowerCase() === 'fieldset' && parent.disabled) {
                                return false;
                            }
                            parent = parent.parentElement;
                        }
                        
                        // 检查CSS cursor属性（提示可交互性）
                        const cursor = style.cursor;
                        const interactiveCursors = ['pointer', 'hand', 'grab', 'grabbing', 'zoom-in', 'zoom-out'];
                        const hasInteractiveCursor = interactiveCursors.includes(cursor);
                        
                        // 检查是否有交互事件监听器
                        const hasEventListeners = (
                            el.onclick !== null ||
                            el.onmousedown !== null ||
                            el.onmouseup !== null ||
                            el.onkeydown !== null ||
                            el.onkeyup !== null ||
                            el.onchange !== null ||
                            el.oninput !== null ||
                            el.onfocus !== null ||
                            el.onsubmit !== null
                        );
                        
                        // 检查tabindex属性
                        const tabIndex = el.getAttribute('tabindex');
                        const isFocusable = tabIndex !== null && tabIndex !== '-1';
                        
                        // 综合判断：基础可操作性 + (交互光标 或 事件监听器 或 可聚焦)
                        return basicInteractable && (hasInteractiveCursor || hasEventListeners || isFocusable || 
                                                   ['a', 'button', 'input', 'select', 'textarea'].includes(el.tagName.toLowerCase()));
                    }
                    
                    // 增强的智能选择器生成函数
                    function generateSmartSelectors(el) {
                        const selectors = [];
                        
                        // 1. ID选择器（最高优先级）
                        if (el.id && el.id.trim()) {
                            selectors.push({
                                type: 'css',
                                value: `#${CSS.escape(el.id)}`,
                                priority: 1,
                                reliability: 'high'
                            });
                        }
                        
                        // 2. 测试属性选择器（高优先级，用于自动化测试）
                        const testAttributes = ['data-testid', 'data-cy', 'data-test', 'data-automation', 'data-qa'];
                        for (const attr of testAttributes) {
                            const value = el.getAttribute(attr);
                            if (value && value.trim()) {
                                selectors.push({
                                    type: 'css',
                                    value: `[${attr}="${CSS.escape(value)}"]`,
                                    priority: 2,
                                    reliability: 'high'
                                });
                                break; // 只取第一个找到的测试属性
                            }
                        }
                        
                        // 3. Name属性选择器（表单元素）
                        if (el.name && el.name.trim()) {
                            const nameSelector = `[name="${CSS.escape(el.name)}"]`;
                            if (document.querySelectorAll(nameSelector).length === 1) {
                                selectors.push({
                                    type: 'css',
                                    value: nameSelector,
                                    priority: 3,
                                    reliability: 'high'
                                });
                            }
                        }
                        
                        // 4. 唯一类名组合选择器
                        if (el.className && typeof el.className === 'string') {
                            const classes = el.className.split(' ').filter(c => c.trim() && !c.includes(' '));
                            if (classes.length > 0) {
                                // 尝试不同的类名组合
                                for (let i = 1; i <= Math.min(classes.length, 3); i++) {
                                    const classSelector = `.${classes.slice(0, i).map(c => CSS.escape(c)).join('.')}`;
                                    const matches = document.querySelectorAll(classSelector);
                                    if (matches.length === 1) {
                                        selectors.push({
                                            type: 'css',
                                            value: classSelector,
                                            priority: 4,
                                            reliability: 'medium'
                                        });
                                        break;
                                    }
                                }
                            }
                        }
                        
                        // 5. 属性组合选择器
                        const tagName = el.tagName.toLowerCase();
                        if (el.type && tagName === 'input') {
                            const typeSelector = `input[type="${CSS.escape(el.type)}"]`;
                            const matches = document.querySelectorAll(typeSelector);
                            selectors.push({
                                type: 'css',
                                value: typeSelector,
                                priority: matches.length === 1 ? 5 : 7,
                                reliability: matches.length === 1 ? 'medium' : 'low'
                            });
                        }
                        
                        // 6. ARIA标签选择器
                        const ariaLabel = el.getAttribute('aria-label');
                        if (ariaLabel && ariaLabel.trim()) {
                            selectors.push({
                                type: 'css',
                                value: `[aria-label="${CSS.escape(ariaLabel)}"]`,
                                priority: 6,
                                reliability: 'medium'
                            });
                        }
                        
                        // 7. 文本选择器（增强版）
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text && text.length > 0 && text.length < 100) {
                            const escapedText = text.replace(/"/g, '\\"');
                            
                            // 精确文本匹配
                            if (['a', 'button'].includes(tagName) || el.getAttribute('role') === 'button' || el.getAttribute('role') === 'link') {
                                selectors.push({
                                    type: 'text',
                                    value: `text="${escapedText}"`,
                                    priority: 8,
                                    reliability: 'medium'
                                });
                            }
                            
                            // 部分文本匹配（对于较长的文本）
                            if (text.length > 20) {
                                const shortText = text.substring(0, 20).trim();
                                selectors.push({
                                    type: 'text',
                                    value: `text*="${shortText.replace(/"/g, '\\"')}"`,
                                    priority: 9,
                                    reliability: 'low'
                                });
                            }
                        }
                        
                        // 8. 占位符文本选择器
                        const placeholder = el.getAttribute('placeholder');
                        if (placeholder && placeholder.trim()) {
                            selectors.push({
                                type: 'css',
                                value: `[placeholder="${CSS.escape(placeholder)}"]`,
                                priority: 10,
                                reliability: 'medium'
                            });
                        }
                        
                        // 9. 增强的XPath选择器
                        function getSmartXPath(element) {
                            // 优先使用ID
                            if (element.id) {
                                return `//*[@id="${element.id}"]`;
                            }
                            
                            // 使用测试属性
                            for (const attr of testAttributes) {
                                const value = element.getAttribute(attr);
                                if (value) {
                                    return `//*[@${attr}="${value}"]`;
                                }
                            }
                            
                            // 使用文本内容（对于链接和按钮）
                            if (text && text.length < 50 && ['a', 'button'].includes(element.tagName.toLowerCase())) {
                                return `//${element.tagName.toLowerCase()}[text()="${text}"]`;
                            }
                            
                            // 构建结构化路径
                            let path = '';
                            let current = element;
                            
                            while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
                                let selector = current.nodeName.toLowerCase();
                                
                                // 使用ID作为锚点
                                if (current.id) {
                                    selector += `[@id="${current.id}"]`;
                                    path = '//' + selector + path;
                                    break;
                                }
                                
                                // 使用类名或其他属性来区分同级元素
                                const siblings = Array.from(current.parentElement?.children || [])
                                    .filter(el => el.tagName === current.tagName);
                                
                                if (siblings.length > 1) {
                                    const index = siblings.indexOf(current) + 1;
                                    selector += `[${index}]`;
                                }
                                
                                path = '/' + selector + path;
                                current = current.parentElement;
                            }
                            
                            return path || `//${element.tagName.toLowerCase()}`;
                        }
                        
                        selectors.push({
                            type: 'xpath',
                            value: getSmartXPath(el),
                            priority: 11,
                            reliability: 'low'
                        });
                        
                        // 10. CSS结构选择器（最后备选）
                        function getStructuralSelector(element) {
                            let path = [];
                            let current = element;
                            
                            while (current && current !== document.body && path.length < 5) {
                                let selector = current.tagName.toLowerCase();
                                
                                if (current.id) {
                                    selector = `#${CSS.escape(current.id)}`;
                                    path.unshift(selector);
                                    break;
                                }
                                
                                if (current.className && typeof current.className === 'string') {
                                    const classes = current.className.split(' ').filter(c => c.trim());
                                    if (classes.length > 0) {
                                        selector += `.${classes[0]}`;
                                    }
                                }
                                
                                path.unshift(selector);
                                current = current.parentElement;
                            }
                            
                            return path.join(' > ');
                        }
                        
                        selectors.push({
                            type: 'css',
                            value: getStructuralSelector(el),
                            priority: 12,
                            reliability: 'low'
                        });
                        
                        // 按优先级和可靠性排序
                        selectors.sort((a, b) => {
                            if (a.priority !== b.priority) {
                                return a.priority - b.priority;
                            }
                            // 相同优先级时，按可靠性排序
                            const reliabilityOrder = { 'high': 1, 'medium': 2, 'low': 3 };
                            return reliabilityOrder[a.reliability] - reliabilityOrder[b.reliability];
                        });
                        
                        return selectors;
                    }
                    
                    // 提取增强的元素信息
                    return interactiveElements.map(el => {
                        // 获取元素文本信息
                        const text = (el.innerText || el.textContent || '').trim();
                        const altText = (el.getAttribute('alt') || '').trim();
                        const ariaLabel = (el.getAttribute('aria-label') || '').trim();
                        const title = (el.getAttribute('title') || '').trim();
                        const placeholder = (el.getAttribute('placeholder') || '').trim();
                        const value = el.value || '';
                        
                        // 获取增强的元素类型信息
                        let type = el.tagName.toLowerCase();
                        let subType = '';
                        
                        if (el.hasAttribute('role')) {
                            type = el.getAttribute('role');
                        }
                        
                        if (el.tagName.toLowerCase() === 'input') {
                            type = 'input';
                            subType = el.type || 'text';
                        }
                        
                        // 检测特殊元素类型
                        if (el.tagName.toLowerCase() === 'div' || el.tagName.toLowerCase() === 'span') {
                            if (el.getAttribute('role') || el.hasAttribute('onclick') || el.getAttribute('tabindex')) {
                                type = 'interactive-container';
                                subType = el.getAttribute('role') || 'clickable';
                            }
                        }
                        
                        // 获取所有属性
                        const attributes = {};
                        Array.from(el.attributes).forEach(attr => {
                            attributes[attr.name] = attr.value;
                        });
                        
                        // 获取增强的位置和可见性信息
                        const rect = el.getBoundingClientRect();
                        const isVisible = isElementVisible(el);
                        const isInteractable = isElementInteractable(el);
                        
                        const position = {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            centerX: Math.round(rect.x + rect.width / 2),
                            centerY: Math.round(rect.y + rect.height / 2),
                            visible: isVisible,
                            inViewport: rect.top >= 0 && rect.left >= 0 && 
                                       rect.bottom <= window.innerHeight && 
                                       rect.right <= window.innerWidth,
                            partiallyInViewport: rect.bottom > 0 && rect.right > 0 && 
                                               rect.top < window.innerHeight && rect.left < window.innerWidth
                        };
                        
                        // 生成智能选择器
                        const selectors = generateSmartSelectors(el);
                        
                        // 增强的交互能力检测
                        const tagName = el.tagName.toLowerCase();
                        const role = el.getAttribute('role');
                        
                        const canClick = isVisible && isInteractable && (
                            tagName === 'button' ||
                            tagName === 'a' ||
                            role === 'button' ||
                            role === 'link' ||
                            role === 'tab' ||
                            role === 'menuitem' ||
                            role === 'option' ||
                            el.hasAttribute('onclick') ||
                            el.hasAttribute('onmousedown') ||
                            el.getAttribute('tabindex') !== null
                        );
                        
                        const canType = isVisible && isInteractable && (
                            (tagName === 'input' && !['button', 'submit', 'reset', 'checkbox', 'radio', 'file', 'image'].includes(el.type)) ||
                            tagName === 'textarea' ||
                            el.getAttribute('contenteditable') === 'true' ||
                            el.getAttribute('contenteditable') === '' ||
                            role === 'textbox'
                        );
                        
                        const canSelect = isVisible && isInteractable && (
                            tagName === 'select' ||
                            role === 'listbox' ||
                            role === 'combobox' ||
                            (tagName === 'input' && ['checkbox', 'radio'].includes(el.type))
                        );
                        
                        const canDrag = isVisible && isInteractable && (
                            el.getAttribute('draggable') === 'true' ||
                            role === 'slider'
                        );
                        
                        const canFocus = isVisible && (
                            el.getAttribute('tabindex') !== null ||
                            ['a', 'button', 'input', 'select', 'textarea'].includes(tagName) ||
                            el.getAttribute('contenteditable') === 'true'
                        );
                        
                        // 检测元素的语义信息
                        const semanticInfo = {
                            isFormElement: ['input', 'select', 'textarea', 'button'].includes(tagName) || 
                                          ['textbox', 'combobox', 'listbox', 'button'].includes(role),
                            isNavigationElement: tagName === 'a' || role === 'link' || role === 'tab',
                            isMediaElement: ['img', 'video', 'audio', 'iframe'].includes(tagName),
                            isContainerElement: ['div', 'span', 'section', 'article'].includes(tagName),
                            hasLabel: !!(ariaLabel || title || placeholder || 
                                       (tagName === 'input' && el.labels && el.labels.length > 0)),
                            isRequired: el.hasAttribute('required') || el.getAttribute('aria-required') === 'true',
                            isDisabled: el.disabled || el.getAttribute('aria-disabled') === 'true'
                        };
                        
                        // 返回增强的元素信息
                        return {
                            // 基础信息
                            type,
                            subType,
                            tagName,
                            
                            // 文本信息
                            text,
                            altText,
                            ariaLabel,
                            title,
                            placeholder,
                            value,
                            
                            // 属性和位置
                            attributes,
                            position,
                            
                            // 选择器信息
                            selectors,
                            selector: selectors[0]?.value || tagName, // 主选择器
                            bestSelector: selectors.find(s => s.reliability === 'high')?.value || selectors[0]?.value,
                            
                            // 状态信息
                            isInteractive: true,
                            isVisible,
                            isInteractable,
                            
                            // 交互能力
                            canClick,
                            canType,
                            canSelect,
                            canDrag,
                            canFocus,
                            
                            // 语义信息
                            semanticInfo,
                            
                            // 元数据
                            extractedAt: Date.now(),
                            confidence: isVisible && isInteractable ? 
                                       (selectors.find(s => s.reliability === 'high') ? 0.9 : 0.7) : 0.5
                        };
                    }).filter(el => el.isVisible || el.semanticInfo.isFormElement); // 返回可见元素或重要的表单元素
                }
                """
            )
            return elements_info or []
        except Exception as e:
            self.logger.error(f"提取元素信息时发生错误: {str(e)}")
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
    
    def start_monitoring(self) -> None:
        """开始监控页面变化"""
        self.page_monitor.start_monitoring()
    
    def stop_monitoring(self) -> None:
        """停止监控页面变化"""
        self.page_monitor.stop_monitoring()
    
    def add_change_listener(self, callback) -> None:
        """添加页面变化监听器"""
        self.page_monitor.add_listener(callback)
    
    def remove_change_listener(self, callback) -> None:
        """移除页面变化监听器"""
        self.page_monitor.remove_listener(callback)
    
    def wait_for_dynamic_content(self, timeout: float = 10.0, stable_time: float = 1.0) -> bool:
        """等待动态内容加载完成"""
        return self.page_monitor.wait_for_dynamic_content(timeout, stable_time)
    
    def wait_for_element_stable(self, selector: str, timeout: float = 10.0, stable_time: float = 1.0) -> bool:
        """等待特定元素稳定"""
        return self.page_monitor.wait_for_element_stable(selector, timeout, stable_time)
    
    def detect_page_changes(self) -> Dict[str, Any]:
        """检测页面变化"""
        return self.page_monitor.detect_page_changes()
    
    def analyze_with_dynamic_content(self, wait_for_stable: bool = True, timeout: float = 10.0) -> Dict[str, Any]:
        """分析页面内容，包括等待动态内容加载
        Args:
            wait_for_stable: 是否等待页面稳定
            timeout: 等待超时时间
        Returns:
            Dict[str, Any]: 页面意图图谱
        """
        try:
            if wait_for_stable:
                self.logger.info("等待动态内容加载完成...")
                self.wait_for_dynamic_content(timeout=timeout)
            
            return self.analyze()
        except Exception as e:
            self.logger.error(f"分析动态页面内容时发生错误: {str(e)}")
            return self.analyze()  # 降级到普通分析