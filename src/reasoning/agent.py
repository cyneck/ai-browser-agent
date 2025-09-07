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

from src.models.response import GeneratedResponse, ResponseContext
from src.models.instruction import Instruction, SingleStepInstruction, MultiStepInstruction, InstructionContext
from src.common.config import get_config, get_human_behavior_config
from src.common.logger import get_logger
from src.perception.page_analyzer import PageAnalyzer
from src.reasoning.instruction_builder import InstructionBuilder
from src.reasoning.intent_classifier import IntentClassifier
from src.reasoning.response_generator import ResponseGenerator
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
            
            self.logger.info(f"启动{browser_type}浏览器，headless={headless}，user_data_dir={user_data_dir}")
            self.playwright = sync_playwright().start()
            browser_instance = getattr(self.playwright, browser_type)
            
            # 使用launch_persistent_context替代launch和new_context
            self.context = browser_instance.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                user_agent="AI Browser Agent/1.0"
            )
            # 在持久化上下文中，不需要单独的browser对象
            self.browser = None
            # 确保context不为None再调用new_page方法
            if self.context is not None:
                self.page = self.context.new_page()
            else:
                raise RuntimeError("Failed to create browser context")
            
            self.page_analyzer = PageAnalyzer(self.page)
            self.instruction_builder = InstructionBuilder()
            self.intent_classifier = IntentClassifier()
            self.response_generator = ResponseGenerator()
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
            
            # 1. 分析用户意图
            intent_result = self.intent_classifier.classify_intent(text)
            self.logger.info(f"识别用户意图: {intent_result.intent_type.value}, 置信度: {intent_result.confidence}")
            
            # 2. 获取页面数据
            page_data = {}
            try:
                if self.page_analyzer is not None:
                    analyzed = self.page_analyzer.analyze()
                    page_data = analyzed if isinstance(analyzed, dict) and analyzed.get("is_valid", True) else {}
                else:
                    self.logger.warning("PageAnalyzer未初始化")
            except Exception as analyze_err:
                self.logger.warning(f"页面分析失败: {analyze_err}")

            # 3. 构建指令（考虑用户意图）
            try:
                if self.instruction_builder is not None:
                    json_instruction = self.instruction_builder.build_optimized(text, page_data, session_state)
                    
                    # 根据用户意图调整指令
                    json_instruction = self._enhance_instruction_with_intent(json_instruction, intent_result)
                else:
                    raise RuntimeError("InstructionBuilder未初始化")
            except Exception as build_err:
                self.logger.error(f"构建指令失败: {build_err}")
                json_instruction = {"action": "error", "error": str(build_err)}
            
            # 4. 执行指令
            if self.action_executor is not None:
                result = self.action_executor.execute(
                    json_instruction,
                    session_state,
                    timeout=get_config("MAX_EXECUTION_TIME", 120)
                )
            else:
                raise RuntimeError("ActionExecutor未初始化")
            
            # 5. 处理执行结果并生成最终响应
            final_response = self._process_execution_result(
                result, intent_result, text, session_state
            )
            
            # 6. 处理截图
            screenshot = final_response.get("screenshot")
            if not screenshot and final_response.get("success", False) and final_response.get("take_screenshot", False):
                try:
                    if self.page is not None:
                        screenshot_bytes = self.page.screenshot()
                        screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
                    else:
                        self.logger.warning("Page对象未初始化，无法截图")
                        screenshot = None
                except Exception:
                    screenshot = None
            
            # 7. 更新页面数据
            try:
                if self.page_analyzer is not None:
                    updated_page_data = self.page_analyzer.analyze()
                else:
                    self.logger.warning("PageAnalyzer未初始化，无法更新页面数据")
                    updated_page_data = {}
            except Exception:
                updated_page_data = {}

            self.logger.info(f"执行完成，成功: {final_response.get('success', False)}")
            return {
                "success": final_response.get("success", False),
                "message": final_response.get("message", "执行完成"),
                "error": final_response.get("error"),
                "screenshot": screenshot,
                "session_state": session_state,
                "page_data": updated_page_data,
                "content": final_response.get("content"),  # 添加内容字段
                "response_format": final_response.get("response_format", "natural_language"),  # 添加格式字段
                "intent_info": {  # 添加意图信息
                    "intent_type": intent_result.intent_type.value,
                    "confidence": intent_result.confidence,
                    "response_format": intent_result.response_format
                }
            }
        except Exception as e:
            self.logger.error(f"执行指令时发生错误: {e}", exc_info=True)
            return {"success": False, "message": "执行失败", "error": str(e), "session_state": session_state}
    
    def _enhance_instruction_with_intent(self, instruction: Dict[str, Any], 
                                       intent_result) -> Dict[str, Any]:
        """根据用户意图增强指令"""
        from src.reasoning.intent_classifier import IntentType
        
        # 如果是多步骤指令，检查是否需要添加特定的提取步骤
        if "steps" in instruction:
            steps = instruction["steps"]
            
            # 如果是信息获取类意图，确保有提取步骤
            if intent_result.intent_type in [IntentType.SUMMARY_INFO, IntentType.DETAILED_INFO, IntentType.STRUCTURED_DATA]:
                # 棻查是否已经有提取动作
                has_extract = any(step.get("action") in ["extract_results", "extract"] for step in steps)
                
                if not has_extract:
                    # 添加适当的提取动作
                    extract_step = self._create_extract_step_for_intent(intent_result)
                    steps.append(extract_step)
            
            # 如果是全页面内容意图，但指令中没有保存操作，则添加全页面内容提取
            elif intent_result.intent_type == IntentType.FULL_PAGE_CONTENT:
                # 检查是否已经有保存网页的操作
                has_save_action = any(step.get("action") in ["save_as_mhtml", "save_as_pdf"] for step in steps)
                
                # 只有在没有保存操作时才添加提取步骤
                if not has_save_action:
                    steps.append({
                        "action": "extract_results",
                        "extraction_type": "full_content",
                        "description": "提取完整页面内容"
                    })
        
        else:
            # 单步骤指令，根据意图调整
            if (intent_result.intent_type == IntentType.FULL_PAGE_CONTENT and 
                instruction.get("action") not in ["save_as_mhtml", "save_as_pdf"] and
                instruction.get("action") != "extract_results"):
                # 转换为全页面内容提取
                instruction = {
                    "action": "extract_results",
                    "extraction_type": "full_content",
                    "description": "提取完整页面内容"
                }
        
        return instruction
    
    def _create_extract_step_for_intent(self, intent_result) -> Dict[str, Any]:
        """根据意图创建适当的提取步骤"""
        from src.reasoning.intent_classifier import IntentType
        
        if intent_result.intent_type == IntentType.STRUCTURED_DATA:
            return {
                "action": "extract_results",
                "extraction_type": "structured",
                "description": "提取结构化数据"
            }
        elif intent_result.intent_type == IntentType.DETAILED_INFO:
            return {
                "action": "extract_results",
                "extraction_type": "auto",
                "description": "提取详细信息"
            }
        else:  # SUMMARY_INFO or default
            return {
                "action": "extract_results",
                "extraction_type": "auto",
                "description": "提取相关信息"
            }
    
    def _process_execution_result(self, result: Dict[str, Any], intent_result, 
                                 original_text: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行结果并生成最终响应"""
        # 如果执行失败，直接返回
        if not result.get("success", False):
            return result
        
        # 获取提取的内容
        extracted_content = result.get("content")
        
        # 如果没有提取到内容，检查步骤结果
        if not extracted_content and "step_results" in result:
            for step_result in result["step_results"]:
                if step_result.get("content"):
                    extracted_content = step_result["content"]
                    break
        
        # 如果仍然没有内容，返回原始结果
        if not extracted_content:
            return result
        
        # 使用响应生成器生成最终响应
        try:
            # 创建响应上下文
            response_context = {
                "original_query": original_text,
                "original_text": original_text,
                "page_url": getattr(self.page, 'url', ''),
                "session_state": session_state
            }
            
            generated_response = self.response_generator.generate_response(
                extracted_content, intent_result, response_context
            )
            
            if generated_response.success:
                # 更新结果
                result["message"] = generated_response.content
                result["content"] = extracted_content  # 保留原始内容
                result["response_format"] = generated_response.format.value
                result["metadata"] = generated_response.metadata
            else:
                # 生成失败，使用默认处理
                result["message"] = generated_response.content or result.get("message", "执行完成")
                result["content"] = extracted_content
            
        except Exception as e:
            self.logger.error(f"生成响应时出错: {e}")
            # 发生错误时，保持原始结果
            result["content"] = extracted_content
        
        return result

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
        # 在持久化上下文模式中，只需要关闭context，不需要单独关闭browser
        resources = [self.page, self.context]
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
            if self.page_analyzer is not None:
                return self.page_analyzer.analyze()
            else:
                return {"success": False, "error": "PageAnalyzer未初始化"}
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
            if self.page is not None:
                return self.page.screenshot()
            else:
                self.logger.warning("Page对象未初始化，无法截图")
                return None
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