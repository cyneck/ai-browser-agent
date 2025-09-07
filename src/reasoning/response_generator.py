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
    """摘要信息响应策略：使用LLM提取生成简洁摘要"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.SUMMARY_INFO
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """生成简洁摘要响应"""
        
        self.logger.info(f"开始生成摘要信息响应，意图关键词: {intent_result.keywords}")
        
        # 获取原始查询
        original_query = context.original_query
        
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
            # 使用LLM提取搜索结果
            summary = self.llm_extractor.extract_information(
                extracted_data, original_query
            )
            
            self.logger.info(f"LLM提取结果: {summary}")
            
            # 如果LLM提取失败，使用通用摘要
            if not summary:
                self.logger.info("LLM提取失败，使用通用摘要")
                summary = self._extract_generic_summary(extracted_data)
                
        elif isinstance(extracted_data, dict):
            self.logger.info("处理字典数据")
            # 对于结构化数据，提取相关字段
            summary = self._extract_summary_from_structured_data(
                extracted_data, intent_result
            )
        else:
            self.logger.info("处理文本数据")
            # 对于文本内容，进行摘要
            summary = self._extract_summary_from_text(str(extracted_data))
        
        self.logger.info(f"最终摘要: {summary}")
        
        return SummaryResponse(
            content=summary,
            format=ResponseFormat.NATURAL_LANGUAGE,
            metadata={"source_data_count": len(extracted_data) if isinstance(extracted_data, list) else 1},
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
    
    def _extract_summary_from_text(self, text: str) -> str:
        """从纯文本中提取摘要"""
        # 简单文本摘要
        sentences = text.split("。")
        if len(sentences) > 1:
            return sentences[0] + "。"
        else:
            return text[:200] + ("..." if len(text) > 200 else "")


class StructuredDataStrategy(ResponseStrategy):
    """结构化数据响应策略：使用LLM提取生成结构化数据"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.STRUCTURED_DATA
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: ResponseContext) -> GeneratedResponse:
        """生成结构化数据响应"""
        
        structure_type = intent_result.additional_params.get("structure_type", "auto")
        
        if isinstance(extracted_data, list):
            # 使用LLM提取结构化数据
            structured_result = self.llm_extractor.extract_structured_data(extracted_data, structure_type)
            
            if structured_result and structured_result.get("structured_data"):
                structured_content = self._format_structured_data(structured_result["structured_data"], structure_type)
                format_type = ResponseFormat.TABLE if structure_type != "auto" else ResponseFormat.TABLE
            else:
                # 降级到原始格式化
                if structure_type == "table" or structure_type == "auto":
                    structured_content = self._format_as_table(extracted_data)
                    format_type = ResponseFormat.TABLE
                else:
                    structured_content = self._format_as_list(extracted_data)
                    format_type = ResponseFormat.LIST
        else:
            structured_content = json.dumps(extracted_data, ensure_ascii=False, indent=2)
            format_type = ResponseFormat.JSON
        
        return StructuredResponse(
            content=structured_content,
            format=format_type,
            metadata={"item_count": len(extracted_data) if isinstance(extracted_data, list) else 1},
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
    """主响应生成器：委托给适当的策略"""
    
    def __init__(self):
        self.logger = get_logger()
        
        # 注册所有策略
        self.strategies = [
            SummaryInfoStrategy(),
            StructuredDataStrategy(),
            DetailedInfoStrategy(),
            FullPageContentStrategy()
        ]
    
    def generate_response(self, extracted_data: Any, intent_result: IntentResult, 
                         context: Optional[Dict[str, Any]] = None) -> GeneratedResponse:
        """
        根据意图和提取的数据生成适当的响应
        
        Args:
            extracted_data: 从网页提取的数据
            intent_result: 分类的用户意图
            context: 附加的上下文信息
            
        Returns:
            适合用户意图的生成响应
        """
        if context is None:
            context = {}
        
        # 创建响应上下文对象
        response_context = ResponseContext(
            original_query=context.get("original_query", ""),
            original_text=context.get("original_text", ""),
            page_url=context.get("page_url", ""),
            session_state=context.get("session_state", {})
        )
        
        # 查找适当的策略
        strategy = None
        for s in self.strategies:
            if s.can_handle(intent_result.intent_type):
                strategy = s
                break
        
        if strategy is None:
            # 降级到摘要策略
            strategy = SummaryInfoStrategy()
        
        try:
            response = strategy.generate(extracted_data, intent_result, response_context)
            self.logger.info(f"使用 {strategy.__class__.__name__} 生成响应")
            return response
        except Exception as e:
            self.logger.error(f"生成响应时出错: {e}")
            return GeneratedResponse(
                content=f"抱歉，处理响应时出现错误：{str(e)}",
                format=ResponseFormat.NATURAL_LANGUAGE,
                metadata={},
                success=False,
                error=str(e)
            )