#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Response Generator

Generates appropriate responses based on user intent and extracted content.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

from src.models.response import (
    GeneratedResponse, ResponseFormat, ResponseStrategy, 
    ResponseStrategyType, SummaryResponse, StructuredResponse,
    DetailedResponse, FullPageResponse, ResponseContext
)
from src.reasoning.intent_classifier import IntentType, IntentResult
from src.reasoning.llm_extractor import LLMExtractor
from src.common.logger import get_logger
from src.common.llm_manager import get_llm_manager


class ResponseStrategy(ABC):
    """抽象基类：响应生成策略"""
    
    @abstractmethod
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """根据提取的数据和意图生成响应"""
        pass
    
    @abstractmethod
    def can_handle(self, intent_type: IntentType) -> bool:
        """检查此策略是否能处理给定的意图类型"""
        pass


class SummaryInfoStrategy(ResponseStrategy):
    """增强的摘要信息响应策略：使用LLM提取生成个性化简洁摘要"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
        self.llm_manager = get_llm_manager()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.SUMMARY_INFO
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """生成个性化简洁摘要响应"""
        
        self.logger.info(f"开始生成摘要信息响应，意图关键词: {intent_result.keywords}")
        
        # 获取原始查询和用户偏好
        original_query = context.original_query
        user_preferences = self._extract_user_preferences(context, intent_result)
        
        if not extracted_data:
            self.logger.warning("没有提取到数据")
            return SummaryResponse(
                content="抱歉，未能获取到相关信息。",
                format=ResponseFormat.NATURAL_LANGUAGE,
                metadata={},
                success=False,
                error="No data extracted"
            )
        
        self.logger.info(f"提取到的数据类型: {type(extracted_data)}")
        
        # 处理不同类型的数据
        if isinstance(extracted_data, list) and extracted_data:
            self.logger.info(f"处理列表数据，项目数量: {len(extracted_data)}")
            
            # 使用增强的LLM提取，支持个性化
            summary = self._generate_personalized_summary(
                extracted_data, original_query, user_preferences
            )
            
            self.logger.info(f"个性化摘要结果: {summary}")
            
            # 如果LLM提取失败，使用通用摘要
            if not summary:
                self.logger.info("个性化摘要失败，使用通用摘要")
                summary = self._extract_generic_summary(extracted_data)
                
        elif isinstance(extracted_data, dict):
            self.logger.info("处理字典数据")
            # 对于结构化数据，提取相关字段
            summary = self._extract_summary_from_structured_data(
                extracted_data, intent_result, user_preferences
            )
        else:
            self.logger.info("处理文本数据")
            # 对于文本内容，进行摘要
            summary = self._extract_summary_from_text(str(extracted_data), user_preferences)
        
        self.logger.info(f"最终摘要: {summary}")
        
        # 应用响应格式化
        formatted_summary = self._apply_response_formatting(summary, intent_result.response_format)
        
        return SummaryResponse(
            content=formatted_summary,
            format=ResponseFormat.NATURAL_LANGUAGE,
            metadata={
                "source_data_count": len(extracted_data) if isinstance(extracted_data, list) else 1,
                "personalization_applied": bool(user_preferences),
                "response_style": user_preferences.get("style", "standard")
            },
            success=True
        )
    
    def _extract_generic_summary(self, results: List[Dict]) -> str:
        """从搜索结果中提取通用摘要（主要降级方法）"""
        if not results:
            return "未找到相关信息。"
        
        # 使用第一个结果作为主要来源
        first_result = results[0]
        title = first_result.get("title", "")
        desc = first_result.get("description", "")
        
        if desc and len(desc) > 50:
            return desc[:200] + ("..." if len(desc) > 200 else "")
        elif title:
            return f"相关信息：{title}"
        else:
            return "找到相关结果，但无法提取摘要信息。"

    def _extract_summary_from_structured_data(self, data: Dict, 
                                            intent_result: IntentResult) -> str:
        """从结构化数据中提取摘要"""
        # 实现依赖于数据结构
        # 这是一个简化版本
        if "summary" in data:
            return data["summary"]
        elif "title" in data:
            return data["title"]
        else:
            return str(data)[:200] + "..."
    
    def _extract_summary_from_text(self, text: str, user_preferences: Dict[str, Any] = None) -> str:
        """从纯文本中提取摘要，支持个性化"""
        if user_preferences is None:
            user_preferences = {}
        
        # 根据用户偏好调整摘要长度
        max_length = user_preferences.get("summary_length", 200)
        if user_preferences.get("style") == "brief":
            max_length = 100
        elif user_preferences.get("style") == "detailed":
            max_length = 400
        
        # 简单文本摘要
        sentences = text.split("。")
        if len(sentences) > 1:
            summary = sentences[0] + "。"
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            return summary
        else:
            return text[:max_length] + ("..." if len(text) > max_length else "")
    
    def _extract_user_preferences(self, context: ResponseContext, intent_result: IntentResult) -> Dict[str, Any]:
        """从上下文中提取用户偏好"""
        preferences = {}
        
        # 从意图结果中提取偏好
        if intent_result.additional_params:
            preferences.update(intent_result.additional_params)
        
        # 从会话状态中提取用户偏好
        session_state = context.session_state
        if session_state:
            user_prefs = session_state.get("user_preferences", {})
            preferences.update(user_prefs)
        
        # 从关键词中推断偏好
        keywords = intent_result.keywords
        if any(word in keywords for word in ["简单", "简要", "brief"]):
            preferences["style"] = "brief"
        elif any(word in keywords for word in ["详细", "完整", "detailed"]):
            preferences["style"] = "detailed"
        
        # 从响应格式中推断偏好
        if intent_result.response_format == "table":
            preferences["prefer_structured"] = True
        elif intent_result.response_format == "natural_language":
            preferences["prefer_natural"] = True
        
        return preferences
    
    def _generate_personalized_summary(self, extracted_data: List[Dict], 
                                     original_query: str, 
                                     user_preferences: Dict[str, Any]) -> Optional[str]:
        """生成个性化摘要"""
        try:
            # 构建个性化提示词
            prompt = self._build_personalized_prompt(extracted_data, original_query, user_preferences)
            
            # 调用LLM生成个性化响应
            available_providers = self.llm_manager.get_available_providers()
            if not available_providers:
                return None
            
            provider = available_providers[0]  # 使用第一个可用提供商
            result = self.llm_manager.call_llm(prompt, provider)
            
            response_text = result.get("text", "").strip()
            
            # 尝试解析JSON响应
            if response_text.startswith("{") and response_text.endswith("}"):
                try:
                    import json
                    response_data = json.loads(response_text)
                    return response_data.get("personalized_summary", response_text)
                except json.JSONDecodeError:
                    pass
            
            return response_text if len(response_text) > 10 else None
            
        except Exception as e:
            self.logger.error(f"个性化摘要生成失败: {e}")
            return None
    
    def _build_personalized_prompt(self, extracted_data: List[Dict], 
                                  original_query: str, 
                                  user_preferences: Dict[str, Any]) -> str:
        """构建个性化提示词"""
        import json
        
        # 构建数据JSON
        data_json = json.dumps(extracted_data[:5], ensure_ascii=False, indent=2)
        
        # 构建偏好描述
        style = user_preferences.get("style", "standard")
        prefer_structured = user_preferences.get("prefer_structured", False)
        
        style_instructions = {
            "brief": "请用简洁的语言回答，控制在50字以内",
            "detailed": "请提供详细的回答，包含更多背景信息",
            "standard": "请用标准的语言回答，简洁明了"
        }
        
        style_instruction = style_instructions.get(style, style_instructions["standard"])
        
        prompt = f"""
你是一个智能助手，需要根据用户的查询和偏好生成个性化的回答。

用户查询: "{original_query}"
用户偏好: {style}
{'用户偏好结构化数据' if prefer_structured else '用户偏好自然语言'}

搜索结果:
{data_json}

请根据用户查询和偏好分析搜索结果，并生成个性化的回答。

要求：
1. {style_instruction}
2. 直接回答用户的问题，不要包含多余的解释
3. 根据用户偏好调整回答风格
4. 如果没有找到相关信息，请简洁地说明

请以JSON格式返回：
{{
  "personalized_summary": "个性化的回答内容"
}}
"""
        
        return prompt
    
    def _apply_response_formatting(self, content: str, response_format: str) -> str:
        """应用响应格式化"""
        if response_format == "markdown":
            # 简单的markdown格式化
            if "：" in content:
                parts = content.split("：", 1)
                return f"**{parts[0]}**：{parts[1]}"
        elif response_format == "json":
            # JSON格式化
            import json
            return json.dumps({"content": content}, ensure_ascii=False, indent=2)
        
        return content  # 默认返回原内容


class StructuredDataStrategy(ResponseStrategy):
    """增强的结构化数据响应策略：支持多格式和个性化结构化数据生成"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
        self.llm_manager = get_llm_manager()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.STRUCTURED_DATA
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """生成多格式结构化数据响应"""
        
        structure_type = intent_result.additional_params.get("structure_type", "auto")
        user_preferences = self._extract_user_preferences(context, intent_result)
        
        if isinstance(extracted_data, list):
            # 使用增强的LLM提取结构化数据
            structured_result = self._generate_enhanced_structured_data(
                extracted_data, structure_type, user_preferences, context
            )
            
            if structured_result and structured_result.get("structured_data"):
                structured_content = self._format_structured_data(
                    structured_result["structured_data"], structure_type, user_preferences
                )
                format_type = self._determine_format_type(structure_type, user_preferences)
            else:
                # 降级到原始格式化
                structured_content, format_type = self._fallback_formatting(
                    extracted_data, structure_type, user_preferences
                )
        else:
            structured_content = json.dumps(extracted_data, ensure_ascii=False, indent=2)
            format_type = ResponseFormat.JSON
        
        # 应用多格式支持
        final_content = self._apply_multi_format_support(
            structured_content, intent_result.response_format, user_preferences
        )
        
        return StructuredResponse(
            content=final_content,
            format=format_type,
            metadata={
                "item_count": len(extracted_data) if isinstance(extracted_data, list) else 1,
                "structure_type": structure_type,
                "personalization_applied": bool(user_preferences),
                "output_format": intent_result.response_format
            },
            success=True,
            structure_type=structure_type,
            structured_data=structured_result.get("structured_data", []) if 'structured_result' in locals() else []
        )
    
    def _format_structured_data(self, data: List[Dict], structure_type: str) -> str:
        """格式化LLM提取的结构化数据"""
        if structure_type == "table" or structure_type == "auto":
            return self._format_as_table(data)
        else:
            return self._format_as_list(data)
    
    def _format_as_table(self, data: List[Dict]) -> str:
        """将数据格式化为表格"""
        if not data:
            return "无数据"
        
        # 获取所有唯一键
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        if not all_keys:
            return str(data)
        
        # 创建表格
        headers = list(all_keys)
        table_lines = [" | ".join(headers)]
        table_lines.append(" | ".join(["---"] * len(headers)))
        
        for item in data:
            if isinstance(item, dict):
                row = [str(item.get(key, "")) for key in headers]
                table_lines.append(" | ".join(row))
        
        return "\n".join(table_lines)
    
    def _format_as_list(self, data: List) -> str:
        """将数据格式化为编号列表"""
        if not data:
            return "无数据"
        
        lines = []
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                title = item.get("title", item.get("name", f"项目{i}"))
                lines.append(f"{i}. {title}")
                if "description" in item:
                    lines.append(f"   {item['description'][:100]}...")
            else:
                lines.append(f"{i}. {str(item)}")
        
        return "\n".join(lines)
    
    def _extract_user_preferences(self, context: ResponseContext, intent_result: IntentResult) -> Dict[str, Any]:
        """从上下文中提取用户偏好"""
        preferences = {}
        
        # 从意图结果中提取偏好
        if intent_result.additional_params:
            preferences.update(intent_result.additional_params)
        
        # 从会话状态中提取用户偏好
        session_state = context.session_state
        if session_state:
            user_prefs = session_state.get("user_preferences", {})
            preferences.update(user_prefs)
        
        return preferences
    
    def _generate_enhanced_structured_data(self, extracted_data: List[Dict], 
                                          structure_type: str, 
                                          user_preferences: Dict[str, Any],
                                          context: ResponseContext) -> Optional[Dict[str, Any]]:
        """生成增强的结构化数据"""
        try:
            # 构建增强的结构化数据提取提示词
            prompt = self._build_enhanced_structured_prompt(
                extracted_data, structure_type, user_preferences, context
            )
            
            # 调用LLM生成结构化数据
            available_providers = self.llm_manager.get_available_providers()
            if not available_providers:
                return None
            
            provider = available_providers[0]
            result = self.llm_manager.call_llm(prompt, provider)
            
            response_text = result.get("text", "").strip()
            
            # 尝试解析JSON响应
            if response_text.startswith("{") and response_text.endswith("}"):
                try:
                    import json
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"增强结构化数据生成失败: {e}")
            return None
    
    def _build_enhanced_structured_prompt(self, extracted_data: List[Dict], 
                                         structure_type: str,
                                         user_preferences: Dict[str, Any],
                                         context: ResponseContext) -> str:
        """构建增强的结构化数据提取提示词"""
        import json
        
        data_json = json.dumps(extracted_data[:5], ensure_ascii=False, indent=2)
        
        # 根据用户偏好调整提示词
        sort_preference = user_preferences.get("sort_by", "relevance")
        include_fields = user_preferences.get("include_fields", [])
        
        prompt = f"""
你是一个结构化数据专家。请从搜索结果中提取结构化信息，并根据用户偏好进行优化。

搜索结果:
{data_json}

结构类型: {structure_type}
排序偏好: {sort_preference}
用户查询: {context.original_query}

请提取并结构化数据，要求：
1. 根据用户查询的相关性提取最重要的信息
2. 按照{sort_preference}进行排序
3. 确保数据的一致性和完整性
4. 如果是表格格式，确保列名清晰易懂

请以JSON格式返回：
{{
  "structured_data": [
    {{
      "字段1": "值1",
      "字段2": "值2",
      "relevance_score": 0.95
    }}
  ],
  "data_type": "数据类型说明",
  "total_items": 数量,
  "sort_applied": "应用的排序方式"
}}
"""
        
        return prompt
    
    def _determine_format_type(self, structure_type: str, user_preferences: Dict[str, Any]) -> ResponseFormat:
        """确定响应格式类型"""
        if structure_type == "table":
            return ResponseFormat.TABLE
        elif structure_type == "list":
            return ResponseFormat.LIST
        elif structure_type == "json":
            return ResponseFormat.JSON
        elif user_preferences.get("prefer_structured"):
            return ResponseFormat.TABLE
        else:
            return ResponseFormat.TABLE  # 默认表格格式
    
    def _fallback_formatting(self, extracted_data: List[Dict], 
                            structure_type: str, 
                            user_preferences: Dict[str, Any]) -> tuple:
        """降级格式化处理"""
        if structure_type == "table" or structure_type == "auto":
            content = self._format_as_enhanced_table(extracted_data, user_preferences)
            format_type = ResponseFormat.TABLE
        elif structure_type == "list":
            content = self._format_as_enhanced_list(extracted_data, user_preferences)
            format_type = ResponseFormat.LIST
        else:
            content = self._format_as_json(extracted_data, user_preferences)
            format_type = ResponseFormat.JSON
        
        return content, format_type
    
    def _format_as_enhanced_table(self, data: List[Dict], user_preferences: Dict[str, Any]) -> str:
        """增强的表格格式化"""
        if not data:
            return "无数据"
        
        # 获取所有唯一键
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        if not all_keys:
            return str(data)
        
        # 根据用户偏好排序和过滤字段
        include_fields = user_preferences.get("include_fields", [])
        if include_fields:
            headers = [key for key in include_fields if key in all_keys]
        else:
            # 智能字段排序：重要字段优先
            priority_fields = ["title", "name", "price", "description", "url", "date"]
            headers = []
            for field in priority_fields:
                if field in all_keys:
                    headers.append(field)
            # 添加剩余字段
            for key in sorted(all_keys):
                if key not in headers:
                    headers.append(key)
        
        # 创建表格
        table_lines = [" | ".join(headers)]
        table_lines.append(" | ".join(["---"] * len(headers)))
        
        # 根据用户偏好排序数据
        sort_by = user_preferences.get("sort_by", "relevance")
        if sort_by != "relevance" and sort_by in headers:
            try:
                data = sorted(data, key=lambda x: x.get(sort_by, ""), reverse=True)
            except:
                pass  # 排序失败时保持原顺序
        
        for item in data:
            if isinstance(item, dict):
                row = []
                for key in headers:
                    value = str(item.get(key, ""))
                    # 限制单元格长度
                    if len(value) > 50:
                        value = value[:47] + "..."
                    row.append(value)
                table_lines.append(" | ".join(row))
        
        return "\n".join(table_lines)
    
    def _format_as_enhanced_list(self, data: List[Dict], user_preferences: Dict[str, Any]) -> str:
        """增强的列表格式化"""
        if not data:
            return "无数据"
        
        lines = []
        show_details = user_preferences.get("show_details", True)
        
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                title = item.get("title", item.get("name", f"项目{i}"))
                lines.append(f"{i}. **{title}**")
                
                if show_details:
                    # 显示重要字段
                    important_fields = ["description", "price", "url", "date"]
                    for field in important_fields:
                        if field in item and item[field]:
                            value = str(item[field])
                            if len(value) > 100:
                                value = value[:97] + "..."
                            lines.append(f"   {field}: {value}")
                
                lines.append("")  # 空行分隔
            else:
                lines.append(f"{i}. {str(item)}")
        
        return "\n".join(lines)
    
    def _format_as_json(self, data: List[Dict], user_preferences: Dict[str, Any]) -> str:
        """JSON格式化"""
        import json
        
        # 根据用户偏好过滤字段
        include_fields = user_preferences.get("include_fields", [])
        if include_fields:
            filtered_data = []
            for item in data:
                if isinstance(item, dict):
                    filtered_item = {k: v for k, v in item.items() if k in include_fields}
                    filtered_data.append(filtered_item)
                else:
                    filtered_data.append(item)
            data = filtered_data
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _apply_multi_format_support(self, content: str, response_format: str, 
                                   user_preferences: Dict[str, Any]) -> str:
        """应用多格式支持"""
        if response_format == "markdown":
            # 转换为Markdown格式
            if "|" in content:  # 表格格式
                return content  # 表格已经是Markdown兼容的
            else:
                # 列表格式转Markdown
                lines = content.split("\n")
                markdown_lines = []
                for line in lines:
                    if line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                        # 转换为Markdown列表
                        markdown_lines.append(line.replace("**", "**").replace("   ", "  - "))
                    else:
                        markdown_lines.append(line)
                return "\n".join(markdown_lines)
        
        elif response_format == "csv":
            # 转换为CSV格式
            if "|" in content:  # 表格格式
                lines = content.split("\n")
                csv_lines = []
                for line in lines:
                    if "|" in line and "---" not in line:
                        csv_line = line.replace(" | ", ",").strip()
                        csv_lines.append(csv_line)
                return "\n".join(csv_lines)
        
        elif response_format == "xml":
            # 简单的XML格式转换
            xml_content = "<data>\n"
            lines = content.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("|") and "---" not in line:
                    xml_content += f"  <item>{line.strip()}</item>\n"
            xml_content += "</data>"
            return xml_content
        
        return content  # 默认返回原内容


class DetailedInfoStrategy(ResponseStrategy):
    """详细信息响应策略：生成详细信息响应"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.DETAILED_INFO
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """生成详细信息响应"""
        
        if isinstance(extracted_data, list):
            # 首先尝试使用LLM进行详细提取
            structured_result = self.llm_extractor.extract_structured_data(extracted_data, "detailed")
            
            if structured_result and structured_result.get("structured_data"):
                content = self._format_detailed_structured_data(structured_result["structured_data"])
            else:
                content = self._format_detailed_list(extracted_data)
        elif isinstance(extracted_data, dict):
            content = self._format_detailed_dict(extracted_data)
        else:
            content = str(extracted_data)
        
        return DetailedResponse(
            content=content,
            format=ResponseFormat.DETAILED_TEXT,
            metadata={"detail_level": "comprehensive"},
            success=True
        )
    
    def _format_detailed_structured_data(self, data: List[Dict]) -> str:
        """格式化LLM提取的详细结构化数据"""
        sections = []
        for i, item in enumerate(data, 1):
            section = f"=== 项目 {i} ==="
            if isinstance(item, dict):
                for key, value in item.items():
                    section += f"\n{key}: {value}"
            else:
                section += f"\n{str(item)}"
            sections.append(section)
        
        return "\n\n".join(sections)
    
    def _format_detailed_list(self, data: List) -> str:
        """格式化列表数据并显示完整详情"""
        if not data:
            return "无详细信息可显示"
        
        sections = []
        for i, item in enumerate(data, 1):
            section = f"=== 结果 {i} ==="
            if isinstance(item, dict):
                for key, value in item.items():
                    section += f"\n{key}: {value}"
            else:
                section += f"\n{str(item)}"
            sections.append(section)
        
        return "\n\n".join(sections)
    
    def _format_detailed_dict(self, data: Dict) -> str:
        """格式化字典数据并显示完整详情"""
        lines = ["=== 详细信息 ==="]
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)


class FullPageContentStrategy(ResponseStrategy):
    """完整页面内容响应策略：返回完整页面内容"""
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.FULL_PAGE_CONTENT
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """返回完整页面内容"""
        
        # extracted_data应该是完整的HTML内容
        return FullPageResponse(
            content=str(extracted_data),
            format=ResponseFormat.HTML,
            metadata={"content_length": len(str(extracted_data))},
            success=True
        )


class ResponseGenerator:
    """增强的主响应生成器：支持多轮对话上下文管理和个性化响应"""
    
    def __init__(self):
        self.logger = get_logger()
        self.llm_manager = get_llm_manager()
        
        # 注册所有策略
        self.strategies = [
            SummaryInfoStrategy(),
            StructuredDataStrategy(),
            DetailedInfoStrategy(),
            FullPageContentStrategy()
        ]
        
        # 多轮对话上下文管理
        self.conversation_context = {}
        self.user_preferences_cache = {}
    
    def generate_response(self, extracted_data: Any, intent_result: IntentResult, 
                         context: Optional[Dict[str, Any]] = None) -> GeneratedResponse:
        """
        根据意图和提取的数据生成适当的响应，支持多轮对话上下文管理
        
        Args:
            extracted_data: 从网页提取的数据
            intent_result: 分类的用户意图
            context: 附加的上下文信息
            
        Returns:
            适合用户意图的生成响应
        """
        if context is None:
            context = {}
        
        # 获取会话ID用于上下文管理
        session_id = context.get("session_id", "default")
        
        # 更新对话上下文
        self._update_conversation_context(session_id, intent_result, context)
        
        # 创建增强的响应上下文对象
        response_context = ResponseContext(
            original_query=context.get("original_query", ""),
            original_text=context.get("original_text", ""),
            page_url=context.get("page_url", ""),
            session_state=context.get("session_state", {})
        )
        
        # 应用上下文增强
        enhanced_context = self._enhance_context_with_history(response_context, session_id)
        
        # 查找适当的策略，考虑多意图情况
        strategy = self._select_optimal_strategy(intent_result, enhanced_context)
        
        try:
            # 生成响应
            response = strategy.generate(extracted_data, intent_result, enhanced_context)
            
            # 应用后处理增强
            enhanced_response = self._post_process_response(response, intent_result, enhanced_context)
            
            # 更新用户偏好缓存
            self._update_user_preferences(session_id, intent_result, enhanced_response)
            
            self.logger.info(f"使用 {strategy.__class__.__name__} 生成响应")
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"生成响应时出错: {e}")
            return GeneratedResponse(
                content=f"抱歉，处理响应时出现错误：{str(e)}",
                format=ResponseFormat.NATURAL_LANGUAGE,
                metadata={},
                success=False,
                error=str(e)
            )
    
    def _update_conversation_context(self, session_id: str, intent_result: IntentResult, 
                                   context: Dict[str, Any]) -> None:
        """更新对话上下文"""
        if session_id not in self.conversation_context:
            self.conversation_context[session_id] = {
                "intent_history": [],
                "topic_continuity": [],
                "user_patterns": {},
                "last_response_type": None
            }
        
        session_context = self.conversation_context[session_id]
        
        # 更新意图历史
        session_context["intent_history"].append({
            "intent": intent_result.intent_type,
            "confidence": intent_result.confidence,
            "keywords": intent_result.keywords,
            "timestamp": context.get("timestamp", "")
        })
        
        # 限制历史长度
        if len(session_context["intent_history"]) > 10:
            session_context["intent_history"] = session_context["intent_history"][-10:]
        
        # 更新话题连续性
        current_topics = self._extract_topics_from_intent(intent_result)
        session_context["topic_continuity"].extend(current_topics)
        if len(session_context["topic_continuity"]) > 20:
            session_context["topic_continuity"] = session_context["topic_continuity"][-20:]
    
    def _extract_topics_from_intent(self, intent_result: IntentResult) -> List[str]:
        """从意图结果中提取话题"""
        topics = []
        
        # 从关键词中提取话题
        for keyword in intent_result.keywords:
            if len(keyword) > 2:  # 过滤太短的词
                topics.append(keyword.lower())
        
        # 从意图类型推断话题
        intent_topics = {
            IntentType.SEARCH: ["搜索", "查找"],
            IntentType.SHOPPING: ["购物", "商品"],
            IntentType.NAVIGATION: ["导航", "访问"],
            IntentType.SOCIAL_INTERACTION: ["社交", "分享"]
        }
        
        if intent_result.intent_type in intent_topics:
            topics.extend(intent_topics[intent_result.intent_type])
        
        return list(set(topics))  # 去重
    
    def _enhance_context_with_history(self, context: ResponseContext, session_id: str) -> ResponseContext:
        """使用历史信息增强上下文"""
        if session_id not in self.conversation_context:
            return context
        
        session_context = self.conversation_context[session_id]
        
        # 创建增强的会话状态
        enhanced_session_state = dict(context.session_state)
        enhanced_session_state.update({
            "intent_history": session_context["intent_history"],
            "topic_continuity": session_context["topic_continuity"],
            "user_patterns": session_context["user_patterns"],
            "conversation_length": len(session_context["intent_history"])
        })
        
        # 添加用户偏好
        if session_id in self.user_preferences_cache:
            enhanced_session_state["user_preferences"] = self.user_preferences_cache[session_id]
        
        # 创建新的上下文对象
        return ResponseContext(
            original_query=context.original_query,
            original_text=context.original_text,
            page_url=context.page_url,
            session_state=enhanced_session_state
        )
    
    def _select_optimal_strategy(self, intent_result: IntentResult, context: ResponseContext) -> ResponseStrategy:
        """选择最优策略，考虑多意图和上下文"""
        # 处理多意图情况
        if intent_result.intent_type == IntentType.MULTI_INTENT and intent_result.secondary_intents:
            # 选择最适合的主要策略
            primary_strategy = self._find_strategy_for_intent(intent_result.secondary_intents[0])
            if primary_strategy:
                return primary_strategy
        
        # 查找主要意图的策略
        strategy = self._find_strategy_for_intent(intent_result.intent_type)
        
        if strategy is None:
            # 基于上下文选择降级策略
            session_state = context.session_state
            intent_history = session_state.get("intent_history", [])
            
            if intent_history:
                # 基于历史意图选择策略
                recent_intents = [h["intent"] for h in intent_history[-3:]]
                if IntentType.STRUCTURED_DATA in recent_intents:
                    strategy = StructuredDataStrategy()
                elif IntentType.DETAILED_INFO in recent_intents:
                    strategy = DetailedInfoStrategy()
            
            # 最终降级到摘要策略
            if strategy is None:
                strategy = SummaryInfoStrategy()
        
        return strategy
    
    def _find_strategy_for_intent(self, intent_type: IntentType) -> Optional[ResponseStrategy]:
        """查找指定意图类型的策略"""
        for strategy in self.strategies:
            if strategy.can_handle(intent_type):
                return strategy
        return None
    
    def _post_process_response(self, response: GeneratedResponse, intent_result: IntentResult, 
                              context: ResponseContext) -> GeneratedResponse:
        """响应后处理增强"""
        try:
            # 应用个性化调整
            personalized_content = self._apply_personalization(response.content, context)
            
            # 添加上下文相关的建议
            suggestions = self._generate_contextual_suggestions(intent_result, context)
            
            # 更新元数据
            enhanced_metadata = dict(response.metadata)
            enhanced_metadata.update({
                "personalization_applied": personalized_content != response.content,
                "contextual_suggestions": suggestions,
                "conversation_aware": True
            })
            
            # 创建增强的响应对象
            if hasattr(response, 'structure_type'):
                # StructuredResponse
                return StructuredResponse(
                    content=personalized_content,
                    format=response.format,
                    metadata=enhanced_metadata,
                    success=response.success,
                    structure_type=getattr(response, 'structure_type', 'auto'),
                    structured_data=getattr(response, 'structured_data', [])
                )
            elif hasattr(response, 'detail_level'):
                # DetailedResponse
                return DetailedResponse(
                    content=personalized_content,
                    format=response.format,
                    metadata=enhanced_metadata,
                    success=response.success
                )
            else:
                # SummaryResponse or GeneratedResponse
                return SummaryResponse(
                    content=personalized_content,
                    format=response.format,
                    metadata=enhanced_metadata,
                    success=response.success
                )
                
        except Exception as e:
            self.logger.warning(f"响应后处理失败: {e}")
            return response  # 返回原始响应
    
    def _apply_personalization(self, content: str, context: ResponseContext) -> str:
        """应用个性化调整"""
        session_state = context.session_state
        user_preferences = session_state.get("user_preferences", {})
        
        if not user_preferences:
            return content
        
        # 应用语言风格偏好
        style = user_preferences.get("language_style", "standard")
        if style == "formal":
            # 转换为正式语言
            content = content.replace("你", "您").replace("咋样", "如何")
        elif style == "casual":
            # 转换为随意语言
            content = content.replace("您", "你")
        
        # 应用长度偏好
        length_pref = user_preferences.get("response_length", "standard")
        if length_pref == "brief" and len(content) > 200:
            # 截断长响应
            sentences = content.split("。")
            if len(sentences) > 1:
                content = sentences[0] + "。"
        
        return content
    
    def _generate_contextual_suggestions(self, intent_result: IntentResult, 
                                       context: ResponseContext) -> List[str]:
        """生成上下文相关的建议"""
        suggestions = []
        
        # 基于意图类型生成建议
        if intent_result.intent_type == IntentType.SEARCH:
            suggestions.extend(["细化搜索条件", "查看更多结果", "切换搜索引擎"])
        elif intent_result.intent_type == IntentType.STRUCTURED_DATA:
            suggestions.extend(["导出数据", "更改排序方式", "筛选字段"])
        elif intent_result.intent_type == IntentType.SUMMARY_INFO:
            suggestions.extend(["获取详细信息", "查看相关内容", "保存结果"])
        
        # 基于二级意图生成建议
        if intent_result.secondary_intents:
            for secondary_intent in intent_result.secondary_intents:
                if secondary_intent == IntentType.SCREENSHOT:
                    suggestions.append("截取页面截图")
                elif secondary_intent == IntentType.DOWNLOAD:
                    suggestions.append("下载相关内容")
        
        # 基于对话历史生成建议
        session_state = context.session_state
        intent_history = session_state.get("intent_history", [])
        if len(intent_history) > 1:
            # 如果用户经常搜索，建议保存搜索历史
            search_count = sum(1 for h in intent_history if h["intent"] == IntentType.SEARCH)
            if search_count > 3:
                suggestions.append("保存搜索历史")
        
        return suggestions[:5]  # 限制建议数量
    
    def _update_user_preferences(self, session_id: str, intent_result: IntentResult, 
                                response: GeneratedResponse) -> None:
        """更新用户偏好缓存"""
        if session_id not in self.user_preferences_cache:
            self.user_preferences_cache[session_id] = {}
        
        preferences = self.user_preferences_cache[session_id]
        
        # 从意图结果中学习偏好
        if intent_result.response_format != "natural_language":
            preferences["preferred_format"] = intent_result.response_format
        
        # 从响应成功率中学习
        if response.success:
            strategy_name = response.metadata.get("strategy_used", "unknown")
            if "successful_strategies" not in preferences:
                preferences["successful_strategies"] = {}
            
            preferences["successful_strategies"][strategy_name] = \
                preferences["successful_strategies"].get(strategy_name, 0) + 1
        
        # 从关键词中学习兴趣
        if "interests" not in preferences:
            preferences["interests"] = {}
        
        for keyword in intent_result.keywords:
            if len(keyword) > 2:
                preferences["interests"][keyword] = \
                    preferences["interests"].get(keyword, 0) + 1
        
        # 限制偏好缓存大小
        if len(preferences.get("interests", {})) > 50:
            # 保留最常见的兴趣
            sorted_interests = sorted(preferences["interests"].items(), 
                                    key=lambda x: x[1], reverse=True)
            preferences["interests"] = dict(sorted_interests[:30])
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        if session_id not in self.conversation_context:
            return {"error": "Session not found"}
        
        session_context = self.conversation_context[session_id]
        user_preferences = self.user_preferences_cache.get(session_id, {})
        
        return {
            "total_interactions": len(session_context["intent_history"]),
            "common_intents": self._get_common_intents(session_context["intent_history"]),
            "main_topics": self._get_main_topics(session_context["topic_continuity"]),
            "user_preferences": user_preferences,
            "conversation_patterns": session_context["user_patterns"]
        }
    
    def _get_common_intents(self, intent_history: List[Dict]) -> List[str]:
        """获取常见意图"""
        intent_counts = {}
        for item in intent_history:
            intent = item["intent"].value
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return sorted(intent_counts.keys(), key=lambda x: intent_counts[x], reverse=True)[:5]
    
    def _get_main_topics(self, topic_continuity: List[str]) -> List[str]:
        """获取主要话题"""
        topic_counts = {}
        for topic in topic_continuity:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return sorted(topic_counts.keys(), key=lambda x: topic_counts[x], reverse=True)[:10]