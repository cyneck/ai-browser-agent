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

from src.models.instruction import (
    Instruction, SingleStepInstruction, MultiStepInstruction, 
    InstructionContext, ActionType, BaseAction, NavigateAction,
    ClickAction, FillAction, WaitAction, ExtractAction
)
from src.common.config import get_config
from src.common.logger import get_logger
from src.common.performance_monitor import get_performance_monitor
from src.common.llm_manager import get_llm_manager
from src.prompts.prompt_manager import PromptManager
from src.plugins.plugin_manager import PluginManager


class InstructionBuilder:
    """指令构建器类，负责将自然语言文本构建为标准化的指令"""

    def __init__(self):
        """初始化指令构建器"""
        self.logger = get_logger()
        self.prompt_manager = PromptManager()
        self.plugin_manager = PluginManager()
        self.llm_manager = get_llm_manager()

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
            
            # 提取对话历史
            conversation_history = session_state.get("conversation_history", [])
            
            # 先尝试简单启发式规则（避免不必要的LLM调用）
            simple_action = self._try_simple_heuristics(user_text, page_data)
            if simple_action:
                self.logger.info("使用简单启发式规则，无需LLM")
                return simple_action
            
            # 检查是否有可用的LLM提供商
            available_providers = self.llm_manager.get_available_providers()
            if not available_providers:
                self.logger.warning("没有可用的LLM提供商，返回错误指令")
                return {
                    "action": "error",
                    "error": "没有配置LLM提供商",
                    "original_text": user_text
                }
            
            # 使用LLM生成指令
            self.logger.debug("使用LLM生成指令")
            context_analysis = self._analyze_context(user_text, page_data, conversation_history)
            
            # 尝试使用增强提示词，如果不可用则使用普通提示词
            try:
                prompt = self.prompt_manager.build_enhanced_prompt(
                    user_text, page_data, conversation_history, context_analysis
                )
            except AttributeError:
                prompt = self.prompt_manager.build_complete_prompt(
                    user_text, page_data, conversation_history
                )
            
            json_instruction = self._call_llm(prompt, user_text)
            validated_instruction = self._validate_instruction(json_instruction, page_data)
            
            # 更新对话历史
            self._update_conversation_history(conversation_history, user_text, validated_instruction)
            session_state["conversation_history"] = conversation_history
            
            self.logger.info("指令构建完成")
            return validated_instruction
            
        except Exception as e:
            self.logger.error(f"构建指令时发生错误: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "original_text": user_text
            }

    def build_optimized(self, user_text: str, page_data: Dict[str, Any], 
                       session_state: Dict[str, Any]) -> Dict[str, Any]:
        """优化版本：与build()方法相同，保持向后兼容"""
        return self.build(user_text, page_data, session_state)
    
    def _update_conversation_history(self, conversation_history: List[Dict[str, str]], 
                                    user_text: str, instruction: Dict[str, Any]):
        """更新对话历史"""
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": json.dumps(instruction)})
        # 限制对话历史长度
        if len(conversation_history) > 10:
            conversation_history[:] = conversation_history[-10:]

    def _try_simple_heuristics(self, user_text: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """尝试简单的启发式规则，避免不必要的LLM调用"""
        # 1. 当前页面查询
        if self._is_current_page_query(user_text):
            return {"action": "extract_results", "extraction_type": "auto", "description": "提取当前页面信息"}
        
        # 2. 导航意图
        nav_url = self._detect_navigation_intent_and_url(user_text)
        if nav_url:
            # 尝试插件回退策略（除非是小红书且设置了直接访问）
            is_xiaohongshu = "xiaohongshu.com" in nav_url
            direct_access = get_config("XIAOHONGSHU_DIRECT_ACCESS", "false").lower() == "true"
            if not (is_xiaohongshu and direct_access):
                fallback = self.plugin_manager.build_instruction_with_fallback(user_text, nav_url)
                if fallback:
                    return fallback
            return {"action": "navigate", "value": nav_url, "description": f"导航到 {nav_url}"}
        
        # 3. 搜索意图（页面为空时）
        is_search = self._intent_is_search(user_text)
        is_page_empty = not page_data or not page_data.get("is_valid", True)
        if is_search and is_page_empty:
            return self._build_search_instruction(user_text)
        
        # 4. 已知站点的操作
        if page_data and page_data.get("is_valid"):
            return self._maybe_build_known_site_action(user_text, page_data)
        
        return None
    
    def _build_search_instruction(self, user_text: str) -> Dict[str, Any]:
        """构建搜索引擎搜索指令"""
        from src.common.search_engines import get_primary_search_engine
        search_keywords = self._extract_search_keywords(user_text)
        primary_engine = get_primary_search_engine()
        
        steps = [
            {"action": "navigate", "value": primary_engine["url"], "description": f"导航到{primary_engine['display_name']}首页"},
            {"action": "wait", "value": 2000, "description": "等待页面加载(2秒)"},
            {"action": "wait", "selector": primary_engine["search_box_selector"], "timeout": 5000, "description": f"等待{primary_engine['display_name']}搜索框加载"},
            {"action": "fill", "selector": primary_engine["search_box_selector"], "value": search_keywords, "description": f"在搜索框输入'{search_keywords}'"},
        ]
        
        # 添加提交步骤
        if primary_engine["submit_method"] == "enter_key":
            steps.append({"action": "key", "selector": primary_engine["search_box_selector"], "value": "Enter", "description": "按回车键执行搜索"})
        else:
            steps.append({"action": "click", "selector": "#su", "description": f"点击{primary_engine['display_name']}搜索按钮"})
        
        steps.extend([
            {"action": "wait", "value": 3000, "description": "等待搜索结果加载"},
            {"action": "extract_results", "extraction_type": "auto", "description": "提取搜索结果"}
        ])
        
        return {"steps": steps, "description": f"在{primary_engine['display_name']}上搜索: {search_keywords}"}

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
            
            # 分析当前页面是否为搜索引擎页面
            if current_url:
                website_plugin = self.plugin_manager.get_website_plugin(current_url)
                if website_plugin:
                    analysis["current_page_is_search_engine"] = True
                    analysis["search_engine_name"] = website_plugin.__class__.__name__.replace("Plugin", "")
                    analysis["can_search_on_current_page"] = True
                else:
                    analysis["current_page_is_search_engine"] = False
        
        # 分析交互类型
        if "点击" in user_text or "click" in user_text.lower():
            analysis["interaction_type"] = "click"
        elif "输入" in user_text or "fill" in user_text.lower() or "填写" in user_text:
            analysis["interaction_type"] = "fill"
        elif "截图" in user_text or "screenshot" in user_text.lower():
            analysis["interaction_type"] = "screenshot"
            
        return analysis

    def _is_current_page_query(self, user_text: str) -> bool:
        """检查是否是询问当前页面的查询"""
        current_page_patterns = [
            r"当前页面.*?(是|什么)",
            r"现在.*?页面.*?(是|什么)",
            r"这个页面.*?(是|什么)",
            r"what.*?page.*?is",
            r"what.*?is.*?page",
            r"当前.*?网页.*?(是|什么)"
        ]
        
        user_text_lower = user_text.lower()
        return any(re.search(pattern, user_text_lower) for pattern in current_page_patterns)

    def _detect_navigation_intent_and_url(self, user_text: str) -> Optional[str]:
        """识别导航意图并提取规范化 URL。
        规则：优先匹配显式 http/https；否则匹配裸域（ASCII 顶级域），忽略周边中文词缀（如“访问”“网站”）。
        """
        # 1) 显式 URL（http/https）
        m = re.search(r"https?://[A-Za-z0-9.-]+(?:\.[A-Za-z]{2,24})(?:/[^\s]*)?", user_text)
        if m:
            return m.group(0)
        
        # 2) 中文网站名称到URL的映射 (通过插件管理器获取)
        chinese_site_mapping = self.plugin_manager.get_all_site_name_mappings()
        
        # 尝试精确匹配
        for site_name, url in chinese_site_mapping.items():
            if site_name == user_text.strip() or f"打开{site_name}" == user_text.strip() or f"访问{site_name}" == user_text.strip():
                return url
        
        # 尝试模糊匹配
        for site_name, url in chinese_site_mapping.items():
            if site_name in user_text:
                return url
        
        # 特殊处理常见的网站名称
        site_mappings = {
            "知乎": "https://www.zhihu.com",
            "微博": "https://weibo.com",
            "豆瓣": "https://www.douban.com",
            "GitHub": "https://github.com",
            "知乎网站": "https://www.zhihu.com"
        }
        
        for site_name, url in site_mappings.items():
            if site_name in user_text:
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


    def _intent_is_search(self, instruction: str) -> bool:
        return bool(re.search(r"(搜索|搜搜|查询|找|新闻|news|search|哪些|什么|怎么样|如何|情况|多少|现在|是什么|怎样|天气|日天)", instruction, re.IGNORECASE))

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
            if not url:
                return None
                
            host = ""
            m = re.search(r"://([^/]+)/?", url)
            if m:
                host = m.group(1).lower()
            if not host:
                return None
                
            self.logger.debug(f"尝试为站点 {host} 构建搜索动作")
            
            query = self._extract_query_from_instruction(user_text)
            
            # 尝试通过网站插件构建搜索动作
            website_plugin = self.plugin_manager.get_website_plugin(url)
            if website_plugin:
                self.logger.debug(f"找到网站插件: {website_plugin.__class__.__name__}")
                steps = website_plugin.build_search_action(query)
                if steps:
                    return {"steps": steps, "description": f"站内搜索: {query}"}
                else:
                    self.logger.debug(f"插件未返回有效步骤")
                    return None
            else:
                self.logger.debug(f"未找到适合的网站插件")
                return None
                
        except Exception as e:
            self.logger.error(f"在已知站点（如百度/Bing/Google）上生成搜索动作的启发式异常: {e}")
            return None

    def _call_llm(self, prompt: str, user_text: str = None) -> Dict[str, Any]:
        """调用LLM生成指令，带有智能降级策略
        
        Args:
            prompt: LLM提示词
            user_text: 用户原始文本，用于降级时的启发式生成
        """
        import time
        
        self.logger.debug("_call_llm: 开始调用 LLM")
        
        # 检查是否有可用的LLM提供商
        available_providers = self.llm_manager.get_available_providers()
        if not available_providers:
            self.logger.warning("没有配置任何LLM提供商，使用内置启发式")
            return self._fallback_instruction_generation(user_text or prompt)
            
        try:
            # 获取配置的LLM提供商和模型
            llm_provider = get_config("LLM_PROVIDER", "gemini")
            model_name = None  # 使用提供商的默认模型
            
            # 如果配置了特定模型，则使用
            if llm_provider == "gemini":
                model_name = get_config("GEMINI_MODEL")
            elif llm_provider == "openai":
                model_name = get_config("OPENAI_MODEL")
            elif llm_provider == "qwen":
                model_name = get_config("QWEN_MODEL")
            elif llm_provider == "ollama":
                model_name = get_config("OLLAMA_MODEL")
            
            self.logger.debug(f"_call_llm: 调用 {llm_provider} API")
            
            # 获取性能监控器
            perf_monitor = get_performance_monitor()
            start_time = time.time()
            prompt_tokens = int(len(prompt.split()) * 1.3)  # 粗略估算token数
            
            # 调用LLM
            result = self.llm_manager.call_llm(prompt, llm_provider, model_name)
            text = result.get("text", "")
            response_time = time.time() - start_time
            
            self.logger.debug(f"_call_llm: {llm_provider} API 返回成功，耗时 {response_time:.2f}秒")
            
            try:
                # 尝试从响应中提取JSON
                json_instruction = self.llm_manager.extract_json_from_response(text)
                
                completion_tokens = int(len(text.split()) * 1.3)
                perf_monitor.record_llm_call(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time=response_time,
                    model_name=f"{llm_provider}/{model_name or 'default'}",
                    success=True
                )
                
                return json_instruction
            except Exception as e:
                perf_monitor.record_llm_call(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    response_time=time.time() - start_time,
                    model_name=f"{llm_provider}/{model_name or 'default'}",
                    success=False,
                    error_message=str(e)
                )
                self.logger.warning(f"_call_llm: LLM返回无效JSON，使用启发式降级: {e}")
                return self._fallback_instruction_generation(user_text or prompt)
                
        except Exception as e:
            # 确保llm_provider已定义
            if 'llm_provider' not in locals():
                llm_provider = "unknown"
            self.logger.error(f"_call_llm: 调用{llm_provider}失败: {e}，使用启发式降级") 
            return self._fallback_instruction_generation(user_text or prompt)
    
    def _fallback_instruction_generation(self, user_input: str) -> Dict[str, Any]:
        """当LLM不可用时的启发式指令生成
        
        Args:
            user_input: 用户输入文本或prompt字符串
        """
        # 如果输入是字符串且包含"用户指令:"，尝试提取
        if isinstance(user_input, str) and "用户指令:" in user_input:
            user_instruction_match = re.search(r"用户指令: (.+)", user_input)
            if user_instruction_match:
                user_instruction = user_instruction_match.group(1).strip()
            else:
                user_instruction = user_input.strip()
        else:
            # 直接使用输入作为用户指令
            user_instruction = str(user_input).strip() if user_input else ""
        
        # 检查用户指令是否为空
        if not user_instruction:
            return {"action": "error", "error": "用户输入为空", "message": "用户输入为空"}
        
        self.logger.info(f"启发式处理指令: {user_instruction}")
        
        # 搜索意图检测和关键词提取
        if self._intent_is_search(user_instruction):
            # 更智能的搜索关键词提取
            search_keywords = self._extract_search_keywords(user_instruction)
            
            # 使用搜索引擎优先级配置进行通用搜索
            from src.common.search_engines import get_primary_search_engine
            primary_engine = get_primary_search_engine()
            
            # 构建搜索步骤
            steps = [
                {"action": "navigate", "value": primary_engine["url"], "description": f"导航到{primary_engine['display_name']}"},
                {"action": "wait", "value": 2000, "description": "等待页面加载(2秒)"},
                {"action": "wait", "selector": primary_engine["search_box_selector"], "timeout": 5000, "description": f"等待{primary_engine['display_name']}搜索框加载"},
                {"action": "fill", "selector": primary_engine["search_box_selector"], "value": search_keywords, "description": f"在搜索框输入'{search_keywords}'"},
            ]
            
            # 根据搜索引擎的推荐提交方式添加步骤
            if primary_engine["submit_method"] == "enter_key":
                steps.append({"action": "key", "selector": primary_engine["search_box_selector"], "value": "Enter", "description": "按回车键执行搜索"})
            else:
                # 百度使用点击按钮的方式
                steps.append({"action": "click", "selector": "#su", "description": f"点击{primary_engine['display_name']}搜索按钮"})
            
            steps.extend([
                {"action": "wait", "value": 3000, "description": "等待搜索结果加载"},
                {"action": "extract_results", "extraction_type": "auto", "description": "提取搜索结果"}
            ])
            
            return {
                "steps": steps,
                "description": f"在{primary_engine['display_name']}搜索: {search_keywords}"
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
        basic_action = self._detect_basic_action(user_instruction)
        # 如果基础操作是默认的wait，说明无法识别指令，返回错误
        if basic_action.get("action") == "wait" and basic_action.get("description") == "等待页面响应":
            return {"action": "error", "error": "无法解析用户指令", "original_text": user_instruction}
        
        return basic_action
    
    def _extract_search_keywords(self, instruction: str) -> str:
        """更智能地提取搜索关键词"""
        # 常见搜索模式
        patterns = [
            r"搜索[\s'\"]*([^'\"，。]+)",
            r"搜搜[\s'\"]*([^'\"，。]+)",
            r"查找[\s'\"]*([^'\"，。]+)", 
            r"查询[\s'\"]*([^'\"，。]+)",
            r"在.+?搜索[\s'\"]*([^'\"，。]+)",
            r"在.+?查找[\s'\"]*([^'\"，。]+)",
            r"在.+?查询[\s'\"]*([^'\"，。]+)",
            r"输入[\s'\"]*([^'\"，。]+)[\s'\"]*并.*?搜索",
            r"'([^']+)'",
            r'"([^"]+)"',
            r"([^，。！？；：]+(?:秋天|春天|夏天|冬天))",
            r"([^，。！？；：]+(?:附近|美食|推荐|打卡点|食谱))"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction)
            if match:
                keyword = match.group(1).strip()
                if len(keyword) > 1:  # 过滤太短的关键词
                    return keyword
        
        # 如果没有匹配到特定模式，尝试提取核心词汇
        # 智能移除常见的动词和介词，但保留核心内容
        # 移除常见的操作词汇，但保留具体的搜索内容
        action_words = r"(打开|访问|进入|搜索|搜搜|查找|查询|点击|输入|在|上|的|并|然后|请|帮我)"
        cleaned = re.sub(action_words, "", instruction)
        cleaned = cleaned.strip()
        
        if cleaned and len(cleaned) > 1:
            return cleaned
        
        # 如果清理后太短，返回原始指令
        return instruction.strip()

    def _build_xiaohongshu_fallback_strategy(self, user_text: str) -> Dict[str, Any]:
        """构建小红书的内置回退策略（当插件不可用时）"""
        # 提取搜索关键词
        keywords = self._extract_search_keywords(user_text)
        
        # 使用通用的搜索引擎回退策略构建器
        from src.common.search_engines import build_search_fallback_strategy
        strategies = build_search_fallback_strategy("xiaohongshu.com", keywords)
        
        # 返回第一个（优先级最高的）策略
        primary_strategy = strategies[0]
        return {
            "steps": primary_strategy["steps"],
            "description": primary_strategy["description"],
            "fallback_info": {
                "reason": "小红书可能存在网络访问限制（错误代码300012）",
                "strategy": primary_strategy["description"]
            }
        }
    
    def _detect_basic_action(self, instruction: str) -> Dict[str, Any]:
        """检测基础操作"""
        instruction_lower = instruction.lower()
        
        # 截图
        if any(word in instruction_lower for word in ["截图", "screenshot", "截取"]):
            return {"action": "screenshot", "description": "截取页面截图"}

        # 保存为mhtml (更具体的匹配应该放在"保存"之前)
        if any(word in instruction_lower for word in ["保存为html", "save as html", "保存为网页"]):
            return {"action": "save_as_mhtml", "description": "保存为html"}
            
        # 保存为pdf (更通用的匹配应该放在更具体匹配之后)
        if any(word in instruction_lower for word in ["保存为pdf", "save as pdf"]):
            return {"action": "save_as_pdf", "description": "保存为pdf"}
            
        # 通用保存操作 (最通用的匹配应该放在最后)
        if any(word in instruction_lower for word in ["保存"]):
            return {"action": "save_as_pdf", "description": "保存为pdf"}

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
                    "screenshot", "extract", "extract_results", "scroll", "back",
                    "forward", "refresh", "close", "error", "wait_for_login",
                    "smart_fill", "smart_submit", "key","save_as_pdf", "save_as_mhtml"
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
                "screenshot", "extract", "extract_results", "scroll", "back",
                "forward", "refresh", "close", "error", "wait_for_login",
                "smart_fill", "smart_submit", "key","save_as_pdf", "save_as_mhtml"
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