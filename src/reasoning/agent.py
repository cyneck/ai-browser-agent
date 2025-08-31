#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浏览器代理

负责协调感知层、推理层和执行层，处理用户指令并执行网页自动化任务。
"""

import base64
import json
import time
import threading
from queue import Queue, Empty
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from src.common.config import get_config, get_human_behavior_config
from src.common.logger import get_logger
from src.perception.page_analyzer import PageAnalyzer
from src.reasoning.instruction_builder import InstructionBuilder
from src.action.executor import ActionExecutor
from src.action.state_manager import StateManager
from src.action.error_handler import ErrorHandler


class BrowserAgent:
    """
    浏览器代理类，协调各层组件执行用户指令。
    此类是线程安全的，通过专用的Playwright线程处理所有浏览器交互。
    """
    
    def __init__(self):
        """初始化浏览器代理"""
        self.logger = get_logger()
        self.initialized = False
        self._lock = threading.Lock()
        self._playwright_thread: Optional[threading.Thread] = None
        self._command_queue: Queue = Queue()
        self._result_queue: Queue = Queue()

        # 这些属性将在专用的Playwright线程中被初始化和使用
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.page_analyzer: Optional[PageAnalyzer] = None
        self.instruction_builder: Optional[InstructionBuilder] = None
        self.action_executor: Optional[ActionExecutor] = None
        self.state_manager: Optional[StateManager] = None
        self.error_handler: Optional[ErrorHandler] = None

    def initialize(self):
        """
        初始化浏览器代理，启动专用的Playwright线程。
        这个方法是线程安全的。
        """
        with self._lock:
            if self.initialized:
                return
            
            self._playwright_thread = threading.Thread(target=self._playwright_thread_loop, daemon=True)
            self._playwright_thread.start()
            
            # 等待线程初始化完成
            result = self._result_queue.get()
            if result.get("success"):
                self.initialized = True
                self.logger.info("浏览器代理初始化完成")
            else:
                error = result.get("error", "未知错误")
                self.logger.error(f"初始化浏览器代理时发生错误: {error}")
                raise RuntimeError(f"Failed to initialize BrowserAgent: {error}")

    def _playwright_thread_loop(self):
        """
        专用于Playwright操作的线程主循环。
        负责初始化浏览器和处理指令队列中的任务。
        """
        try:
            # 1. 初始化Playwright和浏览器组件
            browser_type = get_config("BROWSER_TYPE", "chromium")
            headless = get_config("HEADLESS", False)
            user_data_dir = get_config("USER_DATA_DIR", "./browser_data")
            Path(user_data_dir).mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"启动{browser_type}浏览器，headless={headless}")
            self.playwright = sync_playwright().start()
            browser_instance = getattr(self.playwright, browser_type)
            
            self.browser = browser_instance.launch(headless=headless)
            self.context = self.browser.new_context(user_agent="AI Browser Agent/1.0")
            self.page = self.context.new_page()
            
            self.page_analyzer = PageAnalyzer(self.page)
            self.instruction_builder = InstructionBuilder()
            self.state_manager = StateManager()
            self.error_handler = ErrorHandler()
            
            # 获取人类行为模拟配置
            behavior_config = get_human_behavior_config()
            self.action_executor = ActionExecutor(
                self.page, 
                self.state_manager, 
                self.error_handler,
                behavior_config
            )
            
            # 通知主线程初始化成功
            self._result_queue.put({"success": True})
        except Exception as e:
            self.logger.error(f"Playwright线程初始化失败: {e}", exc_info=True)
            self._result_queue.put({"success": False, "error": str(e)})
            return

        # 2. 开始处理指令循环
        while True:
            try:
                task = self._command_queue.get()
                if task is None:  # 哨兵值，表示退出
                    self.logger.info("Playwright线程收到退出信号")
                    break

                command = task["command"]
                args = task.get("args", [])
                kwargs = task.get("kwargs", {})
                
                # 根据指令调用相应的方法
                handler = getattr(self, f"_handle_{command}", None)
                if handler:
                    result = handler(*args, **kwargs)
                    self._result_queue.put(result)
                else:
                    self._result_queue.put({"success": False, "error": f"未知指令: {command}"})
            except Exception as e:
                self.logger.error(f"Playwright线程在处理任务时出错: {e}", exc_info=True)
                self._result_queue.put({"success": False, "error": str(e)})
        
        # 3. 循环结束后清理资源
        self._cleanup_resources()
        self.logger.info("Playwright线程已清理并退出")

    def execute(self, text: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        将执行自然语言文本的任务发送到Playwright线程并等待结果。
        """
        if not self.initialized:
            self.initialize()
        
        self._command_queue.put({
            "command": "execute",
            "kwargs": {"text": text, "session_state": session_state}
        })
        return self._result_queue.get()

    def _handle_execute(self, text: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """在Playwright线程内部实际执行任务"""
        try:
            self.logger.info(f"执行自然语言文本: {text}")
            
            page_data = {}
            try:
                analyzed = self.page_analyzer.analyze()
                page_data = analyzed if isinstance(analyzed, dict) and analyzed.get("is_valid", True) else {}
            except Exception as analyze_err:
                self.logger.warning(f"页面分析失败: {analyze_err}")

            try:
                json_instruction = self.instruction_builder.build_optimized(text, page_data, session_state)
            except Exception as build_err:
                self.logger.error(f"构建指令失败: {build_err}")
                json_instruction = {"action": "error", "error": str(build_err)}
            
            result = self.action_executor.execute(
                json_instruction,
                session_state,
                timeout=get_config("MAX_EXECUTION_TIME", 120)
            )
            
            screenshot = result.get("screenshot")
            if not screenshot and result.get("success", False) and result.get("take_screenshot", False):
                try:
                    screenshot_bytes = self.page.screenshot()
                    screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
                except Exception:
                    screenshot = None
            
            try:
                updated_page_data = self.page_analyzer.analyze()
            except Exception:
                updated_page_data = {}

            self.logger.info(f"执行完成，成功: {result.get('success', False)}")
            return {
                "success": result.get("success", False),
                "message": result.get("message", "执行完成"),
                "error": result.get("error"),
                "screenshot": screenshot,
                "session_state": session_state,
                "page_data": updated_page_data
            }
        except Exception as e:
            self.logger.error(f"执行指令时发生错误: {e}", exc_info=True)
            return {"success": False, "message": "执行失败", "error": str(e), "session_state": session_state}

    def cleanup(self):
        """清理资源，并向Playwright线程发送退出信号"""
        with self._lock:
            if not self.initialized or not self._playwright_thread:
                return
            
            self.logger.info("开始清理浏览器代理资源")
            try:
                # 发送退出信号
                self._command_queue.put(None)
                # 等待线程结束
                self._playwright_thread.join(timeout=10)
                if self._playwright_thread.is_alive():
                    self.logger.warning("Playwright线程在超时后仍未结束")
            except Exception as e:
                self.logger.error(f"清理过程中发生错误: {e}")
            finally:
                self._playwright_thread = None
                self.initialized = False
                self.logger.info("浏览器代理资源已清理")

    def _cleanup_resources(self):
        """在Playwright线程内部安全地关闭所有资源"""
        self.logger.info("开始关闭Playwright资源")
        resources = [self.page, self.context, self.browser]
        for resource in resources:
            if resource:
                try:
                    resource.close()
                except Exception as e:
                    self.logger.warning(f"关闭资源 {type(resource).__name__} 时出错: {e}")
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                self.logger.warning(f"停止Playwright时出错: {e}")
        self.logger.info("Playwright资源已关闭")

    # ---- 跨层接口封装 (通过队列与Playwright线程通信) ----
    
    def close(self) -> None:
        """关闭浏览器代理（与cleanup等价）"""
        self.cleanup()

    def process_instruction(self, instruction: str, session_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """兼容接口设计文档的对外入口"""
        return self.execute(instruction, session_state or {})

    def get_page_state(self) -> Dict[str, Any]:
        """获取当前页面状态"""
        if not self.initialized: self.initialize()
        self._command_queue.put({"command": "get_page_state"})
        return self._result_queue.get()

    def _handle_get_page_state(self) -> Dict[str, Any]:
        try:
            return self.page_analyzer.analyze()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def take_screenshot(self) -> Optional[bytes]:
        """截取当前页面截图"""
        if not self.initialized: self.initialize()
        self._command_queue.put({"command": "take_screenshot"})
        result = self._result_queue.get()
        return result if isinstance(result, bytes) else None

    def _handle_take_screenshot(self) -> Optional[bytes]:
        try:
            return self.page.screenshot()
        except Exception:
            return None

    def get_supported_actions(self) -> List[str]:
        if not self.initialized: self.initialize()
        # 这个方法不与Playwright直接交互，可以安全调用
        # 但为了保持一致性，我们也可以通过队列
        if not self.action_executor:
             # 如果线程还没初始化好，返回一个空列表或默认值
            return []
        return self.action_executor.get_supported_actions()
