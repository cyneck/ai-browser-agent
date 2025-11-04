#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面监控器

负责监控DOM变化和动态内容加载，实现页面状态变更通知机制。
"""

import asyncio
import time
from typing import Dict, Any, List, Callable, Optional, Set
from threading import Lock, Event
from playwright.sync_api import Page

from src.common.logger import get_logger


class PageMonitor:
    """页面监控器类，负责监控页面变化和动态内容加载"""
    
    def __init__(self, page: Page):
        """初始化页面监控器
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.logger = get_logger()
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._listeners_lock = Lock()
        self._is_monitoring = False
        self._last_dom_state = None
        self._mutation_observer_script = None
        self._change_event = Event()
        self._loading_indicators = [
            'loading', 'spinner', 'loader', 'progress', 'skeleton',
            '[class*="loading"]', '[class*="spinner"]', '[class*="loader"]',
            '[class*="progress"]', '[class*="skeleton"]', '[aria-busy="true"]'
        ]
        
    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """添加页面变化监听器
        Args:
            callback: 页面变化时的回调函数，接收变化信息字典
        """
        with self._listeners_lock:
            if callback not in self._listeners:
                self._listeners.append(callback)
                self.logger.info(f"添加页面变化监听器: {callback.__name__}")
    
    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """移除页面变化监听器
        Args:
            callback: 要移除的回调函数
        """
        with self._listeners_lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
                self.logger.info(f"移除页面变化监听器: {callback.__name__}")
    
    def start_monitoring(self) -> None:
        """开始监控页面变化"""
        if self._is_monitoring:
            self.logger.warning("页面监控已经在运行中")
            return
            
        try:
            self._is_monitoring = True
            self._setup_mutation_observer()
            self._capture_initial_state()
            self.logger.info("开始监控页面变化")
        except Exception as e:
            self.logger.error(f"启动页面监控失败: {str(e)}")
            self._is_monitoring = False
    
    def stop_monitoring(self) -> None:
        """停止监控页面变化"""
        if not self._is_monitoring:
            return
            
        try:
            self._cleanup_mutation_observer()
            self._is_monitoring = False
            self.logger.info("停止监控页面变化")
        except Exception as e:
            self.logger.error(f"停止页面监控失败: {str(e)}")
    
    def wait_for_dynamic_content(self, timeout: float = 10.0, stable_time: float = 1.0) -> bool:
        """等待动态内容加载完成（智能等待策略）
        Args:
            timeout: 最大等待时间（秒）
            stable_time: 页面稳定时间（秒），页面在此时间内无变化则认为加载完成
        Returns:
            bool: 是否成功等待到稳定状态
        """
        try:
            start_time = time.time()
            last_change_time = start_time
            
            # 清除之前的事件状态
            self._change_event.clear()
            
            # 设置临时的变化监听器
            def temp_listener(change_info):
                nonlocal last_change_time
                last_change_time = time.time()
                self._change_event.set()
                self._change_event.clear()
            
            self.add_listener(temp_listener)
            
            try:
                # 智能等待策略
                while time.time() - start_time < timeout:
                    current_time = time.time()
                    
                    # 检查是否有加载指示器
                    if self._has_loading_indicators():
                        self.logger.debug("检测到加载指示器，继续等待...")
                        last_change_time = current_time
                        time.sleep(0.2)
                        continue
                    
                    # 检查网络活动
                    if self._has_network_activity():
                        self.logger.debug("检测到网络活动，继续等待...")
                        last_change_time = current_time
                        time.sleep(0.2)
                        continue
                    
                    # 检查JavaScript执行状态
                    if self._is_javascript_busy():
                        self.logger.debug("检测到JavaScript执行，继续等待...")
                        last_change_time = current_time
                        time.sleep(0.2)
                        continue
                    
                    # 如果页面在stable_time内没有变化，认为加载完成
                    if current_time - last_change_time >= stable_time:
                        self.logger.info(f"页面已稳定 {stable_time} 秒，动态内容加载完成")
                        return True
                    
                    # 等待一小段时间再检查
                    time.sleep(0.1)
                
                self.logger.warning(f"等待动态内容超时 ({timeout} 秒)")
                return False
                
            finally:
                self.remove_listener(temp_listener)
                
        except Exception as e:
            self.logger.error(f"等待动态内容时发生错误: {str(e)}")
            return False
    
    def wait_for_element_stable(self, selector: str, timeout: float = 10.0, stable_time: float = 1.0) -> bool:
        """等待特定元素稳定（位置和内容不再变化）
        Args:
            selector: 元素选择器
            timeout: 最大等待时间（秒）
            stable_time: 元素稳定时间（秒）
        Returns:
            bool: 是否成功等待到元素稳定
        """
        try:
            start_time = time.time()
            last_element_state = None
            last_change_time = start_time
            
            while time.time() - start_time < timeout:
                try:
                    # 获取元素当前状态
                    element_state = self.page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('{selector}');
                            if (!el) return null;
                            
                            const rect = el.getBoundingClientRect();
                            return {{
                                text: el.innerText || el.textContent || '',
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                visible: rect.width > 0 && rect.height > 0
                            }};
                        }}
                    """)
                    
                    # 比较状态是否发生变化
                    if element_state != last_element_state:
                        last_element_state = element_state
                        last_change_time = time.time()
                    
                    # 检查是否已稳定
                    if time.time() - last_change_time >= stable_time:
                        self.logger.info(f"元素 {selector} 已稳定 {stable_time} 秒")
                        return True
                    
                    time.sleep(0.1)
                    
                except Exception:
                    # 元素可能暂时不存在，继续等待
                    time.sleep(0.1)
            
            self.logger.warning(f"等待元素 {selector} 稳定超时 ({timeout} 秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"等待元素稳定时发生错误: {str(e)}")
            return False
    
    def detect_page_changes(self) -> Dict[str, Any]:
        """检测页面变化
        Returns:
            Dict[str, Any]: 页面变化信息
        """
        try:
            current_state = self._capture_current_state()
            
            if self._last_dom_state is None:
                self._last_dom_state = current_state
                return {"has_changes": False, "changes": []}
            
            changes = []
            
            # 检测URL变化
            if current_state["url"] != self._last_dom_state["url"]:
                changes.append({
                    "type": "url_change",
                    "old_value": self._last_dom_state["url"],
                    "new_value": current_state["url"]
                })
            
            # 检测标题变化
            if current_state["title"] != self._last_dom_state["title"]:
                changes.append({
                    "type": "title_change",
                    "old_value": self._last_dom_state["title"],
                    "new_value": current_state["title"]
                })
            
            # 检测元素数量变化
            if current_state["element_count"] != self._last_dom_state["element_count"]:
                changes.append({
                    "type": "element_count_change",
                    "old_value": self._last_dom_state["element_count"],
                    "new_value": current_state["element_count"]
                })
            
            # 检测内容变化
            if current_state["content_hash"] != self._last_dom_state["content_hash"]:
                changes.append({
                    "type": "content_change",
                    "description": "页面内容发生变化"
                })
            
            # 更新状态
            self._last_dom_state = current_state
            
            return {
                "has_changes": len(changes) > 0,
                "changes": changes,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"检测页面变化时发生错误: {str(e)}")
            return {"has_changes": False, "changes": [], "error": str(e)}
    
    def _setup_mutation_observer(self) -> None:
        """设置DOM变化观察器和网络活动监控"""
        try:
            self._mutation_observer_script = self.page.evaluate("""
                () => {
                    // 如果已经存在观察器，先断开
                    if (window._pageMonitorObserver) {
                        window._pageMonitorObserver.disconnect();
                    }
                    
                    // 初始化计数器
                    window._activeFetchCount = 0;
                    window._activeXHRCount = 0;
                    window._activeTimerCount = 0;
                    window._pendingPromiseCount = 0;
                    
                    // 监控fetch请求
                    const originalFetch = window.fetch;
                    window.fetch = function(...args) {
                        window._activeFetchCount++;
                        return originalFetch.apply(this, args).finally(() => {
                            window._activeFetchCount--;
                        });
                    };
                    
                    // 监控XMLHttpRequest
                    const originalXHROpen = XMLHttpRequest.prototype.open;
                    XMLHttpRequest.prototype.open = function(...args) {
                        window._activeXHRCount++;
                        this.addEventListener('loadend', () => {
                            window._activeXHRCount--;
                        });
                        return originalXHROpen.apply(this, args);
                    };
                    
                    // 监控setTimeout和setInterval
                    const originalSetTimeout = window.setTimeout;
                    const originalSetInterval = window.setInterval;
                    const originalClearTimeout = window.clearTimeout;
                    const originalClearInterval = window.clearInterval;
                    
                    window.setTimeout = function(callback, delay, ...args) {
                        window._activeTimerCount++;
                        const id = originalSetTimeout(() => {
                            window._activeTimerCount--;
                            callback.apply(this, args);
                        }, delay);
                        return id;
                    };
                    
                    window.setInterval = function(callback, delay, ...args) {
                        window._activeTimerCount++;
                        return originalSetInterval(callback, delay, ...args);
                    };
                    
                    window.clearTimeout = function(id) {
                        window._activeTimerCount = Math.max(0, window._activeTimerCount - 1);
                        return originalClearTimeout(id);
                    };
                    
                    window.clearInterval = function(id) {
                        window._activeTimerCount = Math.max(0, window._activeTimerCount - 1);
                        return originalClearInterval(id);
                    };
                    
                    // 创建DOM变化观察器
                    const observer = new MutationObserver((mutations) => {
                        const changeInfo = {
                            type: 'dom_mutation',
                            mutations: mutations.map(mutation => ({
                                type: mutation.type,
                                target: mutation.target.tagName || 'unknown',
                                addedNodes: mutation.addedNodes.length,
                                removedNodes: mutation.removedNodes.length,
                                attributeName: mutation.attributeName
                            })),
                            timestamp: Date.now(),
                            networkActivity: {
                                activeFetch: window._activeFetchCount,
                                activeXHR: window._activeXHRCount,
                                activeTimers: window._activeTimerCount
                            }
                        };
                        
                        // 触发自定义事件
                        window.dispatchEvent(new CustomEvent('pageMonitorChange', {
                            detail: changeInfo
                        }));
                    });
                    
                    // 开始观察
                    observer.observe(document.body || document.documentElement, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeOldValue: true,
                        characterData: true,
                        characterDataOldValue: true
                    });
                    
                    window._pageMonitorObserver = observer;
                    return true;
                }
            """)
            
            # 监听自定义事件
            self.page.expose_function("_handlePageChange", self._handle_page_change)
            self.page.evaluate("""
                () => {
                    window.addEventListener('pageMonitorChange', (event) => {
                        window._handlePageChange(event.detail);
                    });
                }
            """)
            
        except Exception as e:
            self.logger.error(f"设置DOM变化观察器失败: {str(e)}")
    
    def _cleanup_mutation_observer(self) -> None:
        """清理DOM变化观察器"""
        try:
            self.page.evaluate("""
                () => {
                    if (window._pageMonitorObserver) {
                        window._pageMonitorObserver.disconnect();
                        delete window._pageMonitorObserver;
                    }
                }
            """)
        except Exception as e:
            self.logger.error(f"清理DOM变化观察器失败: {str(e)}")
    
    def _handle_page_change(self, change_info: Dict[str, Any]) -> None:
        """处理页面变化事件"""
        try:
            # 通知所有监听器
            with self._listeners_lock:
                for listener in self._listeners:
                    try:
                        listener(change_info)
                    except Exception as e:
                        self.logger.error(f"调用监听器时发生错误: {str(e)}")
        except Exception as e:
            self.logger.error(f"处理页面变化事件时发生错误: {str(e)}")
    
    def _capture_initial_state(self) -> None:
        """捕获初始页面状态"""
        try:
            self._last_dom_state = self._capture_current_state()
        except Exception as e:
            self.logger.error(f"捕获初始页面状态失败: {str(e)}")
    
    def _capture_current_state(self) -> Dict[str, Any]:
        """捕获当前页面状态
        Returns:
            Dict[str, Any]: 当前页面状态信息
        """
        try:
            return self.page.evaluate("""
                () => {
                    // 计算内容哈希（简单版本）
                    const content = document.body ? document.body.innerText : '';
                    let hash = 0;
                    for (let i = 0; i < content.length; i++) {
                        const char = content.charCodeAt(i);
                        hash = ((hash << 5) - hash) + char;
                        hash = hash & hash; // 转换为32位整数
                    }
                    
                    return {
                        url: window.location.href,
                        title: document.title,
                        element_count: document.querySelectorAll('*').length,
                        content_hash: hash,
                        timestamp: Date.now()
                    };
                }
            """)
        except Exception as e:
            self.logger.error(f"捕获页面状态失败: {str(e)}")
            return {
                "url": "",
                "title": "",
                "element_count": 0,
                "content_hash": 0,
                "timestamp": time.time() * 1000
            }
    
    def _has_loading_indicators(self) -> bool:
        """检查页面是否有加载指示器
        Returns:
            bool: 是否存在加载指示器
        """
        try:
            for indicator in self._loading_indicators:
                elements = self.page.query_selector_all(indicator)
                for element in elements:
                    if element.is_visible():
                        return True
            return False
        except Exception:
            return False
    
    def _has_network_activity(self) -> bool:
        """检查是否有网络活动
        Returns:
            bool: 是否有活跃的网络请求
        """
        try:
            # 检查是否有正在进行的fetch请求或XMLHttpRequest
            has_activity = self.page.evaluate("""
                () => {
                    // 检查是否有活跃的fetch请求
                    if (window._activeFetchCount && window._activeFetchCount > 0) {
                        return true;
                    }
                    
                    // 检查是否有活跃的XMLHttpRequest
                    if (window._activeXHRCount && window._activeXHRCount > 0) {
                        return true;
                    }
                    
                    // 检查document.readyState
                    if (document.readyState === 'loading') {
                        return true;
                    }
                    
                    return false;
                }
            """)
            return has_activity
        except Exception:
            return False
    
    def _is_javascript_busy(self) -> bool:
        """检查JavaScript是否繁忙
        Returns:
            bool: JavaScript是否正在执行重要任务
        """
        try:
            is_busy = self.page.evaluate("""
                () => {
                    // 检查是否有定时器在运行
                    const hasActiveTimers = window._activeTimerCount && window._activeTimerCount > 0;
                    
                    // 检查是否有动画在运行
                    const hasActiveAnimations = document.getAnimations && document.getAnimations().length > 0;
                    
                    // 检查是否有Promise在pending状态
                    const hasPendingPromises = window._pendingPromiseCount && window._pendingPromiseCount > 0;
                    
                    return hasActiveTimers || hasActiveAnimations || hasPendingPromises;
                }
            """)
            return is_busy
        except Exception:
            return False
    
    def wait_for_element_appear(self, selector: str, timeout: float = 10.0) -> bool:
        """等待元素出现
        Args:
            selector: 元素选择器
            timeout: 最大等待时间（秒）
        Returns:
            bool: 元素是否出现
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    element = self.page.query_selector(selector)
                    if element and element.is_visible():
                        self.logger.info(f"元素 {selector} 已出现")
                        return True
                except Exception:
                    pass
                
                time.sleep(0.1)
            
            self.logger.warning(f"等待元素 {selector} 出现超时 ({timeout} 秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"等待元素出现时发生错误: {str(e)}")
            return False
    
    def wait_for_element_disappear(self, selector: str, timeout: float = 10.0) -> bool:
        """等待元素消失
        Args:
            selector: 元素选择器
            timeout: 最大等待时间（秒）
        Returns:
            bool: 元素是否消失
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    element = self.page.query_selector(selector)
                    if not element or not element.is_visible():
                        self.logger.info(f"元素 {selector} 已消失")
                        return True
                except Exception:
                    # 元素不存在也算消失
                    return True
                
                time.sleep(0.1)
            
            self.logger.warning(f"等待元素 {selector} 消失超时 ({timeout} 秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"等待元素消失时发生错误: {str(e)}")
            return False
    
    def wait_for_text_change(self, selector: str, initial_text: str = None, timeout: float = 10.0) -> bool:
        """等待元素文本内容变化
        Args:
            selector: 元素选择器
            initial_text: 初始文本内容，如果为None则自动获取
            timeout: 最大等待时间（秒）
        Returns:
            bool: 文本是否发生变化
        """
        try:
            # 获取初始文本
            if initial_text is None:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        initial_text = element.inner_text()
                    else:
                        initial_text = ""
                except Exception:
                    initial_text = ""
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        current_text = element.inner_text()
                        if current_text != initial_text:
                            self.logger.info(f"元素 {selector} 文本已变化")
                            return True
                except Exception:
                    pass
                
                time.sleep(0.1)
            
            self.logger.warning(f"等待元素 {selector} 文本变化超时 ({timeout} 秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"等待文本变化时发生错误: {str(e)}")
            return False
    
    def wait_for_page_load_complete(self, timeout: float = 30.0) -> bool:
        """等待页面完全加载完成（包括所有资源）
        Args:
            timeout: 最大等待时间（秒）
        Returns:
            bool: 页面是否完全加载完成
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # 检查document.readyState
                    ready_state = self.page.evaluate("document.readyState")
                    if ready_state != "complete":
                        time.sleep(0.1)
                        continue
                    
                    # 检查是否还有图片在加载
                    images_loading = self.page.evaluate("""
                        () => {
                            const images = document.querySelectorAll('img');
                            for (let img of images) {
                                if (!img.complete) {
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if images_loading:
                        time.sleep(0.1)
                        continue
                    
                    # 等待动态内容稳定
                    if self.wait_for_dynamic_content(timeout=5.0, stable_time=0.5):
                        self.logger.info("页面完全加载完成")
                        return True
                    
                except Exception:
                    pass
                
                time.sleep(0.1)
            
            self.logger.warning(f"等待页面完全加载超时 ({timeout} 秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"等待页面加载完成时发生错误: {str(e)}")
            return False
    
    def get_page_state_info(self) -> Dict[str, Any]:
        """获取页面状态的详细信息
        Returns:
            Dict[str, Any]: 页面状态信息，包括加载状态、网络活动等
        """
        try:
            state_info = self.page.evaluate("""
                () => {
                    // 获取基础页面信息
                    const basicInfo = {
                        url: window.location.href,
                        title: document.title,
                        readyState: document.readyState,
                        elementCount: document.querySelectorAll('*').length,
                        timestamp: Date.now()
                    };
                    
                    // 获取网络活动信息
                    const networkInfo = {
                        activeFetch: window._activeFetchCount || 0,
                        activeXHR: window._activeXHRCount || 0,
                        activeTimers: window._activeTimerCount || 0,
                        pendingPromises: window._pendingPromiseCount || 0
                    };
                    
                    // 获取加载指示器信息
                    const loadingSelectors = [
                        'loading', 'spinner', 'loader', 'progress', 'skeleton',
                        '[class*="loading"]', '[class*="spinner"]', '[class*="loader"]',
                        '[class*="progress"]', '[class*="skeleton"]', '[aria-busy="true"]'
                    ];
                    
                    let loadingElements = 0;
                    loadingSelectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    loadingElements++;
                                }
                            });
                        } catch (e) {
                            // 忽略选择器错误
                        }
                    });
                    
                    // 获取图片加载状态
                    const images = document.querySelectorAll('img');
                    let imagesLoading = 0;
                    let imagesTotal = images.length;
                    
                    images.forEach(img => {
                        if (!img.complete) {
                            imagesLoading++;
                        }
                    });
                    
                    // 获取动画状态
                    let activeAnimations = 0;
                    if (document.getAnimations) {
                        activeAnimations = document.getAnimations().length;
                    }
                    
                    return {
                        basic: basicInfo,
                        network: networkInfo,
                        loading: {
                            hasLoadingElements: loadingElements > 0,
                            loadingElementCount: loadingElements,
                            imagesLoading: imagesLoading,
                            imagesTotal: imagesTotal,
                            activeAnimations: activeAnimations
                        },
                        isStable: (
                            networkInfo.activeFetch === 0 &&
                            networkInfo.activeXHR === 0 &&
                            imagesLoading === 0 &&
                            loadingElements === 0 &&
                            basicInfo.readyState === 'complete'
                        )
                    };
                }
            """)
            
            return state_info
            
        except Exception as e:
            self.logger.error(f"获取页面状态信息时发生错误: {str(e)}")
            return {
                "basic": {"url": "", "title": "", "readyState": "unknown", "elementCount": 0, "timestamp": time.time() * 1000},
                "network": {"activeFetch": 0, "activeXHR": 0, "activeTimers": 0, "pendingPromises": 0},
                "loading": {"hasLoadingElements": False, "loadingElementCount": 0, "imagesLoading": 0, "imagesTotal": 0, "activeAnimations": 0},
                "isStable": False,
                "error": str(e)
            }
    
    def is_page_stable(self) -> bool:
        """检查页面是否处于稳定状态
        Returns:
            bool: 页面是否稳定
        """
        try:
            state_info = self.get_page_state_info()
            return state_info.get("isStable", False)
        except Exception as e:
            self.logger.error(f"检查页面稳定性时发生错误: {str(e)}")
            return False