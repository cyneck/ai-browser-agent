#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动作执行器

负责安全地执行标准化的JSON格式指令，与浏览器交互。
"""
import json
import time
import base64
import re
import os
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from playwright.sync_api import Page, Error as PlaywrightError

from src.models.instruction import (
    ActionType, BaseAction, NavigateAction, ClickAction, 
    FillAction, WaitAction, ExtractAction
)
from src.common.logger import get_logger
from src.common.performance_monitor import get_performance_monitor
from src.action.state_manager import StateManager
from src.action.error_handler import ErrorHandler
from src.action.error_integration import get_integrated_error_handler
from src.action.safety_validator import SafetyValidator
from src.action.human_behavior_simulator import HumanBehaviorSimulator
from src.common.config import get_config


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
        self.integrated_error_handler = get_integrated_error_handler()
        self.perf_monitor = get_performance_monitor()
        self.behavior_simulator = HumanBehaviorSimulator(behavior_config)
        self.debug_mode = get_config("DEBUG_MODE", False)

        # 将 action 名称映射到对应的处理方法
        self.action_handlers: Dict[ActionType, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            ActionType.NAVIGATE: self._execute_navigate,
            ActionType.CLICK: self._execute_click,
            ActionType.FILL: self._execute_fill,
            ActionType.TYPE: self._execute_fill,  # 'type' is an alias for 'fill'
            ActionType.KEY: self._execute_key,  # Add keyboard action support
            ActionType.SELECT: self._execute_select,
            ActionType.WAIT: self._execute_wait,
            ActionType.SCREENSHOT: self._execute_screenshot,
            ActionType.EXTRACT: self._execute_extract,
            ActionType.EXTRACT_RESULTS: self._execute_extract_results,
            ActionType.SCROLL: self._execute_scroll,
            ActionType.BACK: self._execute_back,
            ActionType.FORWARD: self._execute_forward,
            ActionType.REFRESH: self._execute_refresh,
            ActionType.CLOSE: self._execute_close,
            ActionType.ERROR: self._execute_error,
            ActionType.WAIT_FOR_LOGIN: self._execute_wait_for_login,
            ActionType.SMART_FILL: self._execute_smart_fill,
            ActionType.SMART_SUBMIT: self._execute_smart_submit,
            ActionType.SAVE_AS_PDF: self._execute_save_as_pdf,
            ActionType.SAVE_AS_MHTML: self._execute_save_as_mhtml,
            # New enhanced action handlers
            ActionType.DRAG_AND_DROP: self._execute_drag_and_drop,
            ActionType.RIGHT_CLICK: self._execute_right_click,
            ActionType.DOUBLE_CLICK: self._execute_double_click,
            ActionType.HOVER: self._execute_hover,
            ActionType.UPLOAD_FILE: self._execute_upload_file,
            ActionType.DOWNLOAD_FILE: self._execute_download_file,
            ActionType.SWITCH_TAB: self._execute_switch_tab,
            ActionType.NEW_TAB: self._execute_new_tab,
            ActionType.CLOSE_TAB: self._execute_close_tab,
            ActionType.ZOOM: self._execute_zoom,
            ActionType.FULLSCREEN: self._execute_fullscreen,
            ActionType.SMART_WAIT: self._execute_smart_wait,
        }
        
        self.safety_validator = SafetyValidator([action.value for action in ActionType])

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
        return [action.value for action in ActionType]

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
            
            # 应用反检测措施
            self.behavior_simulator.apply_anti_detection_measures(self.page)

            # 优化：对于直接明确的指令，跳过LLM调用
            action_str = instruction.get("action")
            if action_str:
                try:
                    action = ActionType(action_str)
                    if action in self.action_handlers:
                        self.logger.info(f"检测到直接指令 '{action.value}'，跳过LLM推理。")
                        # 如果是直接指令，确保其有 description，然后标准化为多步格式后执行
                        normalized_instruction = self._normalize_to_multi_step(instruction)
                        if "description" not in normalized_instruction:
                            normalized_instruction["description"] = f"执行 {action.value} 操作"
                        return self._execute_steps(normalized_instruction, timeout)
                except ValueError:
                    # 如果action_str不是有效的ActionType，继续下面的处理
                    pass
            
            # 尝试通过简单的启发式规则识别指令
            user_text = instruction.get("user_text")
            if user_text:
                heuristic_instruction = self._try_simple_heuristics(user_text, instruction, self.page)
                if heuristic_instruction and heuristic_instruction.get("action") in [action.value for action in ActionType]: # 确保识别到的指令是支持的指令
                    self.logger.info(f"通过启发式规则识别到指令: {heuristic_instruction.get('action')}")
                    # 如果启发式规则成功识别，将其标准化为多步格式后执行
                    # 对于导航指令，将原始的 user_text 作为 description 传递
                    if heuristic_instruction.get("action") == "navigate":
                        heuristic_instruction["description"] = user_text
                    return self._execute_steps(self._normalize_to_multi_step(heuristic_instruction), timeout)

            # 安全校验与转义
            instruction = self.safety_validator.validate_and_sanitize(instruction)

            # 标准化为多步格式
            if "steps" not in instruction:
                instruction = self._normalize_to_multi_step(instruction)

            return self._execute_steps(instruction, timeout)
        except Exception as e:
            # 使用集成错误处理器，支持自动恢复
            return self.integrated_error_handler.handle_error_with_recovery(
                e, instruction, 
                {"session_state": session_state, "page_url": self.page.url},
                executor_callback=lambda recovery_instruction: self.execute(recovery_instruction, session_state),
                auto_recovery=True
            )

    def _normalize_to_multi_step(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """将单步指令标准化为多步格式"""
        # 确保 description 总是存在
        action_type = instruction.get('action', '未知')
        description = instruction.get("description", f"执行 {action_type} 操作")
        result = {
            "steps": [instruction],
            "description": description,
            "success": instruction.get("success", True) # 默认成功，除非instruction明确指定失败
        }
        return result

    def _try_simple_heuristics(self, user_text: str, instruction: Dict[str, Any], page: Page | None = None) -> Optional[Dict[str, Any]]:
        """尝试通过简单的启发式规则从user_text中识别指令"""
        if not user_text:
            return None

        intent = self._extract_intent_from_user_text(user_text, page)
        if not intent:
            return None
        
        result = self._handle_instruction_with_intent(intent)
        return result

    def _extract_intent_from_user_text(self, user_text: str, page: Page | None = None) -> dict | None:
        """
        从用户文本中提取指令意图。
        """
        self.logger.debug(f"尝试从用户文本中提取意图: {user_text}")
        # TODO: 实现更复杂的意图提取逻辑
        if "前往" in user_text or "导航到" in user_text:
            url_pattern = re.compile(r"https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?://[a-zA-Z0-9]+\.[^\s]{2,}|[a-zA-Z0-9]+\.[^\s]{2,}")
            match = url_pattern.search(user_text)
            if match:
                url = match.group(0)
                self.logger.info(f"从用户文本中提取到URL: {url}")
                return {"action": "navigate", "args": {"url": url}}
        
        return None

    def _handle_instruction_with_intent(self, intent: dict) -> dict:
        """
        根据提取到的意图处理指令，生成符合多步格式的指令。
        """
        # TODO: 实现更完整的指令处理逻辑
        action = intent.get("action")
        args = intent.get("args", {})
        description = f"执行 {action} 操作" # Fallback description

        if action == "navigate":
            url = args.get('url')
            description = f"导航到 {url}"
            return {"action": action, "args": args, "description": description, "success": True}
        
        return {"action": action, "args": args, "description": description, "success": False}


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

            # 如果启用了调试模式，保存截图和MHTML
            if self.debug_mode:
                self._save_debug_info(step, step_result, i+1)

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

    def _save_debug_info(self, step: Dict[str, Any], step_result: Dict[str, Any], step_index: int):
        """保存调试信息，包括截图和MHTML页面信息"""
        try:
            # 创建调试目录
            debug_dir = "./debug"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存截图
            try:
                screenshot_bytes = self.page.screenshot()
                screenshot_filename = f"screenshot_step{step_index}_{timestamp}.jpeg"
                screenshot_path = os.path.join(debug_dir, screenshot_filename)
                
                # 保存为JPEG格式
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(screenshot_bytes))
                image = image.convert("RGB")  # 转换为RGB模式以支持JPEG
                image.save(screenshot_path, "JPEG")
                
                self.logger.info(f"调试截图已保存: {screenshot_path}")
            except ImportError as e:
                self.logger.error(f"保存调试截图失败，缺少PIL库: {e}")
            except Exception as e:
                self.logger.error(f"保存调试截图失败: {e}")
            
            # 保存MHTML页面信息
            try:
                mhtml_filename = f"page_step{step_index}_{timestamp}.mhtml"
                mhtml_path = os.path.join(debug_dir, mhtml_filename)
                
                content = self.page.content()
                with open(mhtml_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"调试MHTML已保存: {mhtml_path}")
            except Exception as e:
                self.logger.error(f"保存调试MHTML失败: {e}")
                
        except Exception as e:
            self.logger.error(f"保存调试信息失败: {e}")

    def _execute_save_as_mhtml(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """将当前页面保存为MHTML"""
        import os
        from datetime import datetime
        
        # 使用固定下载路径配置
        download_dir = "./downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"page_{timestamp}.mhtml"
        path = os.path.join(download_dir, filename)
        
        try:
            content = self.page.content()
            # MHTML is not directly supported, so we save the HTML content.
            # For a true MHTML, a third-party library would be needed.
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 构建下载URL
            file_name = os.path.basename(path)
            download_url = f"/download/{file_name}"
            
            self.logger.info(f"页面已成功保存为MHTML: {path}")
            return {
                "success": True, 
                "message": f"页面已成功保存为MHTML: {path}", 
                "download_url": download_url,
                "path": path
            }
        except Exception as e:
            error_message = f"保存MHTML失败: {e}"
            self.logger.error(error_message)
            return self.integrated_error_handler.handle_error_with_recovery(
                e, step, {"path": path, "page_url": self.page.url}, auto_recovery=False
            )

    def _execute_save_as_pdf(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """将当前页面保存为PDF"""
        import os
        from datetime import datetime
        
        # 使用固定下载路径配置
        download_dir = "./downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"page_{timestamp}.pdf"
        path = os.path.join(download_dir, filename)
        
        try:
            self.page.pdf(path=path)
            
            # 构建下载URL
            file_name = os.path.basename(path)
            download_url = f"/download/{file_name}"
            
            self.logger.info(f"页面已成功保存为PDF: {path}")
            return {
                "success": True, 
                "message": f"页面已成功保存为PDF: {path}",
                "download_url": download_url,
                "path": path
            }
        except PlaywrightError as e:
            error_message = f"保存PDF失败: {e}"
            self.logger.error(error_message)
            return self.integrated_error_handler.handle_error_with_recovery(
                e, step, {"path": path, "page_url": self.page.url}, auto_recovery=False
            )

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        action_str = step.get("action")
        description = step.get("description", f"执行 {action_str} 操作")
        self.logger.info(f"执行步骤: {action_str} - {description}")

        # 尝试将action_str转换为ActionType枚举
        try:
            action = ActionType(action_str)
        except ValueError:
            return {
                "success": False,
                "message": f"不支持的操作类型: {action_str}",
                "error": f"未找到操作 '{action_str}' 的处理器。"
            }

        handler = self.action_handlers.get(action)
        if not handler:
            return {
                "success": False,
                "message": f"不支持的操作类型: {action.value}",
                "error": f"未找到操作 '{action.value}' 的处理器。"
            }

        # 人类行为模拟：操作前等待
        self.behavior_simulator.wait_before_action(action.value)

        start_time = time.time()
        page_load_start = time.time()
        
        try:
            # 记录页面加载时间（如果适用）
            if action == ActionType.NAVIGATE:
                page_load_start = time.time()
            
            result = handler(step)
            execution_time = time.time() - start_time
            page_load_time = time.time() - page_load_start if action == ActionType.NAVIGATE else 0
            
            # 记录浏览器操作性能
            screenshot_size = None
            if action == ActionType.SCREENSHOT and result.get("data"):
                import base64
                try:
                    screenshot_data = result["data"]
                    if isinstance(screenshot_data, str):
                        screenshot_size = len(screenshot_data.encode('utf-8'))
                except:
                    pass
            
            self.perf_monitor.record_browser_action(
                action_type=action.value,
                selector=step.get("selector"),
                execution_time=execution_time,
                page_load_time=page_load_time,
                success=result.get("success", True),
                error_message=result.get("error"),
                screenshot_size=screenshot_size
            )
            
            if result.get("success"):
                self.state_manager.set_state("last_action", action.value)
                self.state_manager.set_state("last_message", result.get("message"))
                
            # 记录操作历史到行为模拟器
            self.behavior_simulator.record_action(
                action.value, 
                result.get("success", False), 
                execution_time
            )
            return result
            
        except PlaywrightError as e:
            execution_time = time.time() - start_time
            self.perf_monitor.record_browser_action(
                action_type=action.value,
                selector=step.get("selector"),
                execution_time=execution_time,
                page_load_time=0,
                success=False,
                error_message=str(e)
            )
            # 记录失败的操作
            self.behavior_simulator.record_action(
                action.value, 
                False, 
                execution_time
            )
            return self.integrated_error_handler.handle_error_with_recovery(
                e, step, {"page_url": self.page.url}, auto_recovery=False
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.perf_monitor.record_browser_action(
                action_type=action.value,
                selector=step.get("selector"),
                execution_time=execution_time,
                page_load_time=0,
                success=False,
                error_message=str(e)
            )
            # 记录失败的操作
            self.behavior_simulator.record_action(
                action.value, 
                False, 
                execution_time
            )
            return self.integrated_error_handler.handle_error_with_recovery(
                e, step, {"page_url": self.page.url}, auto_recovery=False
            )

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
                    target_x = int(bbox["x"] + bbox["width"] // 2)  # 转换为整数
                    target_y = int(bbox["y"] + bbox["height"] // 2)  # 转换为整数
                    
                    # 获取当前鼠标位置（如果可能）
                    try:
                        # 使用页面中心作为起始位置
                        viewport = self.page.viewport_size  # 修复：viewport_size 是属性而不是方法
                        if viewport:  # 检查viewport是否为None
                            start_x = int(viewport["width"] // 2)  # 转换为整数
                            start_y = int(viewport["height"] // 2)  # 转换为整数
                            
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

    def _execute_key(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行键盘按键操作"""
        selector = step.get("selector")
        key = step.get("value") or step.get("key")
        
        if not key:
            return {"success": False, "message": "按键失败：按键值为空"}
            
        try:
            if selector:
                # 先聚焦到元素，然后按键
                self.page.locator(selector).focus()
                self.page.keyboard.press(key)
                return {"success": True, "message": f"成功在 {selector} 上按下 {key} 键"}
            else:
                # 直接按键
                self.page.keyboard.press(key)
                return {"success": True, "message": f"成功按下 {key} 键"}
        except Exception as e:
            return {"success": False, "message": f"按键失败: {str(e)}"}

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
            
    def _execute_extract_results(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """智能提取结果的动作，支持多种提取策略"""
        try:
            # 获取提取策略参数
            extraction_type = step.get("extraction_type", "auto")  # auto, search_results, full_content, structured
            target_selector = step.get("target_selector")  # 可选的特定选择器
            
            # 根据策略提取不同类型的内容
            if extraction_type == "full_content":
                extracted_content = self._extract_full_page_content()
            elif extraction_type == "structured":
                extracted_content = self._extract_structured_data(target_selector)
            elif extraction_type == "search_results" or self._is_search_results_page():
                extracted_content = self._extract_search_results()
            else:
                # Auto-detect appropriate extraction method
                extracted_content = self._auto_extract_content()
            
            if extracted_content:
                return {
                    "success": True, 
                    "message": f"成功提取内容",
                    "content": extracted_content,
                    "extraction_type": extraction_type,
                    "search_results": extracted_content if isinstance(extracted_content, list) else None  # 保持向后兼容
                }
            else:
                return {
                    "success": False, 
                    "message": "未找到可提取的内容",
                    "content": None
                }
        except Exception as e:
            return {
                "success": False, 
                "message": f"提取内容时出错: {str(e)}",
                "error": str(e)
            }

    def _execute_scroll(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行滚动操作，支持惯性模拟"""
        if "selector" in step:
            self.page.locator(step["selector"]).scroll_into_view_if_needed()
            # 滚动后等待
            scroll_delay = self.behavior_simulator.get_base_delay() * 0.5
            if scroll_delay > 0:
                time.sleep(scroll_delay)
            return {"success": True, "message": f"成功滚动到元素 {step['selector']}"}
        elif "value" in step:
            # 使用增强的惯性滚动
            scroll_value = step["value"]
            direction = "down" if scroll_value > 0 else "up"
            distance = abs(scroll_value)
            
            self.behavior_simulator.simulate_scroll_with_momentum(
                self.page, direction, distance
            )
            return {"success": True, "message": f"成功滚动页面 {step['value']} 像素"}
        else:
            # 滚动到底部，使用惯性模拟
            self.behavior_simulator.simulate_scroll_with_momentum(
                self.page, "down", 1000
            )
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
        # 在关闭页面前，尝试提取重要内容
        extracted_content = None
        try:
            # 如果页面上有搜索结果，先提取再关闭
            current_url = self.page.url
            if any(domain in current_url for domain in ["baidu.com", "bing.com", "google.com", "xiaohongshu.com"]):
                # 提取搜索结果
                search_results = self._extract_search_results()
                if search_results:
                    extracted_content = search_results
                    self.logger.info(f"在关闭页面前提取到搜索结果: {len(search_results)} 条")
        except Exception as e:
            self.logger.warning(f"提取页面内容时出错: {e}")
        
        # 关闭页面
        self.page.close()
        
        result = {"success": True, "message": "成功关闭页面"}
        if extracted_content:
            result["extracted_content"] = extracted_content
            result["message"] = f"成功关闭页面并提取了 {len(extracted_content)} 条结果"
        
        return result

    def _execute_error(self, step: Dict[str, Any]) -> Dict[str, Any]:
        error_message = step.get("error", "未知错误")
        return {"success": False, "message": "执行错误指令", "error": error_message}
        
    def _extract_search_results(self) -> List[Dict[str, Any]]:
        """提取当前页面的搜索结果"""
        results = []
        try:
            current_url = self.page.url
            
            # 根据不同的搜索引擎使用不同的选择器
            if "baidu.com" in current_url:
                # 百度搜索结果
                result_elements = self.page.locator(".result, .c-container").all()
                for i, element in enumerate(result_elements[:10]):  # 只取前10个结果
                    try:
                        title_elem = element.locator("h3 a, .t a").first
                        desc_elem = element.locator(".c-abstract, .c-span9").first
                        
                        title = title_elem.inner_text() if title_elem.count() > 0 else "无标题"
                        description = desc_elem.inner_text() if desc_elem.count() > 0 else "无描述"
                        href = title_elem.get_attribute("href") if title_elem.count() > 0 else ""
                        
                        results.append({
                            "title": title.strip(),
                            "description": description.strip()[:200],  # 限制描述长度
                            "url": href,
                            "index": i + 1
                        })
                    except Exception:
                        continue
                        
            elif "bing.com" in current_url:
                # 必应搜索结果
                result_elements = self.page.locator(".b_algo").all()
                for i, element in enumerate(result_elements[:10]):
                    try:
                        title_elem = element.locator("h2 a").first
                        desc_elem = element.locator(".b_caption p").first
                        
                        title = title_elem.inner_text() if title_elem.count() > 0 else "无标题"
                        description = desc_elem.inner_text() if desc_elem.count() > 0 else "无描述"
                        href = title_elem.get_attribute("href") if title_elem.count() > 0 else ""
                        
                        results.append({
                            "title": title.strip(),
                            "description": description.strip()[:200],
                            "url": href,
                            "index": i + 1
                        })
                    except Exception:
                        continue
                        
            elif "google.com" in current_url:
                # Google搜索结果
                result_elements = self.page.locator(".g").all()
                for i, element in enumerate(result_elements[:10]):
                    try:
                        title_elem = element.locator("h3").first
                        desc_elem = element.locator(".VwiC3b").first
                        link_elem = element.locator("a").first
                        
                        title = title_elem.inner_text() if title_elem.count() > 0 else "无标题"
                        description = desc_elem.inner_text() if desc_elem.count() > 0 else "无描述"
                        href = link_elem.get_attribute("href") if link_elem.count() > 0 else ""
                        
                        results.append({
                            "title": title.strip(),
                            "description": description.strip()[:200],
                            "url": href,
                            "index": i + 1
                        })
                    except Exception:
                        continue
                        
            elif "xiaohongshu.com" in current_url:
                # 小红书搜索结果
                result_elements = self.page.locator(".note-item, .feed-item").all()
                for i, element in enumerate(result_elements[:10]):
                    try:
                        title_elem = element.locator(".title, .note-title").first
                        desc_elem = element.locator(".desc, .note-text").first
                        
                        title = title_elem.inner_text() if title_elem.count() > 0 else "无标题"
                        description = desc_elem.inner_text() if desc_elem.count() > 0 else "无描述"
                        
                        results.append({
                            "title": title.strip(),
                            "description": description.strip()[:200],
                            "index": i + 1,
                            "platform": "小红书"
                        })
                    except Exception:
                        continue
            
            # 如果没有找到特定的搜索结果，尝试通用选择器
            if not results:
                generic_results = self.page.locator("a").all()
                for i, element in enumerate(generic_results[:5]):  # 只取前5个链接
                    try:
                        text = element.inner_text().strip()
                        href = element.get_attribute("href") or ""
                        if text and len(text) > 5:  # 过滤太短的文本
                            results.append({
                                "title": text[:100],  # 限制标题长度
                                "url": href,
                                "index": i + 1,
                                "type": "通用链接"
                            })
                    except Exception:
                        continue
                        
        except Exception as e:
            self.logger.error(f"提取搜索结果时出错: {e}")
            
        return results
    
    def _is_search_results_page(self) -> bool:
        """判断当前是否为搜索结果页面"""
        current_url = self.page.url.lower()
        search_indicators = [
            "search", "s?", "query", "q=", 
            "baidu.com/s", "google.com/search", "bing.com/search"
        ]
        return any(indicator in current_url for indicator in search_indicators)
    
    def _extract_full_page_content(self) -> str:
        """提取完整的页面HTML内容"""
        try:
            return self.page.content()
        except Exception as e:
            self.logger.error(f"提取完整页面内容失败: {e}")
            return ""
    
    def _extract_structured_data(self, target_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """提取结构化数据（表格、列表等）"""
        structured_data = []
        
        try:
            if target_selector:
                # 使用特定选择器
                elements = self.page.locator(target_selector).all()
                for element in elements:
                    try:
                        text = element.inner_text()
                        href = element.get_attribute("href") or ""
                        structured_data.append({
                            "text": text.strip(),
                            "href": href,
                            "type": "custom_selector"
                        })
                    except Exception:
                        continue
            else:
                # 自动检测结构化元素
                
                # 提取表格数据
                tables = self.page.locator("table").all()
                for table in tables:
                    try:
                        rows = table.locator("tr").all()
                        table_data = []
                        headers = []
                        
                        for i, row in enumerate(rows):
                            cells = row.locator("td, th").all()
                            row_data = [cell.inner_text().strip() for cell in cells]
                            
                            if i == 0 and row.locator("th").count() > 0:
                                headers = row_data
                            else:
                                if headers:
                                    cell_dict = dict(zip(headers, row_data))
                                else:
                                    cell_dict = {f"column_{j+1}": cell for j, cell in enumerate(row_data)}
                                table_data.append(cell_dict)
                        
                        if table_data:
                            structured_data.extend(table_data)
                    except Exception:
                        continue
                
                # 提取列表数据
                lists = self.page.locator("ul, ol").all()
                for list_elem in lists:
                    try:
                        items = list_elem.locator("li").all()
                        for item in items:
                            text = item.inner_text().strip()
                            if text and len(text) > 3:  # 过滤太短的内容
                                link = item.locator("a").first
                                href = link.get_attribute("href") if link.count() > 0 else ""
                                structured_data.append({
                                    "text": text,
                                    "href": href,
                                    "type": "list_item"
                                })
                    except Exception:
                        continue
                
                # 提取卡片式内容
                cards = self.page.locator(".card, .item, .post, .article, .entry").all()
                for card in cards:
                    try:
                        title_elem = card.locator("h1, h2, h3, h4, .title, .headline").first
                        desc_elem = card.locator("p, .description, .summary, .excerpt").first
                        link_elem = card.locator("a").first
                        
                        title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""
                        description = desc_elem.inner_text().strip() if desc_elem.count() > 0 else ""
                        href = link_elem.get_attribute("href") if link_elem.count() > 0 else ""
                        
                        if title or description:
                            structured_data.append({
                                "title": title,
                                "description": description[:200],  # 限制描述长度
                                "href": href,
                                "type": "card"
                            })
                    except Exception:
                        continue
        
        except Exception as e:
            self.logger.error(f"提取结构化数据失败: {e}")
        
        return structured_data
    
    def _auto_extract_content(self) -> Union[List[Dict[str, Any]], str]:
        """自动检测并提取适当的内容"""
        current_url = self.page.url.lower()
        
        # 如果是搜索结果页，优先提取搜索结果
        if self._is_search_results_page():
            search_results = self._extract_search_results()
            if search_results:
                return search_results
        
        # 尝试提取结构化数据
        structured_data = self._extract_structured_data()
        if structured_data:
            return structured_data
        
        # 如果都没有，返回主要内容区域的文本
        try:
            # 尝试获取主要内容区域
            main_selectors = [
                "main", "#main", ".main",
                "article", ".article", "#article",
                ".content", "#content",
                ".post", ".entry",
                "body"
            ]
            
            for selector in main_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0:
                        text = element.inner_text()
                        if text and len(text.strip()) > 100:  # 确保有意义的内容
                            return text.strip()
                except Exception:
                    continue
            
            # 最后的备选方案
            return self.page.inner_text("body")
            
        except Exception as e:
            self.logger.error(f"自动提取内容失败: {e}")
            return ""
        
    def _execute_smart_fill(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """智能填充操作，处理多元素选择器的情况"""
        query = step.get("query", "")
        if not query:
            return {"success": False, "message": "智能填充失败：查询内容为空"}
        
        # 百度特定的智能选择器策略
        selectors_priority = [
            "#kw",  # 传统搜索框（优先）
            "input[name='wd']",  # 备用搜索框
            "#chat-textarea"  # AI聊天框（最后选择）
        ]
        
        for selector in selectors_priority:
            try:
                # 检查元素是否存在且可见
                element = self.page.locator(selector)
                if element.count() > 0 and element.is_visible():
                    # 使用人类打字模拟
                    if self.behavior_simulator.is_enabled():
                        self.behavior_simulator.simulate_human_typing(self.page, selector, query)
                    else:
                        element.fill(query)
                    
                    self.logger.info(f"成功使用选择器 {selector} 填充内容")
                    return {
                        "success": True, 
                        "message": f"成功在百度搜索框中输入 '{query}'",
                        "used_selector": selector
                    }
            except Exception as e:
                self.logger.debug(f"选择器 {selector} 失败: {e}")
                continue
        
        return {
            "success": False, 
            "message": "智能填充失败：未找到可用的搜索框"
        }
    
    def _execute_smart_submit(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """智能提交操作，根据元素类型选择最佳提交方式"""
        # 百度特定的智能提交策略
        submit_strategies = [
            # 策略 1: 在传统搜索框上按 Enter
            {
                "selector": "#kw, input[name='wd']",
                "method": "enter_key",
                "description": "在传统搜索框上按回车键"
            },
            # 策略 2: 点击搜索按钮
            {
                "selector": "#su, .s_btn, .btn-search",
                "method": "click",
                "description": "点击搜索按钮"
            },
            # 策略 3: 在AI聊天框上按 Enter
            {
                "selector": "#chat-textarea",
                "method": "enter_key",
                "description": "在AI聊天框上按回车键"
            },
            # 策略 4: 点击AI提交按钮
            {
                "selector": "#chat-submit-button, .chat-submit",
                "method": "click",
                "description": "点击AI提交按钮"
            }
        ]
        
        for strategy in submit_strategies:
            try:
                selector = strategy["selector"]
                method = strategy["method"]
                description = strategy["description"]
                
                # 检查元素是否存在
                element = self.page.locator(selector)
                if element.count() > 0:
                    # 检查元素是否可见（对于按钮）
                    if method == "click":
                        visible_element = None
                        for i in range(element.count()):
                            if element.nth(i).is_visible():
                                visible_element = element.nth(i)
                                break
                        
                        if visible_element:
                            visible_element.click()
                            self.logger.info(f"成功执行策略: {description}")
                            return {
                                "success": True,
                                "message": f"成功{description}",
                                "strategy": description
                            }
                    else:  # enter_key
                        # 对于输入框，只需要存在即可
                        if element.count() > 0:
                            # 先聚焦到元素，然后按Enter
                            element.first.focus()
                            self.page.keyboard.press("Enter")
                            self.logger.info(f"成功执行策略: {description}")
                            return {
                                "success": True,
                                "message": f"成功{description}",
                                "strategy": description
                            }
            except Exception as e:
                self.logger.debug(f"策略 '{strategy['description']}' 失败: {e}")
                continue
        
        return {
            "success": False,
            "message": "智能提交失败：未找到可用的提交方式"
        }
    
    def get_behavior_stats(self) -> Dict[str, Any]:
        """获取人类行为模拟统计信息"""
        return self.behavior_simulator.get_enhanced_stats()
        
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
        
    def adjust_behavior_for_detection(self, detection_level: str) -> None:
        """
        根据检测级别调整行为模拟
        
        Args:
            detection_level: 检测级别 ("low", "medium", "high")
        """
        self.behavior_simulator.adjust_behavior_based_on_detection(detection_level)

    # --- Enhanced Action Handler Methods ---

    def _execute_drag_and_drop(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行拖拽操作"""
        source_selector = step.get("source_selector") or step.get("selector")
        target_selector = step.get("target_selector") or step.get("value")
        
        if not source_selector or not target_selector:
            return {"success": False, "message": "拖拽失败：缺少源选择器或目标选择器"}
        
        try:
            source_element = self._find_element_with_fallback(source_selector)
            target_element = self._find_element_with_fallback(target_selector)
            
            if not source_element or not target_element:
                return {"success": False, "message": "拖拽失败：找不到源元素或目标元素"}
            
            # 获取元素位置
            source_box = source_element.bounding_box()
            target_box = target_element.bounding_box()
            
            if not source_box or not target_box:
                return {"success": False, "message": "拖拽失败：无法获取元素位置"}
            
            # 计算中心点
            source_x = source_box["x"] + source_box["width"] / 2
            source_y = source_box["y"] + source_box["height"] / 2
            target_x = target_box["x"] + target_box["width"] / 2
            target_y = target_box["y"] + target_box["height"] / 2
            
            # 执行拖拽操作
            self.page.mouse.move(source_x, source_y)
            self.page.mouse.down()
            
            # 模拟自然的拖拽移动
            if self.behavior_simulator.is_enabled():
                self.behavior_simulator.simulate_mouse_movement(
                    self.page, (int(source_x), int(source_y)), (int(target_x), int(target_y))
                )
            else:
                self.page.mouse.move(target_x, target_y)
            
            self.page.mouse.up()
            
            return {
                "success": True, 
                "message": f"成功将元素从 {source_selector} 拖拽到 {target_selector}"
            }
            
        except Exception as e:
            return {"success": False, "message": f"拖拽操作失败: {str(e)}"}

    def _execute_right_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行右键点击操作"""
        selector = step.get("selector")
        if not selector:
            return {"success": False, "message": "右键点击失败：选择器为空"}
        
        try:
            element = self._find_element_with_fallback(selector)
            if not element:
                return {"success": False, "message": f"右键点击失败：找不到元素 {selector}"}
            
            element.click(button="right")
            return {"success": True, "message": f"成功右键点击元素 {selector}"}
            
        except Exception as e:
            return {"success": False, "message": f"右键点击失败: {str(e)}"}

    def _execute_double_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行双击操作"""
        selector = step.get("selector")
        if not selector:
            return {"success": False, "message": "双击失败：选择器为空"}
        
        try:
            element = self._find_element_with_fallback(selector)
            if not element:
                return {"success": False, "message": f"双击失败：找不到元素 {selector}"}
            
            element.dblclick()
            return {"success": True, "message": f"成功双击元素 {selector}"}
            
        except Exception as e:
            return {"success": False, "message": f"双击失败: {str(e)}"}

    def _execute_hover(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行悬停操作"""
        selector = step.get("selector")
        if not selector:
            return {"success": False, "message": "悬停失败：选择器为空"}
        
        try:
            element = self._find_element_with_fallback(selector)
            if not element:
                return {"success": False, "message": f"悬停失败：找不到元素 {selector}"}
            
            element.hover()
            
            # 悬停后等待
            hover_delay = self.behavior_simulator.get_base_delay() * 0.5
            if hover_delay > 0:
                time.sleep(hover_delay)
            
            return {"success": True, "message": f"成功悬停在元素 {selector}"}
            
        except Exception as e:
            return {"success": False, "message": f"悬停失败: {str(e)}"}

    def _execute_upload_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件上传操作"""
        selector = step.get("selector")
        file_path = step.get("file_path") or step.get("value")
        
        if not selector:
            return {"success": False, "message": "文件上传失败：选择器为空"}
        if not file_path:
            return {"success": False, "message": "文件上传失败：文件路径为空"}
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {"success": False, "message": f"文件上传失败：文件不存在 {file_path}"}
            
            element = self._find_element_with_fallback(selector)
            if not element:
                return {"success": False, "message": f"文件上传失败：找不到文件输入元素 {selector}"}
            
            # 设置文件
            element.set_input_files(file_path)
            
            return {
                "success": True, 
                "message": f"成功上传文件 {file_path} 到 {selector}"
            }
            
        except Exception as e:
            return {"success": False, "message": f"文件上传失败: {str(e)}"}

    def _execute_download_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件下载操作"""
        selector = step.get("selector")
        download_path = step.get("download_path") or "./downloads"
        
        if not selector:
            return {"success": False, "message": "文件下载失败：选择器为空"}
        
        try:
            # 确保下载目录存在
            os.makedirs(download_path, exist_ok=True)
            
            # 监听下载事件
            with self.page.expect_download() as download_info:
                element = self._find_element_with_fallback(selector)
                if not element:
                    return {"success": False, "message": f"文件下载失败：找不到下载链接 {selector}"}
                
                element.click()
            
            download = download_info.value
            
            # 保存文件
            file_name = download.suggested_filename
            file_path = os.path.join(download_path, file_name)
            download.save_as(file_path)
            
            return {
                "success": True, 
                "message": f"成功下载文件到 {file_path}",
                "file_path": file_path,
                "file_name": file_name
            }
            
        except Exception as e:
            return {"success": False, "message": f"文件下载失败: {str(e)}"}

    def _execute_switch_tab(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行切换标签页操作"""
        tab_index = step.get("tab_index")
        tab_url = step.get("tab_url") or step.get("value")
        
        try:
            context = self.page.context
            pages = context.pages
            
            if tab_index is not None:
                # 按索引切换
                if 0 <= tab_index < len(pages):
                    target_page = pages[tab_index]
                    target_page.bring_to_front()
                    # 更新当前页面引用
                    self.page = target_page
                    return {"success": True, "message": f"成功切换到标签页 {tab_index}"}
                else:
                    return {"success": False, "message": f"标签页索引 {tab_index} 超出范围"}
            
            elif tab_url:
                # 按URL切换
                for page in pages:
                    if tab_url in page.url:
                        page.bring_to_front()
                        self.page = page
                        return {"success": True, "message": f"成功切换到包含URL {tab_url} 的标签页"}
                
                return {"success": False, "message": f"未找到包含URL {tab_url} 的标签页"}
            
            else:
                return {"success": False, "message": "切换标签页失败：缺少标签页索引或URL"}
                
        except Exception as e:
            return {"success": False, "message": f"切换标签页失败: {str(e)}"}

    def _execute_new_tab(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行新建标签页操作"""
        url = step.get("url") or step.get("value")
        
        try:
            context = self.page.context
            new_page = context.new_page()
            
            if url:
                new_page.goto(url, wait_until="domcontentloaded")
                message = f"成功新建标签页并导航到 {url}"
            else:
                message = "成功新建空白标签页"
            
            # 切换到新标签页
            new_page.bring_to_front()
            self.page = new_page
            
            return {"success": True, "message": message}
            
        except Exception as e:
            return {"success": False, "message": f"新建标签页失败: {str(e)}"}

    def _execute_close_tab(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行关闭标签页操作"""
        tab_index = step.get("tab_index")
        
        try:
            context = self.page.context
            pages = context.pages
            
            if tab_index is not None:
                # 关闭指定索引的标签页
                if 0 <= tab_index < len(pages):
                    target_page = pages[tab_index]
                    target_page.close()
                    
                    # 如果关闭的是当前页面，切换到第一个可用页面
                    if target_page == self.page and len(pages) > 1:
                        remaining_pages = [p for p in pages if p != target_page]
                        if remaining_pages:
                            self.page = remaining_pages[0]
                            self.page.bring_to_front()
                    
                    return {"success": True, "message": f"成功关闭标签页 {tab_index}"}
                else:
                    return {"success": False, "message": f"标签页索引 {tab_index} 超出范围"}
            else:
                # 关闭当前标签页
                self.page.close()
                return {"success": True, "message": "成功关闭当前标签页"}
                
        except Exception as e:
            return {"success": False, "message": f"关闭标签页失败: {str(e)}"}

    def _execute_zoom(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行页面缩放操作"""
        zoom_level = step.get("zoom_level") or step.get("value")
        
        if zoom_level is None:
            return {"success": False, "message": "页面缩放失败：缺少缩放级别"}
        
        try:
            # 转换为浮点数
            zoom_factor = float(zoom_level)
            
            # 设置页面缩放
            self.page.evaluate(f"document.body.style.zoom = '{zoom_factor}'")
            
            return {
                "success": True, 
                "message": f"成功设置页面缩放为 {zoom_factor}"
            }
            
        except Exception as e:
            return {"success": False, "message": f"页面缩放失败: {str(e)}"}

    def _execute_fullscreen(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行全屏操作"""
        enable = step.get("enable", True)
        
        try:
            if enable:
                # 进入全屏
                self.page.evaluate("""
                    if (document.documentElement.requestFullscreen) {
                        document.documentElement.requestFullscreen();
                    } else if (document.documentElement.webkitRequestFullscreen) {
                        document.documentElement.webkitRequestFullscreen();
                    } else if (document.documentElement.msRequestFullscreen) {
                        document.documentElement.msRequestFullscreen();
                    }
                """)
                message = "成功进入全屏模式"
            else:
                # 退出全屏
                self.page.evaluate("""
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                """)
                message = "成功退出全屏模式"
            
            return {"success": True, "message": message}
            
        except Exception as e:
            return {"success": False, "message": f"全屏操作失败: {str(e)}"}

    def _execute_smart_wait(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能等待操作"""
        wait_type = step.get("wait_type", "auto")
        selector = step.get("selector")
        timeout = step.get("timeout", 30000)
        condition = step.get("condition")
        
        try:
            if wait_type == "network_idle":
                # 等待网络空闲
                self.page.wait_for_load_state("networkidle", timeout=timeout)
                return {"success": True, "message": "成功等待网络空闲"}
                
            elif wait_type == "element_visible":
                # 等待元素可见
                if not selector:
                    return {"success": False, "message": "智能等待失败：等待元素可见需要选择器"}
                self.page.wait_for_selector(selector, state="visible", timeout=timeout)
                return {"success": True, "message": f"成功等待元素 {selector} 可见"}
                
            elif wait_type == "element_hidden":
                # 等待元素隐藏
                if not selector:
                    return {"success": False, "message": "智能等待失败：等待元素隐藏需要选择器"}
                self.page.wait_for_selector(selector, state="hidden", timeout=timeout)
                return {"success": True, "message": f"成功等待元素 {selector} 隐藏"}
                
            elif wait_type == "url_change":
                # 等待URL变化
                current_url = self.page.url
                self.page.wait_for_url(lambda url: url != current_url, timeout=timeout)
                return {"success": True, "message": "成功等待URL变化"}
                
            else:
                return {"success": False, "message": f"不支持的等待类型: {wait_type}"}
                
        except Exception as e:
            return {"success": False, "message": f"智能等待失败: {str(e)}"}