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
from dataclasses import dataclass

from src.reasoning.intent_classifier import IntentType, IntentResult
from src.reasoning.llm_extractor import LLMExtractor
from src.common.logger import get_logger


@dataclass
class GeneratedResponse:
    """Response generated based on user intent"""
    content: str
    format: str
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class ResponseStrategy(ABC):
    """Abstract base class for response generation strategies"""
    
    @abstractmethod
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: Dict[str, Any]) -> GeneratedResponse:
        """Generate response based on extracted data and intent"""
        pass
    
    @abstractmethod
    def can_handle(self, intent_type: IntentType) -> bool:
        """Check if this strategy can handle the given intent type"""
        pass


class SummaryInfoStrategy(ResponseStrategy):
    """Strategy for generating summary information responses using LLM-based extraction"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.SUMMARY_INFO
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: Dict[str, Any]) -> GeneratedResponse:
        """Generate concise summary response using LLM-based extraction"""
        
        self.logger.info(f"开始生成摘要信息响应，意图关键词: {intent_result.keywords}")
        
        # Get original query from context
        original_query = context.get("original_query", "")
        
        if not extracted_data:
            self.logger.warning("没有提取到数据")
            return GeneratedResponse(
                content="抱歉，未能获取到相关信息。",
                format="natural_language",
                metadata={},
                success=False,
                error="No data extracted"
            )
        
        self.logger.info(f"提取到的数据类型: {type(extracted_data)}")
        
        # Handle different data types
        if isinstance(extracted_data, list) and extracted_data:
            self.logger.info(f"处理列表数据，项目数量: {len(extracted_data)}")
            # Use LLM-based extraction for search results
            summary = self.llm_extractor.extract_information(
                extracted_data, original_query
            )
            
            self.logger.info(f"LLM提取结果: {summary}")
            
            # Fallback to generic extraction if LLM-based fails
            if not summary:
                self.logger.info("LLM提取失败，使用通用摘要")
                summary = self._extract_generic_summary(extracted_data)
                
        elif isinstance(extracted_data, dict):
            self.logger.info("处理字典数据")
            # For structured data, extract relevant fields
            summary = self._extract_summary_from_structured_data(
                extracted_data, intent_result
            )
        else:
            self.logger.info("处理文本数据")
            # For text content, summarize
            summary = self._extract_summary_from_text(str(extracted_data))
        
        self.logger.info(f"最终摘要: {summary}")
        
        return GeneratedResponse(
            content=summary,
            format="natural_language",
            metadata={"source_data_count": len(extracted_data) if isinstance(extracted_data, list) else 1},
            success=True
        )
    

    
    def _extract_generic_summary(self, results: List[Dict]) -> str:
        """Extract generic summary from search results (primary fallback method)"""
        if not results:
            return "未找到相关信息。"
        
        # Use first result as primary source
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
        """Extract summary from structured data"""
        # Implementation depends on data structure
        # This is a simplified version
        if "summary" in data:
            return data["summary"]
        elif "title" in data:
            return data["title"]
        else:
            return str(data)[:200] + "..."
    
    def _extract_summary_from_text(self, text: str) -> str:
        """Extract summary from plain text"""
        # Simple text summarization
        sentences = text.split("。")
        if len(sentences) > 1:
            return sentences[0] + "。"
        else:
            return text[:200] + ("..." if len(text) > 200 else "")


class StructuredDataStrategy(ResponseStrategy):
    """Strategy for generating structured data responses using LLM-based extraction"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.STRUCTURED_DATA
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: Dict[str, Any]) -> GeneratedResponse:
        """Generate structured data response using LLM-based extraction"""
        
        structure_type = intent_result.additional_params.get("structure_type", "auto")
        
        if isinstance(extracted_data, list):
            # Use LLM to extract structured data
            structured_result = self.llm_extractor.extract_structured_data(extracted_data, structure_type)
            
            if structured_result and structured_result.get("structured_data"):
                structured_content = self._format_structured_data(structured_result["structured_data"], structure_type)
                format_type = structure_type if structure_type != "auto" else "table"
            else:
                # Fallback to original formatting
                if structure_type == "table" or structure_type == "auto":
                    structured_content = self._format_as_table(extracted_data)
                    format_type = "table"
                else:
                    structured_content = self._format_as_list(extracted_data)
                    format_type = "list"
        else:
            structured_content = json.dumps(extracted_data, ensure_ascii=False, indent=2)
            format_type = "json"
        
        return GeneratedResponse(
            content=structured_content,
            format=format_type,
            metadata={"item_count": len(extracted_data) if isinstance(extracted_data, list) else 1},
            success=True
        )
    
    def _format_structured_data(self, data: List[Dict], structure_type: str) -> str:
        """Format LLM-extracted structured data"""
        if structure_type == "table" or structure_type == "auto":
            return self._format_as_table(data)
        else:
            return self._format_as_list(data)
    
    def _format_as_table(self, data: List[Dict]) -> str:
        """Format data as table"""
        if not data:
            return "无数据"
        
        # Get all unique keys
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        if not all_keys:
            return str(data)
        
        # Create table
        headers = list(all_keys)
        table_lines = [" | ".join(headers)]
        table_lines.append(" | ".join(["---"] * len(headers)))
        
        for item in data:
            if isinstance(item, dict):
                row = [str(item.get(key, "")) for key in headers]
                table_lines.append(" | ".join(row))
        
        return "\n".join(table_lines)
    
    def _format_as_list(self, data: List) -> str:
        """Format data as numbered list"""
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
    """Strategy for generating detailed information responses"""
    
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.logger = get_logger()
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.DETAILED_INFO
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: Dict[str, Any]) -> GeneratedResponse:
        """Generate detailed information response"""
        
        if isinstance(extracted_data, list):
            # First try to use LLM for detailed extraction
            structured_result = self.llm_extractor.extract_structured_data(extracted_data, "detailed")
            
            if structured_result and structured_result.get("structured_data"):
                content = self._format_detailed_structured_data(structured_result["structured_data"])
            else:
                content = self._format_detailed_list(extracted_data)
        elif isinstance(extracted_data, dict):
            content = self._format_detailed_dict(extracted_data)
        else:
            content = str(extracted_data)
        
        return GeneratedResponse(
            content=content,
            format="detailed_text",
            metadata={"detail_level": "comprehensive"},
            success=True
        )
    
    def _format_detailed_structured_data(self, data: List[Dict]) -> str:
        """Format LLM-extracted detailed structured data"""
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
        """Format list data with full details"""
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
        """Format dictionary data with full details"""
        lines = ["=== 详细信息 ==="]
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)


class FullPageContentStrategy(ResponseStrategy):
    """Strategy for returning full page content"""
    
    def can_handle(self, intent_type: IntentType) -> bool:
        return intent_type == IntentType.FULL_PAGE_CONTENT
    
    def generate(self, extracted_data: Any, intent_result: IntentResult, 
                context: Dict[str, Any]) -> GeneratedResponse:
        """Return full page content"""
        
        # extracted_data should be the full HTML content
        return GeneratedResponse(
            content=str(extracted_data),
            format="html",
            metadata={"content_length": len(str(extracted_data))},
            success=True
        )


class ResponseGenerator:
    """Main response generator that delegates to appropriate strategies"""
    
    def __init__(self):
        self.logger = get_logger()
        
        # Register all strategies
        self.strategies = [
            SummaryInfoStrategy(),
            StructuredDataStrategy(),
            DetailedInfoStrategy(),
            FullPageContentStrategy()
        ]
    
    def generate_response(self, extracted_data: Any, intent_result: IntentResult, 
                         context: Optional[Dict[str, Any]] = None) -> GeneratedResponse:
        """
        Generate appropriate response based on intent and extracted data
        
        Args:
            extracted_data: Data extracted from web page
            intent_result: Classified user intent
            context: Additional context information
            
        Returns:
            Generated response appropriate for the user's intent
        """
        if context is None:
            context = {}
        
        # Find appropriate strategy
        strategy = None
        for s in self.strategies:
            if s.can_handle(intent_result.intent_type):
                strategy = s
                break
        
        if strategy is None:
            # Fallback to summary strategy
            strategy = SummaryInfoStrategy()
        
        try:
            response = strategy.generate(extracted_data, intent_result, context)
            self.logger.info(f"Generated response using {strategy.__class__.__name__}")
            return response
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return GeneratedResponse(
                content=f"抱歉，处理响应时出现错误：{str(e)}",
                format="natural_language",
                metadata={},
                success=False,
                error=str(e)
            )