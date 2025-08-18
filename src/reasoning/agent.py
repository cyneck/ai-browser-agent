#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浏览器代理

负责协调感知层、推理层和执行层，处理用户指令并执行网页自动化任务。
"""

import base64
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from src.common.config import get_config
from src.common.logger import get_logger
from src.perception.page_analyzer import PageAnalyzer
from src.reasoning.instruction_builder import InstructionBuilder
from src.action.executor import ActionExecutor
from src.action.state_manager import StateManager
from src.action.error_handler import ErrorHandler


class BrowserAgent:
    """浏览器代理类，协调各层组件执行用户指令"""
    
    def __init__(self):
        """初始化浏览器代理"""
        self.logger = get_logger()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.page_analyzer: Optional[PageAnalyzer] = None
        self.instruction_builder: Optional[InstructionBuilder] = None
        self.action_executor: Optional[ActionExecutor] = None
        self.state_manager: Optional[StateManager] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.initialized = False
    
    def initialize(self):
        """初始化浏览器和各层组件"""
        if self.initialized:
            return
        
        try:
            # 获取配置
            browser_type = get_config("BROWSER_TYPE", "chromium")
            headless = get_config("HEADLESS", False)
            user_data_dir = get_config("USER_DATA_DIR", "./browser_data")
            
            # 确保用户数据目录存在
            Path(user_data_dir).mkdir(parents=True, exist_ok=True)
            
            # 启动浏览器
            self.logger.info(f"启动{browser_type}浏览器，headless={headless}")
            self.playwright = sync_playwright().start()
            browser_instance = getattr(self.playwright, browser_type)
            
            # 创建持久化的浏览器上下文
            self.browser = browser_instance.launch(headless=headless)
            self.context = self.browser.new_context(user_agent="AI Browser Agent/1.0")
            self.page = self.context.new_page()
            
            # 初始化各层组件
            self.page_analyzer = PageAnalyzer()
            self.instruction_builder = InstructionBuilder()
            self.state_manager = StateManager()
            self.error_handler = ErrorHandler()
            self.action_executor = ActionExecutor(self.page, state_manager=self.state_manager, error_handler=self.error_handler)
            
            self.initialized = True
            self.logger.info("浏览器代理初始化完成")
        except Exception as e:
            self.logger.error(f"初始化浏览器代理时发生错误: {str(e)}")
            self.cleanup()
            raise
    
    def execute(self, instruction: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户指令
        
        Args:
            instruction: 用户的自然语言指令
            session_state: 会话状态，用于保存多轮对话的上下文
            
        Returns:
            Dict[str, Any]: 执行结果，包含success、message、error等字段
        """
        if not self.initialized:
            self.initialize()
        
        try:
            # 记录指令
            self.logger.info(f"执行指令: {instruction}")
            
            # 分析当前页面
            page_data = self.page_analyzer.analyze(self.page)
            
            # 构建指令
            json_instruction = self.instruction_builder.build(
                instruction,
                page_data,
                session_state
            )
            
            # 执行指令
            start_time = time.time()
            max_execution_time = get_config("MAX_EXECUTION_TIME", 60)
            
            result = self.action_executor.execute(
                json_instruction,
                session_state,
                timeout=max_execution_time
            )
            
            execution_time = time.time() - start_time
            self.logger.info(f"指令执行完成，耗时: {execution_time:.2f}秒")
            
            # 截图（可选）
            screenshot = None
            if result.get("success", False) and result.get("take_screenshot", False):
                screenshot_bytes = self.page.screenshot()
                screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
            
            # 执行后重新感知，形成闭环
            updated_page_data = self.page_analyzer.analyze(self.page)

            # 构建返回结果
            return {
                "success": result.get("success", False),
                "message": result.get("message", "执行完成"),
                "error": result.get("error"),
                "screenshot": screenshot,
                "session_state": session_state,
                "page_data": updated_page_data
            }
        except Exception as e:
            self.logger.error(f"执行指令时发生错误: {str(e)}")
            return {
                "success": False,
                "message": "执行失败",
                "error": str(e),
                "session_state": session_state
            }

    # ---- 跨层接口封装 ----
    def close(self) -> None:
        """关闭浏览器代理（与cleanup等价）"""
        self.cleanup()

    def process_instruction(self, instruction: str, session_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """兼容接口设计文档的对外入口"""
        return self.execute(instruction, session_state or {})

    def get_page_state(self) -> Dict[str, Any]:
        """获取当前页面状态（意图图谱/摘要）"""
        if not self.initialized:
            self.initialize()
        return self.page_analyzer.analyze(self.page)

    def take_screenshot(self) -> bytes:
        """截取当前页面截图"""
        if not self.initialized:
            self.initialize()
        return self.page.screenshot()

    def get_supported_actions(self) -> List[str]:
        if not self.initialized:
            self.initialize()
        return self.action_executor.get_supported_actions()
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("清理浏览器代理资源")
        
        # 关闭浏览器
        if self.page:
            try:
                self.page.close()
            except:
                pass
            self.page = None
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
            self.context = None
        
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
            self.browser = None
        
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
            self.playwright = None
        
        # 重置状态
        self.initialized = False
        self.logger.info("浏览器代理资源已清理")