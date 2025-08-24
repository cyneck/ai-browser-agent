#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User Prompts

Contains templates and logic for building user prompts that include page context,
user instructions, and conversation history.
"""

import json
from typing import Dict, Any, List, Optional


class UserPrompts:
    """Container for user prompt templates and generation logic"""
    
    def __init__(self):
        """Initialize user prompts"""
        pass
    
    def build_basic_user_prompt(self, user_text: str, page_data: Dict[str, Any]) -> str:
        """Build a basic user prompt with page data
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            
        Returns:
            User prompt string
        """
        return f"""
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
    
    def build_enhanced_user_prompt(self, user_text: str, page_data: Dict[str, Any],
                                  context_analysis: Dict[str, Any]) -> str:
        """Build an enhanced user prompt with context analysis
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            context_analysis: Analysis of user context and intent
            
        Returns:
            Enhanced user prompt string
        """
        # Build context information based on analysis
        context_info = self._build_context_info(context_analysis)
        
        return f"""
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
    
    def add_conversation_history(self, base_prompt: str, 
                               conversation_history: List[Dict[str, str]]) -> str:
        """Add conversation history to a base prompt
        
        Args:
            base_prompt: The base user prompt
            conversation_history: Previous conversation messages
            
        Returns:
            Prompt with conversation history prepended
        """
        if not conversation_history:
            return base_prompt
        
        conversation_context = "\n对话历史:\n"
        for message in conversation_history[-4:]:  # Only keep last 4 messages
            role = "用户" if message["role"] == "user" else "助手"
            conversation_context += f"{role}: {message['content']}\n"
        
        return conversation_context + "\n" + base_prompt
    
    def _build_context_info(self, context_analysis: Dict[str, Any]) -> str:
        """Build context information string from analysis
        
        Args:
            context_analysis: Analysis of user context and intent
            
        Returns:
            Context information string
        """
        context_info = ""
        
        # Navigation context
        if context_analysis.get("needs_navigation") and context_analysis.get("target_url"):
            context_info += f"""
上下文分析：
- 需要导航到: {context_analysis['target_url']}
- 当前页面是否适合: {context_analysis.get('current_page_suitable', False)}
请生成包含导航和后续操作的完整流程。
            """
        
        # Search context
        if context_analysis.get("search_intent"):
            keywords = ", ".join(context_analysis.get("search_keywords", []))
            context_info += f"""
搜索意图识别: 用户想要搜索 "{keywords}"
请生成包含导航、找到搜索框、输入关键词、触发搜索的完整流程。
            """
        
        # Interaction type context
        interaction_type = context_analysis.get("interaction_type", "unknown")
        if interaction_type != "unknown":
            context_info += f"""
交互类型: {interaction_type}
            """
        
        return context_info
    
    def get_page_data_template(self) -> str:
        """Get the standard template for page data presentation
        
        Returns:
            Template string for page data
        """
        return """
        当前页面信息：
        URL: {url}
        标题: {title}
        页面类型: {page_type}
        
        页面上的可交互元素：
        {elements}
        
        页面上的功能区域：
        {functional_areas}
        
        ARIA 概览（可选）：
        {aria_snapshot}
        """
    
    def format_page_data(self, page_data: Dict[str, Any]) -> Dict[str, str]:
        """Format page data for template usage
        
        Args:
            page_data: Raw page data dictionary
            
        Returns:
            Formatted page data for template substitution
        """
        return {
            "url": page_data.get('url', 'N/A'),
            "title": page_data.get('title', 'N/A'),
            "page_type": page_data.get('page_type', 'unknown'),
            "elements": json.dumps(page_data.get('elements', []), ensure_ascii=False, indent=2),
            "functional_areas": json.dumps(page_data.get('functional_areas', []), ensure_ascii=False, indent=2),
            "aria_snapshot": json.dumps(page_data.get('aria_snapshot') or {}, ensure_ascii=False)[:800]
        }
    
    def build_instruction_request(self, instruction_type: str = "standard") -> str:
        """Build the instruction request part of the prompt
        
        Args:
            instruction_type: Type of instruction request (standard, complete_workflow)
            
        Returns:
            Instruction request string
        """
        if instruction_type == "complete_workflow":
            return """
        请根据用户指令和页面信息，生成一次性完成所有操作的多步骤JSON指令。
        注意：必须包含从开始到结束的完整流程，不要遗漏任何步骤。
        """
        else:
            return """
        请根据用户指令和页面信息，生成标准化的JSON格式指令。
        """