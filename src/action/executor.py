#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动作执行器

负责安全地执行标准化的JSON格式指令，与浏览器交互。
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable

from jinja2 import Template, Environment, FileSystemLoader
from playwright.sync_api import Page
import base64

from src.common.logger import get_logger
from src.action.state_manager import StateManager
from src.action.error_handler import ErrorHandler
from src.action.safety_validator import SafetyValidator


class ActionExecutor:
    """动作执行器类，负责安全地执行指令"""
    
    def __init__(self, page: Page, state_manager: Optional[StateManager] = None, error_handler: Optional[ErrorHandler] = None):
        """初始化动作执行器
        
        Args:
            page: Playwright页面对象
        """
        self.logger = get_logger()
        self.page = page
        self.template_env = self._setup_template_env()
        self.execution_namespace = {"__builtins__": {"Exception": Exception}}
        self._setup_execution_namespace()
        self.state_manager = state_manager or StateManager()
        self.error_handler = error_handler or ErrorHandler()
        self.safety_validator = SafetyValidator(self.get_supported_actions())
    
    def execute(self, instruction: Dict[str, Any], session_state: Dict[str, Any],
                timeout: int = 60) -> Dict[str, Any]:
        """执行指令
        
        Args:
            instruction: 标准化的JSON格式指令
            session_state: 会话状态
            timeout: 执行超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 记录指令
            self.logger.info(f"执行指令: {json.dumps(instruction, ensure_ascii=False)}")
            
            # 更新执行命名空间
            self.execution_namespace.update({
                "page": self.page,
                "session_state": session_state,
                "instruction": instruction
            })
            
            # 先进行安全校验与转义
            instruction = self.safety_validator.validate_and_sanitize(instruction)

            # 如果是多步操作，逐步执行
            if "steps" in instruction:
                return self._execute_multi_steps(instruction, timeout)
            else:
                # 单步操作
                return self._execute_single_action(instruction, timeout)
        except Exception as e:
            return self.error_handler.handle_error(e, instruction, {
                "session_state": session_state
            })

    def get_supported_actions(self) -> List[str]:
        try:
            return [t[:-3] for t in self.template_env.list_templates(filter_func=lambda n: n.endswith('.j2'))]
        except Exception:
            # 回退到固定集合（与创建模板一致）
            return [
                "navigate", "click", "type", "select", "wait",
                "screenshot", "extract", "scroll", "back", "forward",
                "refresh", "close", "error"
            ]
    
    def _setup_template_env(self) -> Environment:
        """设置模板环境
        
        Returns:
            Environment: Jinja2模板环境
        """
        # 获取模板目录路径
        template_dir = Path(__file__).parent / "templates"
        
        # 如果模板目录不存在，创建它
        if not template_dir.exists():
            template_dir.mkdir(parents=True)
            
            # 创建基本模板文件
            self._create_basic_templates(template_dir)
        
        # 创建Jinja2环境
        env = Environment(loader=FileSystemLoader(template_dir))
        
        return env
    
    def _create_basic_templates(self, template_dir: Path):
        """创建基本模板文件
        
        Args:
            template_dir: 模板目录路径
        """
        # 导航模板
        navigate_template = """
# 导航到指定URL
try:
    page.goto("{{ instruction.value }}", wait_until="domcontentloaded")
    result = {
        "success": True,
        "message": "成功导航到 {{ instruction.value }}"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "导航失败",
        "error": str(e)
    }
"""
        
        # 点击模板
        click_template = """
# 点击元素
try:
    element = page.locator("{{ instruction.selector }}")
    element.click()
    result = {
        "success": True,
        "message": "成功点击元素 {{ instruction.selector }}"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "点击失败",
        "error": str(e)
    }
"""
        
        # 输入模板
        type_template = """
# 在输入框中输入文本
try:
    element = page.locator("{{ instruction.selector }}")
    element.fill("{{ instruction.value }}")
    result = {
        "success": True,
        "message": "成功在 {{ instruction.selector }} 中输入文本"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "输入失败",
        "error": str(e)
    }
"""
        
        # 选择模板
        select_template = """
# 在下拉菜单中选择选项
try:
    element = page.locator("{{ instruction.selector }}")
    element.select_option(value="{{ instruction.value }}")
    result = {
        "success": True,
        "message": "成功在 {{ instruction.selector }} 中选择选项 {{ instruction.value }}"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "选择失败",
        "error": str(e)
    }
"""
        
        # 等待模板
        wait_template = """
# 等待指定时间或元素出现
try:
    {% if instruction.selector %}
    page.wait_for_selector("{{ instruction.selector }}", timeout={{ instruction.timeout|default(30000) }})
    result = {
        "success": True,
        "message": "成功等待元素 {{ instruction.selector }} 出现"
    }
    {% elif instruction.value %}
    page.wait_for_timeout({{ instruction.value }})
    result = {
        "success": True,
        "message": "成功等待 {{ instruction.value }} 毫秒"
    }
    {% else %}
    page.wait_for_load_state("domcontentloaded")
    result = {
        "success": True,
        "message": "成功等待页面加载"
    }
    {% endif %}
except Exception as e:
    result = {
        "success": False,
        "message": "等待失败",
        "error": str(e)
    }
"""
        
        # 截图模板
        screenshot_template = """
# 截取屏幕截图
try:
    screenshot_bytes = page.screenshot()
    import base64
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
    result = {
        "success": True,
        "message": "成功截取屏幕截图",
        "screenshot": screenshot_base64
    }
except Exception as e:
    result = {
        "success": False,
        "message": "截图失败",
        "error": str(e)
    }
"""
        
        # 提取内容模板
        extract_template = """
# 提取页面内容
try:
    {% if instruction.selector %}
    element = page.locator("{{ instruction.selector }}")
    content = element.inner_text()
    result = {
        "success": True,
        "message": "成功提取内容",
        "content": content
    }
    {% else %}
    content = page.content()
    result = {
        "success": True,
        "message": "成功提取页面内容",
        "content": content
    }
    {% endif %}
except Exception as e:
    result = {
        "success": False,
        "message": "提取内容失败",
        "error": str(e)
    }
"""
        
        # 滚动模板
        scroll_template = """
# 滚动页面
try:
    {% if instruction.selector %}
    element = page.locator("{{ instruction.selector }}")
    element.scroll_into_view_if_needed()
    result = {
        "success": True,
        "message": "成功滚动到元素 {{ instruction.selector }}"
    }
    {% elif instruction.value %}
    page.evaluate("window.scrollBy(0, {{ instruction.value }})")
    result = {
        "success": True,
        "message": "成功滚动页面 {{ instruction.value }} 像素"
    }
    {% else %}
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    result = {
        "success": True,
        "message": "成功滚动到页面底部"
    }
    {% endif %}
except Exception as e:
    result = {
        "success": False,
        "message": "滚动失败",
        "error": str(e)
    }
"""
        
        # 返回上一页模板
        back_template = """
# 返回上一页
try:
    page.go_back()
    result = {
        "success": True,
        "message": "成功返回上一页"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "返回上一页失败",
        "error": str(e)
    }
"""
        
        # 前进到下一页模板
        forward_template = """
# 前进到下一页
try:
    page.go_forward()
    result = {
        "success": True,
        "message": "成功前进到下一页"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "前进到下一页失败",
        "error": str(e)
    }
"""
        
        # 刷新页面模板
        refresh_template = """
# 刷新页面
try:
    page.reload()
    result = {
        "success": True,
        "message": "成功刷新页面"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "刷新页面失败",
        "error": str(e)
    }
"""
        
        # 关闭页面模板
        close_template = """
# 关闭当前页面
try:
    page.close()
    result = {
        "success": True,
        "message": "成功关闭页面"
    }
except Exception as e:
    result = {
        "success": False,
        "message": "关闭页面失败",
        "error": str(e)
    }
"""
        
        # 错误模板
        error_template = """
# 错误处理
result = {
    "success": False,
    "message": "无法执行指令",
    "error": "{{ instruction.error|default('未知错误') }}"
}
"""
        
        # 创建模板文件
        templates = {
            "navigate.j2": navigate_template,
            "click.j2": click_template,
            "type.j2": type_template,
            "select.j2": select_template,
            "wait.j2": wait_template,
            "screenshot.j2": screenshot_template,
            "extract.j2": extract_template,
            "scroll.j2": scroll_template,
            "back.j2": back_template,
            "forward.j2": forward_template,
            "refresh.j2": refresh_template,
            "close.j2": close_template,
            "error.j2": error_template
        }
        
        for filename, content in templates.items():
            with open(template_dir / filename, "w", encoding="utf-8") as f:
                f.write(content)
    
    def _setup_execution_namespace(self):
        """设置执行命名空间"""
        # 基本工具函数
        def ask_user(prompt: str, password: bool = False) -> str:
            """向用户请求输入
            
            Args:
                prompt: 提示信息
                password: 是否是密码输入
                
            Returns:
                str: 用户输入
            """
            if password:
                import getpass
                return getpass.getpass(prompt)
            else:
                return input(prompt)
        
        def extract_search_query(instruction: str) -> str:
            """从指令中提取搜索关键词
            
            Args:
                instruction: 用户指令
                
            Returns:
                str: 搜索关键词
            """
            # 简单实现，实际应该使用更复杂的NLP方法
            search_patterns = [
                r"搜索[\s]*([^\n]+)",
                r"查找[\s]*([^\n]+)",
                r"search[\s]*for[\s]*([^\n]+)",
                r"search[\s]*([^\n]+)"
            ]
            
            for pattern in search_patterns:
                match = re.search(pattern, instruction, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            # 如果没有匹配，返回整个指令
            return instruction

        def to_base64(binary: bytes) -> str:
            return base64.b64encode(binary).decode("utf-8")
        
        # 更新命名空间
        self.execution_namespace.update({
            "ask_user": ask_user,
            "extract_search_query": extract_search_query,
            "time": time,
            "re": re,
            "to_base64": to_base64
        })
    
    def _execute_multi_steps(self, instruction: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行多步操作
        
        Args:
            instruction: 包含多步操作的指令
            timeout: 执行超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        steps = instruction.get("steps", [])
        description = instruction.get("description", "执行多步操作")
        
        self.logger.info(f"开始执行多步操作: {description}")
        
        # 记录每一步的结果
        step_results = []
        overall_success = True
        error_message = ""
        
        # 设置超时时间
        start_time = time.time()
        
        # 逐步执行
        for i, step in enumerate(steps):
            # 检查是否超时
            if time.time() - start_time > timeout:
                overall_success = False
                error_message = f"执行超时（{timeout}秒）"
                break
            
            # 执行单步操作
            step_result = self._execute_single_action(step)
            step_results.append(step_result)
            
            # 如果某一步失败，整体操作失败
            if not step_result.get("success", False):
                overall_success = False
                error_message = f"第{i+1}步操作失败: {step_result.get('error', '未知错误')}"
                break
        
        # 构建整体结果
        result = {
            "success": overall_success,
            "message": description if overall_success else error_message,
            "step_results": step_results
        }
        
        if not overall_success and error_message:
            result["error"] = error_message
        
        return result
    
    def _execute_single_action(self, instruction: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """执行单步操作
        
        Args:
            instruction: 单步操作指令
            timeout: 执行超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        action = instruction.get("action")
        description = instruction.get("description", f"执行{action}操作")
        
        self.logger.info(f"执行操作: {action} - {description}")
        
        # 获取对应的模板
        try:
            template = self.template_env.get_template(f"{action}.j2")
        except Exception as e:
            self.logger.error(f"获取模板失败: {str(e)}")
            return {
                "success": False,
                "message": f"不支持的操作类型: {action}",
                "error": str(e)
            }
        
        # 渲染模板
        try:
            code = template.render(instruction=instruction)
        except Exception as e:
            self.logger.error(f"渲染模板失败: {str(e)}")
            return {
                "success": False,
                "message": "渲染模板失败",
                "error": str(e)
            }
        
        # 执行代码
        try:
            # 设置局部变量result，用于存储执行结果
            local_vars = {}
            
            # 执行代码
            exec(code, self.execution_namespace, local_vars)
            
            # 获取执行结果
            result = local_vars.get("result", {
                "success": False,
                "message": "执行代码未返回结果",
                "error": "未知错误"
            })
            
            # 简单状态写回（可选）
            if isinstance(result, dict) and result.get("success"):
                self.state_manager.set_state("last_action", action)
                self.state_manager.set_state("last_message", result.get("message"))
            return result
        except Exception as e:
            return self.error_handler.handle_error(e, instruction, {})