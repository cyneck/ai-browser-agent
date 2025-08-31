#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动作执行器

负责安全地执行标准化的JSON格式指令，与浏览器交互。
"""

import json
import time
import base64
from typing import Dict, Any, List, Optional, Callable

from playwright.sync_api import Page, Error as PlaywrightError

from src.common.logger import get_logger
from src.action.state_manager import StateManager
from src.action.error_handler import ErrorHandler
from src.action.safety_validator import SafetyValidator


class ActionExecutor:
    """动作执行器类，负责安全地执行指令"""

    def __init__(self, page: Page, state_manager: Optional[StateManager] = None,
                 error_handler: Optional[ErrorHandler] = None):
        """初始化动作执行器

        Args:
            page: Playwright页面对象
            state_manager: 状态管理器
            error_handler: 错误处理器
        """
        self.logger = get_logger()
        self.page = page
        self.state_manager = state_manager or StateManager()
        self.error_handler = error_handler or ErrorHandler()

        # 将 action 名称映射到对应的处理方法
        self.action_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "navigate": self._execute_navigate,
            "click": self._execute_click,
            "fill": self._execute_fill,
            "type": self._execute_fill,  # 'type' is an alias for 'fill'
            "select": self._execute_select,
            "wait": self._execute_wait,
            "screenshot": self._execute_screenshot,
            "extract": self._execute_extract,
            "scroll": self._execute_scroll,
            "back": self._execute_back,
            "forward": self._execute_forward,
            "refresh": self._execute_refresh,
            "close": self._execute_close,
            "error": self._execute_error,
            "wait_for_login": self._execute_wait_for_login,
        }
        
        self.safety_validator = SafetyValidator(self.get_supported_actions())

    def _execute_wait_for_login(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """暂停执行，等待用户手动登录"""
        print("\n" + "="*50)
        print("⏸️  检测到需要手动登录。")
        print("请在浏览器中完成扫码登录或其他登录操作。")
        input("完成后，请按 Enter 键继续执行...")
        print("▶️  继续执行...")
        print("="*50 + "\n")
        return {"success": True, "message": "用户已确认登录，继续执行"}

    def get_supported_actions(self) -> List[str]:
        """获取当前支持的所有操作列表"""
        return list(self.action_handlers.keys())

    def execute(self, instruction: Dict[str, Any], session_state: Dict[str, Any],
                timeout: int = 60) -> Dict[str, Any]:
        """
        执行指令（统一的多步执行方式）

        Args:
            instruction: 标准化的JSON格式指令
            session_state: 会话状态
            timeout: 执行超时时间（秒）

        Returns:
            执行结果
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"执行指令: {json.dumps(instruction, ensure_ascii=False, indent=2)}")
            self.logger.info("=" * 60)

            # 安全校验与转义
            instruction = self.safety_validator.validate_and_sanitize(instruction)

            # 标准化为多步格式
            if "steps" not in instruction:
                instruction = self._normalize_to_multi_step(instruction)

            return self._execute_steps(instruction, timeout)
        except Exception as e:
            return self.error_handler.handle_error(e, instruction, {"session_state": session_state})

    def _normalize_to_multi_step(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """将单步指令标准化为多步格式"""
        return {
            "steps": [instruction],
            "description": instruction.get("description", f"执行 {instruction.get('action', '未知')} 操作")
        }

    def _execute_steps(self, instruction: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """统一的步骤执行方法"""
        steps = instruction.get("steps", [])
        description = instruction.get("description", "执行复合操作")
        self.logger.info(f"开始执行操作: {description}")

        step_results = []
        overall_success = True
        error_message = ""
        start_time = time.time()

        for i, step in enumerate(steps):
            if time.time() - start_time > timeout:
                error_message = f"执行超时（超过 {timeout} 秒）"
                overall_success = False
                break

            step_result = self._execute_step(step)
            step_results.append(step_result)

            if not step_result.get("success", False):
                error_message = f"第 {i + 1} 步操作失败: {step_result.get('message', '未知错误')}"
                overall_success = False
                break
        
        final_message = description if overall_success else error_message
        
        result = {
            "success": overall_success,
            "message": final_message,
            "step_results": step_results
        }

        # For single-step operations, merge the step result into the main result
        if len(steps) == 1 and step_results:
            single_result = step_results[0]
            result.update(single_result)
            # Overwrite the generic message with the specific one from the step
            result["message"] = single_result.get("message", final_message)

        if not overall_success:
            # This is the high-level error, but the specific error from the step
            # is preserved via the update() above.
            result["error"] = error_message

        return result

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        action = step.get("action")
        description = step.get("description", f"执行 {action} 操作")
        self.logger.info(f"执行步骤: {action} - {description}")

        handler = self.action_handlers.get(action)
        if not handler:
            return {
                "success": False,
                "message": f"不支持的操作类型: {action}",
                "error": f"未找到操作 '{action}' 的处理器。"
            }

        try:
            result = handler(step)
            if result.get("success"):
                self.state_manager.set_state("last_action", action)
                self.state_manager.set_state("last_message", result.get("message"))
            return result
        except PlaywrightError as e:
            return self.error_handler.handle_error(e, step, {})
        except Exception as e:
            return self.error_handler.handle_error(e, step, {})

    # --- Action Handler Methods ---

    def _execute_navigate(self, step: Dict[str, Any]) -> Dict[str, Any]:
        url = step.get("value")
        if not url:
            return {"success": False, "message": "导航失败：URL为空"}
        self.page.goto(url, wait_until="domcontentloaded")
        return {"success": True, "message": f"成功导航到 {url}"}

    def _execute_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        selector = step.get("selector")
        if not selector:
            return {"success": False, "message": "点击失败：选择器为空"}
        self.page.locator(selector).click()
        return {"success": True, "message": f"成功点击元素 {selector}"}

    def _execute_fill(self, step: Dict[str, Any]) -> Dict[str, Any]:
        selector = step.get("selector")
        value = step.get("value", "")
        if not selector:
            return {"success": False, "message": "输入失败：选择器为空"}
        self.page.locator(selector).fill(value)
        return {"success": True, "message": f"成功在 {selector} 中输入文本"}

    def _execute_select(self, step: Dict[str, Any]) -> Dict[str, Any]:
        selector = step.get("selector")
        value = step.get("value")
        if not selector or not value:
            return {"success": False, "message": "选择失败：选择器或值为空"}
        self.page.locator(selector).select_option(value=value)
        return {"success": True, "message": f"成功在 {selector} 中选择 {value}"}

    def _execute_wait(self, step: Dict[str, Any]) -> Dict[str, Any]:
        if "selector" in step:
            timeout = step.get("timeout", 30000)
            self.page.wait_for_selector(step["selector"], timeout=timeout)
            return {"success": True, "message": f"成功等待元素 {step['selector']} 出现"}
        elif "value" in step:
            timeout_ms = int(step["value"])
            self.page.wait_for_timeout(timeout_ms)
            return {"success": True, "message": f"成功等待 {timeout_ms} 毫秒"}
        else:
            self.page.wait_for_load_state("domcontentloaded")
            return {"success": True, "message": "成功等待页面加载"}

    def _execute_screenshot(self, step: Dict[str, Any]) -> Dict[str, Any]:
        screenshot_bytes = self.page.screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        return {
            "success": True,
            "message": "成功截取屏幕截图",
            "screenshot": screenshot_base64
        }

    def _execute_extract(self, step: Dict[str, Any]) -> Dict[str, Any]:
        if "selector" in step:
            content = self.page.locator(step["selector"]).inner_text()
            return {"success": True, "message": "成功提取内容", "content": content}
        else:
            content = self.page.content()
            return {"success": True, "message": "成功提取页面内容", "content": content}

    def _execute_scroll(self, step: Dict[str, Any]) -> Dict[str, Any]:
        if "selector" in step:
            self.page.locator(step["selector"]).scroll_into_view_if_needed()
            return {"success": True, "message": f"成功滚动到元素 {step['selector']}"}
        elif "value" in step:
            self.page.evaluate(f"window.scrollBy(0, {step['value']})")
            return {"success": True, "message": f"成功滚动页面 {step['value']} 像素"}
        else:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return {"success": True, "message": "成功滚动到页面底部"}

    def _execute_back(self, step: Dict[str, Any]) -> Dict[str, Any]:
        self.page.go_back()
        return {"success": True, "message": "成功返回上一页"}

    def _execute_forward(self, step: Dict[str, Any]) -> Dict[str, Any]:
        self.page.go_forward()
        return {"success": True, "message": "成功前进到下一页"}

    def _execute_refresh(self, step: Dict[str, Any]) -> Dict[str, Any]:
        self.page.reload()
        return {"success": True, "message": "成功刷新页面"}

    def _execute_close(self, step: Dict[str, Any]) -> Dict[str, Any]:
        self.page.close()
        return {"success": True, "message": "成功关闭页面"}

    def _execute_error(self, step: Dict[str, Any]) -> Dict[str, Any]:
        error_message = step.get("error", "未知错误")
        return {"success": False, "message": "执行错误指令", "error": error_message}
