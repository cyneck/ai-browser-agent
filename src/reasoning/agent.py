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
            self.page_analyzer = PageAnalyzer(self.page)
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

    def _is_navigation_only(self, instruction: Dict[str, Any]) -> bool:
        """判断指令是否仅包含导航/等待步骤"""
        try:
            if not instruction:
                return False
            if instruction.get("action") == "navigate":
                return True
            steps = instruction.get("steps")
            if not isinstance(steps, list):
                return False
            allowed = {"navigate", "wait"}
            has_nav = False
            for step in steps:
                action = step.get("action")
                if action == "navigate":
                    has_nav = True
                if action not in allowed:
                    return False
            return has_nav
        except Exception:
            return False
    
    def execute(self, text: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户自然语言文本
        
        Args:
            text: 用户输入的自然语言文本（例如："在bing网站检索北京秋天"）
            session_state: 会话状态，用于保存多轮对话的上下文
            
        Returns:
            Dict[str, Any]: 执行结果，包含success、message、error等字段
            
        注意：
            - text参数是用户输入的自然语言文本
            - 系统内部会将text转换为executable JSON instruction进行执行
            - instruction特指系统内部使用的JSON格式可执行指令
        """
        if not self.initialized:
            self.initialize()
        
        try:
            self.logger.info(f"执行自然语言文本: {text}")
            
            # 第一次分析（容错）
            page_data = {}
            try:
                analyzed = self.page_analyzer.analyze()
                page_data = analyzed if (isinstance(analyzed, dict) and analyzed.get("is_valid", True)) else {}
            except Exception as analyze_err:
                self.logger.warning(f"页面分析失败，使用空page_data: {analyze_err}")
                page_data = {}
            
            # 第一次构建（将自然语言文本转换为可执行的JSON指令，可能为前置导航）
            try:
                json_instruction = self.instruction_builder.build(
                    text,
                    page_data,
                    session_state
                )
            except Exception as build_err:
                self.logger.error(f"构建指令失败: {build_err}")
                json_instruction = {"action": "error", "error": str(build_err)}
            
            messages: List[str] = []
            screenshots: List[str] = []

            # 执行第一阶段
            result = self.action_executor.execute(
                json_instruction,
                session_state,
                timeout=get_config("MAX_EXECUTION_TIME", 60)
            )
            messages.append(result.get("message", ""))
            if result.get("screenshot"):
                screenshots.append(result["screenshot"])

            # 如果第一阶段仅为导航/等待且成功，则进行第二阶段：重新感知并生成精细操作
            if result.get("success") and self._is_navigation_only(json_instruction):
                try:
                    updated = self.page_analyzer.analyze()
                    updated_page_data = updated if (isinstance(updated, dict) and updated.get("is_valid", True)) else {}
                except Exception:
                    updated_page_data = {}

                # 第二次构建（应避免再次navigate）
                try:
                    json_instruction_2 = self.instruction_builder.build(
                        text,
                        updated_page_data,
                        session_state
                    )
                except Exception as build_err_2:
                    self.logger.error(f"二阶段构建指令失败: {build_err_2}")
                    json_instruction_2 = {"action": "error", "error": str(build_err_2)}

                # 若二阶段仍是纯导航，跳过避免循环
                if not self._is_navigation_only(json_instruction_2):
                    result2 = self.action_executor.execute(
                        json_instruction_2,
                        session_state,
                        timeout=get_config("MAX_EXECUTION_TIME", 60)
                    )
                    messages.append(result2.get("message", ""))
                    if result2.get("screenshot"):
                        screenshots.append(result2["screenshot"])
                    # 合并结果
                    result = {
                        **result2,
                        "success": result.get("success", False) and result2.get("success", False),
                        "message": "; ".join(m for m in messages if m),
                    }
                else:
                    # 若仍为导航，直接返回第一阶段结果
                    result = {
                        **result,
                        "message": "; ".join(m for m in messages if m)
                    }
            
            # 截图（可选）
            screenshot = None
            try:
                if result.get("success", False) and result.get("take_screenshot", False):
                    screenshot_bytes = self.page.screenshot()
                    screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
            except Exception:
                screenshot = None
            # 若前面已有截图，优先返回最后一次
            if not screenshot and screenshots:
                screenshot = screenshots[-1]
            
            # 执行后重新感知（容错）
            try:
                updated = self.page_analyzer.analyze()
                updated_page_data = updated if (isinstance(updated, dict) and updated.get("is_valid", True)) else {}
            except Exception:
                updated_page_data = {}

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
        try:
            analyzed = self.page_analyzer.analyze()
            return analyzed if (isinstance(analyzed, dict) and analyzed.get("is_valid", True)) else {}
        except Exception:
            return {}

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