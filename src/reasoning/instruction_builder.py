#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
指令构建器

负责将用户的自然语言指令转换为标准化的JSON格式指令，供执行层执行。
"""

import json
import os
import re
from typing import Dict, Any, List, Optional

# 可选导入 Gemini SDK，测试可通过打桩替换
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

from src.common.config import get_config
from src.common.logger import get_logger


class InstructionBuilder:
    """指令构建器类，负责构建标准化的JSON格式指令"""

    def __init__(self):
        """初始化指令构建器"""
        self.logger = get_logger()
        self.api_key = get_config("GEMINI_API_KEY")
        self.allowed_domains = get_config("ALLOWED_DOMAINS", "*")

    def build(self, user_instruction: str, page_data: Dict[str, Any],
              session_state: Dict[str, Any]) -> Dict[str, Any]:
        """构建标准化的JSON格式指令"""
        try:
            self.logger.info(f"构建指令: {user_instruction}")

            # 若页面无效/空白，优先从指令中提取 URL 或生成 Bing 搜索前置步骤
            if not page_data or not page_data.get("is_valid", True) or page_data.get("page_type") == "blank":
                nav_only = self._maybe_build_navigation_first(user_instruction)
                if nav_only:
                    return nav_only
                # 如果没有明确URL，则使用 Bing 前置检索
                bing_pre_search = self._build_bing_pre_search(user_instruction)
                if bing_pre_search:
                    return bing_pre_search

            # 在已加载页面上，尝试已知站点的启发式动作（如搜索框操作）
            known = self._maybe_build_known_site_action(user_instruction, page_data)
            if known:
                return known

            # 提取对话历史
            conversation_history = session_state.get("conversation_history", [])

            # 构建提示词
            prompt = self._build_prompt(
                user_instruction,
                page_data,
                conversation_history
            )

            # 调用LLM生成指令
            json_instruction = self._call_llm(prompt)

            # 验证指令格式
            validated_instruction = self._validate_instruction(json_instruction, page_data)

            # 更新对话历史
            conversation_history.append({
                "role": "user",
                "content": user_instruction
            })
            conversation_history.append({
                "role": "assistant",
                "content": json.dumps(validated_instruction)
            })

            # 限制对话历史长度
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]

            # 更新会话状态
            session_state["conversation_history"] = conversation_history

            self.logger.info("指令构建完成")
            return validated_instruction
        except Exception as e:
            self.logger.error(f"构建指令时发生错误: {str(e)}")
            # 返回错误指令
            return {
                "action": "error",
                "error": str(e),
                "original_instruction": user_instruction
            }

    def _build_prompt(self, user_instruction: str, page_data: Dict[str, Any],
                      conversation_history: List[Dict[str, str]]) -> str:
        """构建提示词"""
        system_prompt = """
        你是一个专业的网页自动化助手，负责将用户的自然语言指令转换为标准化的JSON格式指令。
        
        你的任务是：
        1. 理解用户的意图
        2. 分析当前页面的结构和内容
        3. 生成一个或多个操作步骤，以完成用户的指令
        
        你必须严格按照以下JSON格式输出指令：
        ```json
        {
            "action": "操作类型",  // 必需字段，如navigate, click, fill, select等
            "selector": "元素选择器",  // 可选字段，取决于操作类型
            "value": "输入值",  // 可选字段，取决于操作类型
            "description": "操作描述"  // 必需字段，描述此操作的目的
        }
        ```
        
        或者对于多步操作：
        ```json
        {
            "steps": [
                {
                    "action": "操作类型1",
                    "selector": "元素选择器1",
                    "value": "输入值1",
                    "description": "操作1描述"
                },
                {
                    "action": "操作类型2",
                    "selector": "元素选择器2",
                    "value": "输入值2",
                    "description": "操作2描述"
                }
            ],
            "description": "整体操作描述"
        }
        ```
        
        支持的操作类型包括：
        - navigate: 导航到指定URL（必须是带 http/https 的绝对URL，如 https://example.com）
        - click: 点击元素
        - fill: 在输入框中输入文本
        - select: 在下拉菜单中选择选项
        - wait: 等待指定时间或元素出现
        - screenshot: 截取屏幕截图
        - extract: 提取页面内容
        - scroll: 滚动页面
        - back: 返回上一页
        - forward: 前进到下一页
        - refresh: 刷新页面
        - close: 关闭当前页面
        - error: 表示无法执行用户指令
        
        重要：
        - 如果你判断用户意图需要先访问某个站点，但当前页面信息不足，请只返回前置 navigate+wait 步骤。
        - 如果当前已处在目标页面，请不要再次包含 navigate 操作。
        - 当 elements/ARIA 等上下文为空时，仍需给出可执行的最佳猜测选择器（例如常见站点的通用选择器），避免返回 error。
        - 生成选择器时，优先依据页面结构、ARIA信息、稳定属性（如 data-*），避免脆弱的纯文本定位。
        - 返回的JSON必须严格合法，不要包含注释或无关文本。
        """

        user_prompt = f"""
        当前页面信息：
        URL: {page_data.get('url', 'N/A')}
        标题: {page_data.get('title', 'N/A')}
        页面类型: {page_data.get('page_type', 'unknown')}
        
        页面上的可交互元素：
        {json.dumps(page_data.get('elements', []), ensure_ascii=False, indent=2)}
        
        页面上的功能区域：
        {json.dumps(page_data.get('functional_areas', []), ensure_ascii=False, indent=2)}
        
        ARIA 概览（可选）：
        {json.dumps(page_data.get('aria_snapshot') or {}, ensure_ascii=False)[:800]}
        
        用户指令: {user_instruction}
        
        请根据用户指令和页面信息，生成标准化的JSON格式指令。
        """

        if conversation_history:
            conversation_context = "\n对话历史:\n"
            for message in conversation_history[-4:]:
                role = "用户" if message["role"] == "user" else "助手"
                conversation_context += f"{role}: {message['content']}\n"
            user_prompt = conversation_context + "\n" + user_prompt

        return system_prompt + "\n\n" + user_prompt

    def _detect_navigation_intent_and_url(self, user_instruction: str) -> Optional[str]:
        """识别导航意图并提取规范化 URL。
        规则：优先匹配显式 http/https；否则匹配裸域（ASCII 顶级域），忽略周边中文词缀（如“访问”“网站”）。
        """
        # 1) 显式 URL（http/https）
        m = re.search(r"https?://[A-Za-z0-9.-]+(?:\.[A-Za-z]{2,24})(?:/[^\s]*)?", user_instruction)
        if m:
            return m.group(0)
        # 2) 裸域（仅ASCII域名与TLD），避免把中文词缀合入
        m2 = re.search(r"(?<![A-Za-z0-9.-])([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24})(?![A-Za-z0-9.-])",
                       user_instruction)
        if m2:
            return "https://" + m2.group(1)
        return None

    @staticmethod
    def _extract_code_blocks(text: str, language: str = '') -> List[str]:
        """
        提取字符串中的代码块

        Args:
            text (str): 包含代码块的字符串
            language (str, optional): 指定代码块的语言（如 'json'）。默认为空，匹配所有代码块。

        Returns:
            list: 提取到的代码块列表（已去除前后空白字符）
        """
        lang = re.escape(language)
        pattern = re.compile(rf"```{lang}\s*\n(.*?)```", re.DOTALL | re.IGNORECASE) if language else re.compile(r"```\s*\n(.*?)```", re.DOTALL)
        matches = pattern.findall(text or "")
        return [match.strip() for match in matches]

    def _maybe_build_navigation_first(self, user_instruction: str) -> Optional[Dict[str, Any]]:
        """在页面为空时，尝试仅生成导航步骤（URL 直达）。"""
        url = self._detect_navigation_intent_and_url(user_instruction)
        if not url:
            return None
        try:
            self._validate_url_safety(url)
        except Exception as e:
            self.logger.warning(f"URL 不在允许域名范围内: {url} - {e}")
            return {"action": "error", "error": str(e)}
        return {
            "steps": [
                {"action": "navigate", "value": url, "description": f"导航到 {url}"},
                {"action": "wait", "value": 2000, "description": "等待页面就绪(2秒)"}
            ],
            "description": f"前置导航到 {url} 并等待页面加载"
        }

    def _build_bing_pre_search(self, user_instruction: str) -> Dict[str, Any]:
        """当无法直达 URL 时，先在 Bing 搜索预检索站点/意图。"""
        from urllib.parse import quote_plus
        query = quote_plus(user_instruction.strip())
        url = f"https://www.bing.com/search?q={query}"
        try:
            self._validate_url_safety(url)
        except Exception as e:
            return {"action": "error", "error": str(e)}
        return {
            "steps": [
                {"action": "navigate", "value": url, "description": f"在Bing搜索：{user_instruction}"},
                {"action": "wait", "value": 2000, "description": "等待搜索结果加载(2秒)"}
            ],
            "description": "前置导航到Bing进行检索"
        }

    def _intent_is_search(self, instruction: str) -> bool:
        return bool(re.search(r"(搜索|查询|找|news|search)", instruction, re.IGNORECASE))

    def _extract_query_from_instruction(self, instruction: str) -> str:
        m = re.search(r"(?:搜索|查询|找)(.+)", instruction)
        if m:
            return m.group(1).strip().strip("'\"")
        return instruction.strip().strip("'\"")

    def _maybe_build_known_site_action(self, user_instruction: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """在已知站点（如百度/Bing/Google）上生成搜索动作的启发式步骤。"""
        try:
            if not self._intent_is_search(user_instruction):
                return None
            url = (page_data or {}).get("url") or ""
            host = ""
            if url:
                m = re.search(r"://([^/]+)/?", url)
                if m:
                    host = m.group(1).lower()
            if not host:
                return None
            query = self._extract_query_from_instruction(user_instruction)
            steps: List[Dict[str, Any]] = []
            # 百度
            if "baidu.com" in host:
                steps = [
                    {"action": "wait", "selector": "id=kw", "timeout": 5000, "description": "等待搜索框出现"},
                    {"action": "fill", "selector": "id=kw", "value": query, "description": f"在百度搜索框输入 '{query}'"},
                    {"action": "click", "selector": "id=su", "description": "点击百度搜索按钮"}
                ]
            # Bing
            elif "bing.com" in host:
                steps = [
                    {"action": "wait", "selector": "input[name=q]", "timeout": 5000, "description": "等待搜索框出现"},
                    {"action": "fill", "selector": "input[name=q]", "value": query, "description": f"在Bing搜索框输入 '{query}'"},
                    {"action": "click", "selector": "#sb_form_go", "description": "点击Bing搜索按钮"}
                ]
            # Google
            elif "google." in host:
                steps = [
                    {"action": "wait", "selector": "textarea[name=q]", "timeout": 5000, "description": "等待搜索框出现"},
                    {"action": "fill", "selector": "textarea[name=q]", "value": query, "description": f"在Google搜索框输入 '{query}'"},
                    {"action": "click", "selector": "input[name=btnK]", "description": "点击Google搜索按钮"}
                ]
            else:
                return None
            return {"steps": steps, "description": f"站内搜索: {query}"}
        except Exception:
            return None

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用LLM生成指令"""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY 未配置")
        if genai is None:
            raise RuntimeError("Gemini SDK 未安装")
        try:
            genai.configure(api_key=self.api_key)
            model_name = get_config("GEMINI_MODEL", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt)
            text = getattr(resp, "text", "") or ""
            try:
                blocks = self._extract_code_blocks(text, "json")
                if blocks:
                    text = blocks[0]
                return json.loads(text)
            except Exception:
                return {"action": "error", "error": "LLM未返回有效JSON", "raw": (text or "")[:500]}
        except Exception as e:
            self.logger.error(f"调用Gemini失败: {e}")
            return {"action": "error", "error": str(e)}

    def _validate_instruction(self, instruction: Dict[str, Any],
                              page_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证指令格式和安全性"""
        if "action" not in instruction and "steps" not in instruction:
            raise ValueError("指令缺少必需的'action'或'steps'字段")
        if "steps" in instruction:
            for i, step in enumerate(instruction["steps"]):
                if "action" not in step:
                    raise ValueError(f"第{i + 1}步操作缺少必需的'action'字段")
                if step["action"] not in [
                    "navigate", "click", "fill", "select", "wait",
                    "screenshot", "extract", "scroll", "back",
                    "forward", "refresh", "close", "error"
                ]:
                    raise ValueError(f"第{i + 1}步操作的类型'{step['action']}'不受支持")
                if step["action"] == "navigate" and "value" not in step:
                    raise ValueError(f"第{i + 1}步'navigate'操作缺少必需的'value'字段")
                if step["action"] in ["click", "fill", "select"] and "selector" not in step:
                    raise ValueError(f"第{i + 1}步'{step['action']}'操作缺少必需的'selector'字段")
                if step["action"] in ["fill", "select"] and "value" not in step:
                    raise ValueError(f"第{i + 1}步'{step['action']}'操作缺少必需的'value'字段")
                if step["action"] == "navigate":
                    self._validate_url_safety(step["value"])
        else:
            if instruction["action"] not in [
                "navigate", "click", "fill", "select", "wait",
                "screenshot", "extract", "scroll", "back",
                "forward", "refresh", "close", "error"
            ]:
                raise ValueError(f"操作类型'{instruction['action']}'不受支持")
            if instruction["action"] == "navigate" and "value" not in instruction:
                raise ValueError("'navigate'操作缺少必需的'value'字段")
            if instruction["action"] in ["click", "fill", "select"] and "selector" not in instruction:
                raise ValueError(f"'{instruction['action']}'操作缺少必需的'selector'字段")
            if instruction["action"] in ["fill", "select"] and "value" not in instruction:
                raise ValueError(f"'{instruction['action']}'操作缺少必需的'value'字段")
            if instruction["action"] == "navigate":
                self._validate_url_safety(instruction["value"])
        return instruction

    def _validate_url_safety(self, url: str):
        """验证URL安全性"""
        if self.allowed_domains == "*":
            return
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            main_domain = '.'.join(domain_parts[-2:])
        else:
            main_domain = domain
