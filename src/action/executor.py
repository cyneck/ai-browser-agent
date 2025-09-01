#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动作执行器

负责安全地执行标准化的JSON格式指令，与浏览器交互。
"""

import json
import time
import base64
from typing import Dict, Any, List, Optional, Callable, Union

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
            "key": self._execute_key,  # Add keyboard action support
            "select": self._execute_select,
            "wait": self._execute_wait,
            "screenshot": self._execute_screenshot,
            "extract": self._execute_extract,
            "extract_results": self._execute_extract_results,
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
