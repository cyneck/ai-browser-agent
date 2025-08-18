#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
指令构建器

负责将用户的自然语言指令转换为标准化的JSON格式指令，供执行层执行。
"""

import json
import os
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
        """构建标准化的JSON格式指令
        
        Args:
            user_instruction: 用户的自然语言指令
            page_data: 页面意图图谱
            session_state: 会话状态
            
        Returns:
            Dict[str, Any]: 标准化的JSON格式指令
        """
        try:
            self.logger.info(f"构建指令: {user_instruction}")
            
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
        """构建提示词
        
        Args:
            user_instruction: 用户的自然语言指令
            page_data: 页面意图图谱
            conversation_history: 对话历史
            
        Returns:
            str: 提示词
        """
        # 构建系统提示词
        system_prompt = """
        你是一个专业的网页自动化助手，负责将用户的自然语言指令转换为标准化的JSON格式指令。
        
        你的任务是：
        1. 理解用户的意图
        2. 分析当前页面的结构和内容
        3. 生成一个或多个操作步骤，以完成用户的指令
        
        你必须严格按照以下JSON格式输出指令：
        ```json
        {
            "action": "操作类型",  // 必需字段，如navigate, click, type, select等
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
        - navigate: 导航到指定URL
        - click: 点击元素
        - type: 在输入框中输入文本
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
        
        请确保你的输出是有效的JSON格式，并且包含所有必需的字段。
        """
        
        # 构建用户提示词
        user_prompt = f"""
        当前页面信息：
        URL: {page_data.get('url', 'N/A')}
        标题: {page_data.get('title', 'N/A')}
        页面类型: {page_data.get('page_type', 'unknown')}
        
        页面上的可交互元素：
        {json.dumps(page_data.get('elements', []), ensure_ascii=False, indent=2)}
        
        页面上的功能区域：
        {json.dumps(page_data.get('functional_areas', []), ensure_ascii=False, indent=2)}
        
        用户指令: {user_instruction}
        
        请根据用户指令和页面信息，生成标准化的JSON格式指令。
        """
        
        # 如果有对话历史，添加到提示词中
        if conversation_history:
            conversation_context = "\n对话历史:\n"
            for message in conversation_history[-4:]:  # 只使用最近的4条消息
                role = "用户" if message["role"] == "user" else "助手"
                conversation_context += f"{role}: {message['content']}\n"
            user_prompt = conversation_context + "\n" + user_prompt
        
        # Gemini 使用纯文本提示，将系统提示与用户上下文拼接
        return system_prompt + "\n\n" + user_prompt
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用LLM生成指令
        
        Args:
            prompt: 提示词
            
        Returns:
            Dict[str, Any]: 生成的JSON格式指令
        """
        # 如果未配置API Key，降级为内置规则响应
        if not self.api_key:
            self.logger.warning("GEMINI_API_KEY 未配置，使用模拟响应")
            return self._mock_response(prompt)

        try:
            if genai is None:
                raise RuntimeError("Gemini SDK 未安装")
            genai.configure(api_key=self.api_key)
            model_name = get_config("GEMINI_MODEL", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt)
            text = getattr(resp, "text", "") or ""
            # 期望模型直接输出 JSON；若非 JSON，回退到错误
            try:
                return json.loads(text)
            except Exception:
                return {"action": "error", "error": "LLM未返回有效JSON", "raw": text[:500]}
        except Exception as e:
            self.logger.error(f"调用Gemini失败: {e}")
            return {"action": "error", "error": str(e)}

    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        # 模拟响应
        if "登录" in prompt or "login" in prompt.lower():
            return {
                "steps": [
                    {
                        "action": "type",
                        "selector": "input[name=username]",
                        "value": "{{ask_user('请输入用户名')}}",
                        "description": "在用户名输入框中输入用户名"
                    },
                    {
                        "action": "type",
                        "selector": "input[name=password]",
                        "value": "{{ask_user('请输入密码', password=True)}}",
                        "description": "在密码输入框中输入密码"
                    },
                    {
                        "action": "click",
                        "selector": "button[type=submit]",
                        "description": "点击登录按钮"
                    }
                ],
                "description": "完成登录流程"
            }
        elif "搜索" in prompt or "search" in prompt.lower():
            return {
                "steps": [
                    {
                        "action": "type",
                        "selector": "input[type=search]",
                        "value": "{{extract_search_query(instruction)}}",
                        "description": "在搜索框中输入搜索关键词"
                    },
                    {
                        "action": "click",
                        "selector": "button[type=submit]",
                        "description": "点击搜索按钮"
                    }
                ],
                "description": "执行搜索操作"
            }
        elif "导航" in prompt or "navigate" in prompt.lower() or "打开" in prompt or "访问" in prompt:
            url = "https://example.com"
            if "京东" in prompt or "jd" in prompt.lower():
                url = "https://www.jd.com"
            elif "淘宝" in prompt or "taobao" in prompt.lower():
                url = "https://www.taobao.com"
            
            return {
                "action": "navigate",
                "value": url,
                "description": f"导航到{url}"
            }
        else:
            return {
                "action": "error",
                "error": "无法理解用户指令",
                "description": "请提供更明确的指令"
            }
    
    def _validate_instruction(self, instruction: Dict[str, Any], 
                             page_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证指令格式和安全性
        
        Args:
            instruction: 生成的JSON格式指令
            page_data: 页面意图图谱
            
        Returns:
            Dict[str, Any]: 验证后的指令
        """
        # 验证指令格式
        if "action" not in instruction and "steps" not in instruction:
            raise ValueError("指令缺少必需的'action'或'steps'字段")
        
        # 如果是多步操作，验证每一步
        if "steps" in instruction:
            for i, step in enumerate(instruction["steps"]):
                if "action" not in step:
                    raise ValueError(f"第{i+1}步操作缺少必需的'action'字段")
                
                # 验证操作类型
                if step["action"] not in [
                    "navigate", "click", "type", "select", "wait", 
                    "screenshot", "extract", "scroll", "back", 
                    "forward", "refresh", "close", "error"
                ]:
                    raise ValueError(f"第{i+1}步操作的类型'{step['action']}'不受支持")
                
                # 验证必需的字段
                if step["action"] == "navigate" and "value" not in step:
                    raise ValueError(f"第{i+1}步'navigate'操作缺少必需的'value'字段")
                
                if step["action"] in ["click", "type", "select"] and "selector" not in step:
                    raise ValueError(f"第{i+1}步'{step['action']}'操作缺少必需的'selector'字段")
                
                if step["action"] in ["type", "select"] and "value" not in step:
                    raise ValueError(f"第{i+1}步'{step['action']}'操作缺少必需的'value'字段")
                
                # 验证URL安全性
                if step["action"] == "navigate":
                    self._validate_url_safety(step["value"])
        else:
            # 单步操作
            # 验证操作类型
            if instruction["action"] not in [
                "navigate", "click", "type", "select", "wait", 
                "screenshot", "extract", "scroll", "back", 
                "forward", "refresh", "close", "error"
            ]:
                raise ValueError(f"操作类型'{instruction['action']}'不受支持")
            
            # 验证必需的字段
            if instruction["action"] == "navigate" and "value" not in instruction:
                raise ValueError("'navigate'操作缺少必需的'value'字段")
            
            if instruction["action"] in ["click", "type", "select"] and "selector" not in instruction:
                raise ValueError(f"'{instruction['action']}'操作缺少必需的'selector'字段")
            
            if instruction["action"] in ["type", "select"] and "value" not in instruction:
                raise ValueError(f"'{instruction['action']}'操作缺少必需的'value'字段")
            
            # 验证URL安全性
            if instruction["action"] == "navigate":
                self._validate_url_safety(instruction["value"])
        
        return instruction
    
    def _validate_url_safety(self, url: str):
        """验证URL安全性
        
        Args:
            url: 要验证的URL
            
        Raises:
            ValueError: 如果URL不安全
        """
        # 如果允许所有域名，直接返回
        if self.allowed_domains == "*":
            return
        
        # 检查URL是否在允许的域名列表中
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # 提取主域名
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            main_domain = '.'.join(domain_parts[-2:])
        else:
            main_domain = domain
        
        # 检查域名是否在允许列表中
        if main_domain not in self.allowed_domains:
            raise ValueError(f"域名'{main_domain}'不在允许的域名列表中")