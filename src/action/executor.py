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
from src.common.performance_monitor import get_performance_monitor
from src.action.state_manager import StateManager
from src.action.error_handler import ErrorHandler
from src.action.safety_validator import SafetyValidator
from src.action.human_behavior_simulator import HumanBehaviorSimulator


class ActionExecutor:
    """动作执行器类，负责安全地执行指令"""

    def __init__(self, page: Page, state_manager: Optional[StateManager] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 behavior_config: Optional[Dict[str, Any]] = None):
        """初始化动作执行器

        Args:
            page: Playwright页面对象
            state_manager: 状态管理器
            error_handler: 错误处理器
            behavior_config: 人类行为模拟配置
        """
        self.logger = get_logger()
        self.page = page
        self.state_manager = state_manager or StateManager()
        self.error_handler = error_handler or ErrorHandler()
        self.perf_monitor = get_performance_monitor()
        self.behavior_simulator = HumanBehaviorSimulator(behavior_config)

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

        # 人类行为模拟：操作前等待
        self.behavior_simulator.wait_before_action(action)

        start_time = time.time()
        page_load_start = time.time()
        
        try:
            # 记录页面加载时间（如果适用）
            if action == "navigate":
                page_load_start = time.time()
            
            result = handler(step)
            execution_time = time.time() - start_time
            page_load_time = time.time() - page_load_start if action == "navigate" else 0
            
            # 记录浏览器操作性能
            screenshot_size = None
            if action == "screenshot" and result.get("data"):
                import base64
                try:
                    screenshot_data = result["data"]
                    if isinstance(screenshot_data, str):
                        screenshot_size = len(screenshot_data.encode('utf-8'))
                except:
                    pass
            
            self.perf_monitor.record_browser_action(
                action_type=action,
                selector=step.get("selector"),
                execution_time=execution_time,
                page_load_time=page_load_time,
                success=result.get("success", True),
                error_message=result.get("error"),
                screenshot_size=screenshot_size
            )
            
            if result.get("success"):
                self.state_manager.set_state("last_action", action)
                self.state_manager.set_state("last_message", result.get("message"))
                
            # 记录操作历史到行为模拟器
            self.behavior_simulator.record_action(
                action, 
                result.get("success", False), 
                execution_time
            )
            return result
            
        except PlaywrightError as e:
            execution_time = time.time() - start_time
            self.perf_monitor.record_browser_action(
                action_type=action,
                selector=step.get("selector"),
                execution_time=execution_time,
                page_load_time=0,
                success=False,
                error_message=str(e)
            )
            # 记录失败的操作
            self.behavior_simulator.record_action(
                action, 
                False, 
                execution_time
            )
            return self.error_handler.handle_error(e, step, {})
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.perf_monitor.record_browser_action(
                action_type=action,
                selector=step.get("selector"),
                execution_time=execution_time,
                page_load_time=0,
                success=False,
                error_message=str(e)
            )
            # 记录失败的操作
            self.behavior_simulator.record_action(
                action, 
                False, 
                execution_time
            )
            return self.error_handler.handle_error(e, step, {})

    # --- Action Handler Methods ---

    def _execute_navigate(self, step: Dict[str, Any]) -> Dict[str, Any]:
        url = step.get("value")
        if not url:
            return {"success": False, "message": "导航失败：URL为空"}
        self.page.goto(url, wait_until="domcontentloaded")
        
        # 页面加载后等待
        wait_time = self.behavior_simulator.get_page_load_wait_time()
        if wait_time > 0:
            self.logger.debug(f"页面加载后等待: {wait_time:.2f}秒")
            time.sleep(wait_time)
            
        return {"success": True, "message": f"成功导航到 {url}"}

    def _execute_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        selector = step.get("selector")
        if not selector:
            return {"success": False, "message": "点击失败：选择器为空"}
            
        # 模拟鼠标移动（如果启用）
        try:
            element = self.page.locator(selector)
            if self.behavior_simulator.is_enabled():
                # 获取元素位置
                bbox = element.bounding_box()
                if bbox:
                    # 从当前鼠标位置移动到目标元素
                    target_x = bbox["x"] + bbox["width"] // 2
                    target_y = bbox["y"] + bbox["height"] // 2
                    
                    # 获取当前鼠标位置（如果可能）
                    try:
                        # 使用页面中心作为起始位置
                        viewport = self.page.viewport_size()
                        start_x = viewport["width"] // 2
                        start_y = viewport["height"] // 2
                        
                        self.behavior_simulator.simulate_mouse_movement(
                            self.page, (start_x, start_y), (target_x, target_y)
                        )
                    except Exception as e:
                        self.logger.debug(f"鼠标移动模拟失败: {e}")
                        
            element.click()
        except Exception:
            # 如果元素位置获取失败，直接点击
            self.page.locator(selector).click()
            
        return {"success": True, "message": f"成功点击元素 {selector}"}

    def _execute_fill(self, step: Dict[str, Any]) -> Dict[str, Any]:
        selector = step.get("selector")
        value = step.get("value", "")
        if not selector:
            return {"success": False, "message": "输入失败：选择器为空"}
            
        # 使用人类打字模拟
        if self.behavior_simulator.is_enabled() and value:
            self.behavior_simulator.simulate_human_typing(self.page, selector, value)
        else:
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
            # 滚动后等待
            scroll_delay = self.behavior_simulator.get_base_delay() * 0.5
            if scroll_delay > 0:
                time.sleep(scroll_delay)
            return {"success": True, "message": f"成功滚动到元素 {step['selector']}"}
        elif "value" in step:
            self.page.evaluate(f"window.scrollBy(0, {step['value']})")
            # 滚动后等待
            scroll_delay = self.behavior_simulator.get_base_delay() * 0.3
            if scroll_delay > 0:
                time.sleep(scroll_delay)
            return {"success": True, "message": f"成功滚动页面 {step['value']} 像素"}
        else:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # 滚动后等待
            scroll_delay = self.behavior_simulator.get_base_delay() * 0.5
            if scroll_delay > 0:
                time.sleep(scroll_delay)
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
        
    def get_behavior_stats(self) -> Dict[str, Any]:
        """获取人类行为模拟统计信息"""
        return self.behavior_simulator.get_stats()
        
    def configure_behavior(self, config: Dict[str, Any]) -> None:
        """配置人类行为模拟参数"""
        # 更新用户配置
        self.behavior_simulator.config.update(config)
        # 重新合并配置并应用模式
        self.behavior_simulator.effective_config = {
            **self.behavior_simulator.default_config, 
            **self.behavior_simulator.config
        }
        self.behavior_simulator._apply_behavior_mode()
