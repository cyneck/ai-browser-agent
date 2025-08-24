#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
指令构建器

负责将用户的自然语言文本转换为标准化的JSON格式指令，供执行层执行。

术语说明：
- text/user_text: 用户输入的自然语言文本（例如："在bing网站检索北京秋天"）
- instruction/json_instruction: 系统内部使用的可执行JSON格式指令
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
    """指令构建器类，负责将自然语言文本构建为标准化的JSON格式指令"""

    def __init__(self):
        """初始化指令构建器"""
        self.logger = get_logger()
        self.api_key = get_config("GEMINI_API_KEY")


    def build(self, user_text: str, page_data: Dict[str, Any],
              session_state: Dict[str, Any]) -> Dict[str, Any]:
        """将用户自然语言文本构建为标准化的JSON格式指令
        
        Args:
            user_text: 用户输入的自然语言文本（如："在bing网站检索北京秋天"）
            page_data: 当前页面的结构化数据
            session_state: 会话状态
            
        Returns:
            Dict[str, Any]: 可执行的JSON格式指令
        """
        try:
            self.logger.info(f"构建指令: {user_text}")

            # 若页面无效/空白，优先从指令中提取 URL 或生成 Bing 搜索前置步骤
            if not page_data or not page_data.get("is_valid", True) or page_data.get("page_type") == "blank":
                nav_only = self._maybe_build_navigation_first(user_text)
                if nav_only:
                    return nav_only
                # 如果没有明确URL，则使用 Bing 前置检索
                bing_pre_search = self._build_bing_pre_search(user_text)
                if bing_pre_search:
                    return bing_pre_search

            # 在已加载页面上，尝试已知站点的启发式动作（如搜索框操作）
            known = self._maybe_build_known_site_action(user_text, page_data)
            if known:
                return known

            # 提取对话历史
            conversation_history = session_state.get("conversation_history", [])

            # 构建提示词
            prompt = self._build_prompt(
                user_text,
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
                "content": user_text
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
                "original_text": user_text
            }

    def build_optimized(self, user_text: str, page_data: Dict[str, Any], 
                       session_state: Dict[str, Any]) -> Dict[str, Any]:
        """优化版本：智能构建指令，避免双重LLM调用
        
        与普通 build() 方法的区别：
        1. 更好的上下文感知：分析当前页面状态和用户意图
        2. 一次性生成完整指令：包括导航+操作的完整流程
        3. 避免分阶段执行：减少LLM调用次数
        
        Args:
            user_text: 用户输入的自然语言文本
            page_data: 当前页面的结构化数据
            session_state: 会话状态，包含对话历史等
            
        Returns:
            Dict[str, Any]: 标准化的JSON格式指令
        """
        try:
            self.logger.info(f"优化构建指令: {user_text}")
            
            # 提取对话历史
            conversation_history = session_state.get("conversation_history", [])
            
            # 先检查简单的预定义操作（无需LLM）
            simple_action = self._try_simple_heuristics(user_text, page_data)
            if simple_action:
                self.logger.info("使用简单启发式规则，无需LLM")
                return simple_action
            
            # 智能上下文分析
            context_analysis = self._analyze_context(user_text, page_data, conversation_history)
            
            # 构建增强的提示词（一次性生成完整流程）
            enhanced_prompt = self._build_enhanced_prompt(
                user_text, 
                page_data, 
                conversation_history,
                context_analysis
            )
            
            # 单次LLM调用生成完整指令
            json_instruction = self._call_llm(enhanced_prompt)
            
            # 验证指令格式
            validated_instruction = self._validate_instruction(json_instruction, page_data)
            
            # 更新对话历史
            conversation_history.append({
                "role": "user",
                "content": user_text
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
            
            self.logger.info("优化指令构建完成")
            return validated_instruction
            
        except Exception as e:
            self.logger.error(f"优化构建指令时发生错误: {str(e)}")
            # 错误时降级到普通构建方法
            self.logger.warning("降级到普通构建方法")
            return self.build(user_text, page_data, session_state)

    def _try_simple_heuristics(self, user_text: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """尝试简单的启发式规则，避免不必要的LLM调用"""
        # 检查是否为单纯导航意图
        nav_url = self._detect_navigation_intent_and_url(user_text)
        if nav_url and (not page_data or not page_data.get("is_valid", True)):
            return {
                "action": "navigate",
                "value": nav_url,
                "description": f"导航到 {nav_url}"
            }
        
        # 检查是否为已知站点的简单操作
        simple_action = self._maybe_build_known_site_action(user_text, page_data)
        if simple_action:
            return simple_action
            
        return None

    def _analyze_context(self, user_text: str, page_data: Dict[str, Any], 
                        conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析上下文信息，为智能指令构建提供依据"""
        analysis = {
            "needs_navigation": False,
            "target_url": None,
            "current_page_suitable": False,
            "search_intent": False,
            "search_keywords": [],
            "interaction_type": "unknown"
        }
        
        # 分析导航需求
        nav_url = self._detect_navigation_intent_and_url(user_text)
        if nav_url:
            analysis["needs_navigation"] = True
            analysis["target_url"] = nav_url
            
        # 分析当前页面是否适合
        current_url = page_data.get("url", "")
        if current_url and nav_url:
            # 检查是否已经在目标站点
            nav_domain = nav_url.replace("https://", "").replace("http://", "").split("/")[0]
            if nav_domain in current_url:
                analysis["current_page_suitable"] = True
                analysis["needs_navigation"] = False
        
        # 分析搜索意图
        if self._intent_is_search(user_text):
            analysis["search_intent"] = True
            analysis["search_keywords"] = [self._extract_search_keywords(user_text)]
            analysis["interaction_type"] = "search"
        
        # 分析交互类型
        if "点击" in user_text or "click" in user_text.lower():
            analysis["interaction_type"] = "click"
        elif "输入" in user_text or "fill" in user_text.lower() or "填写" in user_text:
            analysis["interaction_type"] = "fill"
        elif "截图" in user_text or "screenshot" in user_text.lower():
            analysis["interaction_type"] = "screenshot"
            
        return analysis

    def _build_enhanced_prompt(self, user_text: str, page_data: Dict[str, Any],
                              conversation_history: List[Dict[str, str]], 
                              context_analysis: Dict[str, Any]) -> str:
        """构建增强的提示词，一次性生成完整流程"""
        
        system_prompt = """
        你是一个高级的网页自动化助手，擅长在单次对话中生成完整的操作流程。
        
        你的核心优势：
        1. 智能上下文理解：能够分析用户意图和页面状态
        2. 一次性完整规划：生成从导航到最终操作的完整步骤
        3. 最优路径选择：选择最高效的执行路径
        
        重要原则：
        - 必须考虑完整的用户旅程，不要分阶段返回
        - 如果需要导航，必须包含导航后的后续操作
        - 先分析当前页面状态，再确定是否需要导航
        - 生成的指令应能一次性完成用户的完整需求
        
        输出格式：严格按照JSON格式，优先使用多步骤指令：
        ```json
        {
            "steps": [
                {
                    "action": "操作类型",
                    "selector": "元素选择器",
                    "value": "输入值",
                    "description": "操作描述"
                }
            ],
            "description": "整体操作描述"
        }
        ```
        
        支持的操作类型：
        - navigate: 导航到指定URL
        - wait: 等待页面加载或元素出现
        - click: 点击元素
        - fill: 在输入框中输入文本
        - select: 在下拉菜单中选择选项
        - screenshot: 截取屏幕截图
        - extract: 提取页面内容
        - scroll: 滚动页面
        
        选择器生成原则：
        1. 优先使用稳定的唯一标识符（ID、name、data-*属性）
        2. 其次使用语义和内容选择器（has-text、aria-label）
        3. 确保每个选择器都尽可能匹配唯一元素
        4. 避免脆弱的选择器（位置选择器、过于宽泛的类选择器）
        """
        
        # 根据上下文分析构建特定提示
        context_info = ""
        if context_analysis.get("needs_navigation") and context_analysis.get("target_url"):
            context_info += f"""
上下文分析：
- 需要导航到: {context_analysis['target_url']}
- 当前页面是否适合: {context_analysis.get('current_page_suitable', False)}
请生成包含导航和后续操作的完整流程。
            """
        
        if context_analysis.get("search_intent"):
            keywords = ", ".join(context_analysis.get("search_keywords", []))
            context_info += f"""
搜索意图识别: 用户想要搜索 "{keywords}"
请生成包含导航、找到搜索框、输入关键词、触发搜索的完整流程。
            """
        
        interaction_type = context_analysis.get("interaction_type", "unknown")
        if interaction_type != "unknown":
            context_info += f"""
交互类型: {interaction_type}
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
        
        {context_info}
        
        用户指令: {user_text}
        
        请根据用户指令和页面信息，生成一次性完成所有操作的多步骤JSON指令。
        注意：必须包含从开始到结束的完整流程，不要遗漏任何步骤。
        """

        if conversation_history:
            conversation_context = "\n对话历史:\n"
            for message in conversation_history[-4:]:
                role = "用户" if message["role"] == "user" else "助手"
                conversation_context += f"{role}: {message['content']}\n"
            user_prompt = conversation_context + "\n" + user_prompt

        return system_prompt + "\n\n" + user_prompt

    def _build_prompt(self, user_text: str, page_data: Dict[str, Any],
                      conversation_history: List[Dict[str, str]]) -> str:
        """构建LLM提示词"""
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
            "value": "输入值",  // 可选字段，取决于操作类型（navigate使用此字段传递URL）
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
        
        选择器生成原则（按优先级排序）：
        1. **优先使用稳定的唯一标识符**：
           - ID选择器：#submit-button, #search-input
           - name属性：input[name='username'], form[name='loginForm']
           - data-*属性：[data-testid='login-btn'], [data-action='submit']
        
        2. **基于语义和内容的选择器**：
           - 精确文本内容：a:has-text('登录'), button:has-text('搜索')
           - aria-label：[aria-label='搜索'], [aria-label='关闭']
           - 语义标签：button, input[type='submit'], nav
        
        3. **属性部分匹配**：
           - href部分匹配：a[href*='login'], a[href*='/tech']
           - class部分匹配：[class*='btn'], [class*='search']
           - placeholder匹配：[placeholder*='用户名']
        
        4. **提供多重备选策略时要确保精确性**：
           - 使用逗号分隔的多个选择器："a:has-text('科技'), a[href*='/tech/'], [data-nav='tech']"
           - 确保每个备选选择器都足够具体，避免匹配多个元素
           - 如果文本选择器可能匹配多个元素，要结合其他属性提高精确性
        
        5. **避免脆弱的选择器**：
           - 避免纯位置选择器：:nth-child(), :nth-of-type()
           - 避免深层嵌套：body > div > section > nav > ul > li > a
           - 避免过于宽泛的类选择器：.nav-link（会匹配多个元素）
           - 避免不完整的属性匹配：[class*='nav']（太宽泛）
        
        **重要：确保选择器精确性**
        - 每个选择器都应该尽可能匹配唯一元素
        - 当使用has-text()时，确保文本内容具有唯一性
        - 备选选择器应该同样精确，不要为了容错而牺牲精确性
        - 如果元素确实需要组合定位，优先使用语义属性组合
        
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
        
        用户指令: {user_text}
        
        请根据用户指令和页面信息，生成标准化的JSON格式指令。
        """

        if conversation_history:
            conversation_context = "\n对话历史:\n"
            for message in conversation_history[-4:]:
                role = "用户" if message["role"] == "user" else "助手"
                conversation_context += f"{role}: {message['content']}\n"
            user_prompt = conversation_context + "\n" + user_prompt

        return system_prompt + "\n\n" + user_prompt

    def _detect_navigation_intent_and_url(self, user_text: str) -> Optional[str]:
        """识别导航意图并提取规范化 URL。
        规则：优先匹配显式 http/https；否则匹配裸域（ASCII 顶级域），忽略周边中文词缀（如“访问”“网站”）。
        """
        # 1) 显式 URL（http/https）
        m = re.search(r"https?://[A-Za-z0-9.-]+(?:\.[A-Za-z]{2,24})(?:/[^\s]*)?", user_text)
        if m:
            return m.group(0)
        
        # 2) 中文网站名称到URL的映射
        chinese_site_mapping = {
            "百度": "https://www.baidu.com",
            "谷歌": "https://www.google.com",
            "google": "https://www.google.com",
            "bing": "https://www.bing.com",
            "必应": "https://www.bing.com",
            "小红书": "https://www.xiaohongshu.com",
            "知乎": "https://www.zhihu.com",
            "微博": "https://www.weibo.com",
            "淘宝": "https://www.taobao.com",
            "京东": "https://www.jd.com"
        }
        
        for site_name, url in chinese_site_mapping.items():
            if site_name in user_text.lower():
                return url
        
        # 3) 裸域（仅ASCII域名与TLD），避免把中文词缀合入
        m2 = re.search(r"(?<![A-Za-z0-9.-])([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24})(?![A-Za-z0-9.-])",
                       user_text)
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

    def _maybe_build_navigation_first(self, user_text: str) -> Optional[Dict[str, Any]]:
        """在页面为空时，尝试仅生成导航步骤（URL 直达）。"""
        url = self._detect_navigation_intent_and_url(user_text)
        if not url:
            return None
        # Note: URL validation removed - no domain filtering
        return {
            "steps": [
                {"action": "navigate", "value": url, "description": f"导航到 {url}"},
                {"action": "wait", "value": 2000, "description": "等待页面就绪(2秒)"}
            ],
            "description": f"前置导航到 {url} 并等待页面加载"
        }

    def _build_bing_pre_search(self, user_text: str) -> Dict[str, Any]:
        """当无法直达 URL 时，先在 Bing 搜索预检索站点/意图。"""
        from urllib.parse import quote_plus
        query = quote_plus(user_text.strip())
        url = f"https://www.bing.com/search?q={query}"
        # Note: URL validation removed - no domain filtering
        return {
            "steps": [
                {"action": "navigate", "value": url, "description": f"在Bing搜索：{user_text}"},
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

    def _maybe_build_known_site_action(self, user_text: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """在已知站点（如百度/Bing/Google）上生成搜索动作的启发式步骤。"""
        try:
            if not self._intent_is_search(user_text):
                return None
            url = (page_data or {}).get("url") or ""
            host = ""
            if url:
                m = re.search(r"://([^/]+)/?", url)
                if m:
                    host = m.group(1).lower()
            if not host:
                return None
            query = self._extract_query_from_instruction(user_text)
            steps: List[Dict[str, Any]] = []
            # 百度 - 使用精确的选择器策略
            if "baidu.com" in host:
                steps = [
                    {"action": "wait", "selector": "input[name='wd'], #kw", "timeout": 5000, "description": "等待百度搜索框出现"},
                    {"action": "fill", "selector": "input[name='wd'], #kw", "value": query, "description": f"在百度搜索框输入 '{query}'"},
                    {"action": "click", "selector": "input[value='百度一下'], #su", "description": "点击百度搜索按钮"}
                ]
            # Bing - 使用精确的选择器策略
            elif "bing.com" in host:
                steps = [
                    {"action": "wait", "selector": "input[name='q'], #sb_form_q", "timeout": 5000, "description": "等待Bing搜索框出现"},
                    {"action": "fill", "selector": "input[name='q'], #sb_form_q", "value": query, "description": f"在Bing搜索框输入 '{query}'"},
                    {"action": "click", "selector": "#sb_form_go, input[type='submit'][value='搜索']", "description": "点击Bing搜索按钮"}
                ]
            # Google - 使用精确的选择器策略
            elif "google." in host:
                steps = [
                    {"action": "wait", "selector": "textarea[name='q'], input[name='q']", "timeout": 5000, "description": "等待Google搜索框出现"},
                    {"action": "fill", "selector": "textarea[name='q'], input[name='q']", "value": query, "description": f"在Google搜索框输入 '{query}'"},
                    {"action": "click", "selector": "input[name='btnK'], input[value='Google 搜索']", "description": "点击Google搜索按钮"}
                ]
            else:
                return None
            return {"steps": steps, "description": f"站内搜索: {query}"}
        except Exception:
            return None

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用LLM生成指令，带有智能降级策略"""
        if not self.api_key:
            self.logger.warning("GEMINI_API_KEY 未配置，使用内置启发式")
            return self._fallback_instruction_generation(prompt)
            
        if genai is None:
            self.logger.warning("Gemini SDK 未安装，使用内置启发式")
            return self._fallback_instruction_generation(prompt)
            
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
                self.logger.warning("LLM返回无效JSON，使用启发式降级")
                return self._fallback_instruction_generation(prompt)
        except Exception as e:
            self.logger.error(f"调用Gemini失败: {e}，使用启发式降级")
            return self._fallback_instruction_generation(prompt)
    
    def _fallback_instruction_generation(self, prompt: str) -> Dict[str, Any]:
        """当LLM不可用时的启发式指令生成"""
        # 从prompt中提取用户指令
        user_instruction_match = re.search(r"用户指令: (.+)", prompt)
        if not user_instruction_match:
            return {"action": "error", "error": "无法解析用户指令"}
            
        user_instruction = user_instruction_match.group(1).strip()
        self.logger.info(f"启发式处理指令: {user_instruction}")
        
        # 搜索意图检测和关键词提取
        if self._intent_is_search(user_instruction):
            # 更智能的搜索关键词提取
            search_keywords = self._extract_search_keywords(user_instruction)
            
            # 检测是否在百度页面
            if "百度" in prompt or "baidu.com" in prompt:
                return {
                    "steps": [
                        {"action": "wait", "selector": "#kw", "timeout": 3000, "description": "等待百度搜索框加载"},
                        {"action": "fill", "selector": "#kw", "value": search_keywords, "description": f"在搜索框输入'{search_keywords}'"},
                        {"action": "click", "selector": "#su", "description": "点击搜索按钮"}
                    ],
                    "description": f"在百度搜索: {search_keywords}"
                }
        
        # 导航意图检测
        url = self._detect_navigation_intent_and_url(user_instruction)
        if url:
            return {
                "steps": [
                    {"action": "navigate", "value": url, "description": f"导航到 {url}"},
                    {"action": "wait", "value": 3000, "description": "等待页面加载"}
                ],
                "description": f"访问网站: {url}"
            }
        
        # 基础操作检测
        return self._detect_basic_action(user_instruction)
    
    def _extract_search_keywords(self, instruction: str) -> str:
        """更智能地提取搜索关键词"""
        # 常见搜索模式
        patterns = [
            r"搜索[\s'\"]*([^'\"，。]+)",
            r"查找[\s'\"]*([^'\"，。]+)",
            r"在.+?搜索[\s'\"]*([^'\"，。]+)",
            r"输入[\s'\"]*([^'\"，。]+)[\s'\"]*并.*?搜索",
            r"'([^']+)'",
            r'"([^"]+)"',
            r"([^，。！？；：]+(?:秋天|春天|夏天|冬天))",
            r"(小红书|北京|上海|广州|深圳)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction)
            if match:
                keyword = match.group(1).strip()
                if len(keyword) > 1:  # 过滤太短的关键词
                    return keyword
        
        # 如果没有匹配到特定模式，尝试提取核心词汇
        # 移除常见的动词和介词
        cleaned = re.sub(r"(打开|访问|进入|搜索|查找|点击|输入|在|上|的|并|然后|请|帮我)", "", instruction)
        cleaned = cleaned.strip()
        
        if cleaned:
            return cleaned
        
        return instruction.strip()
    
    def _detect_basic_action(self, instruction: str) -> Dict[str, Any]:
        """检测基础操作"""
        instruction_lower = instruction.lower()
        
        # 截图
        if any(word in instruction_lower for word in ["截图", "screenshot", "截取"]):
            return {"action": "screenshot", "description": "截取页面截图"}
        
        # 返回
        if any(word in instruction_lower for word in ["返回", "back", "上一页"]):
            return {"action": "back", "description": "返回上一页"}
        
        # 刷新
        if any(word in instruction_lower for word in ["刷新", "refresh", "重新加载"]):
            return {"action": "refresh", "description": "刷新页面"}
        
        # 点击 - 使用更稳定的多重选择器
        if any(word in instruction_lower for word in ["点击", "click"]):
            return {
                "action": "click",
                "selector": "button:first, a:first, [role='button']:first",
                "description": "点击页面元素"
            }
        
        # 默认等待
        return {
            "action": "wait",
            "value": 2000,
            "description": "等待页面响应"
        }

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
                # Note: URL validation removed - no domain filtering
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
            # Note: URL validation removed - no domain filtering
        return instruction


