#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
响应数据模型

定义系统中使用的响应数据实体，包括生成的响应、响应策略等。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from src.reasoning.intent_classifier import IntentType


class ResponseFormat(Enum):
    """响应格式类型"""
    NATURAL_LANGUAGE = "natural_language"
    JSON = "json"
    TABLE = "table"
    LIST = "list"
    DETAILED_TEXT = "detailed_text"
    HTML = "html"


@dataclass
class GeneratedResponse:
    """生成的响应数据实体"""
    content: str
    format: ResponseFormat
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class ResponseContext:
    """响应上下文数据实体"""
    original_query: str
    original_text: str
    page_url: str = ""
    session_state: Dict[str, Any] = field(default_factory=dict)


class ResponseStrategyType(Enum):
    """响应策略类型"""
    SUMMARY_INFO = "summary_info"
    STRUCTURED_DATA = "structured_data"
    DETAILED_INFO = "detailed_info"
    FULL_PAGE_CONTENT = "full_page_content"


@dataclass
class ResponseStrategy:
    """响应策略数据实体"""
    strategy_type: ResponseStrategyType
    intent_type: IntentType
    description: str = ""
    
    
@dataclass
class SummaryResponse(GeneratedResponse):
    """摘要信息响应"""
    format: ResponseFormat = ResponseFormat.NATURAL_LANGUAGE
    summary_length: str = "brief"


@dataclass
class StructuredResponse(GeneratedResponse):
    """结构化数据响应"""
    format: ResponseFormat = ResponseFormat.TABLE
    structure_type: str = "auto"
    structured_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DetailedResponse(GeneratedResponse):
    """详细信息响应"""
    format: ResponseFormat = ResponseFormat.DETAILED_TEXT
    detail_level: str = "comprehensive"


@dataclass
class FullPageResponse(GeneratedResponse):
    """完整页面内容响应"""
    format: ResponseFormat = ResponseFormat.HTML
    content_length: int = 0