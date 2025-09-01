#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intent Classifier

Classifies user intent to determine the appropriate response generation strategy.
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.common.logger import get_logger


class IntentType(Enum):
    """Types of user intents that require different response strategies"""
    
    # Information retrieval intents
    SUMMARY_INFO = "summary_info"           # User wants a concise summary (e.g., weather, news headline)
    DETAILED_INFO = "detailed_info"         # User wants comprehensive information
    STRUCTURED_DATA = "structured_data"     # User wants structured/tabular data
    
    # Content extraction intents  
    FULL_PAGE_CONTENT = "full_page_content" # User wants complete HTML/page content
    SPECIFIC_ELEMENT = "specific_element"   # User wants specific page elements
    
    # Interactive intents
    NAVIGATION = "navigation"               # User wants to navigate/browse
    FORM_INTERACTION = "form_interaction"   # User wants to fill forms/interact
    
    # Media/Visual intents
    SCREENSHOT = "screenshot"               # User wants visual capture
    DOWNLOAD = "download"                   # User wants to download content
    
    # Unknown intent
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent_type: IntentType
    confidence: float
    keywords: List[str]
    extraction_target: Optional[str] = None
    response_format: str = "natural_language"
    additional_params: Dict[str, Any] = None


class IntentClassifier:
    """Classifies user intent to determine appropriate response strategy"""
    
    def __init__(self):
        self.logger = get_logger()
        
        # Intent patterns for classification
        self.intent_patterns = {
            IntentType.SUMMARY_INFO: [
                r"(\w+).*?(怎么样|如何|情况|多少|现在|是什么|怎样)",  # Generic question patterns
                r"(简单|简要|概况|摘要).*?(介绍|说明|信息)",
                r"(今天|现在|当前).*?(是什么|怎样|如何)",
                r"\w+\s+(today|now|current)",  # Generic English patterns
                r"(today|now)\s+\w+",  # Alternative English pattern
                r"what.*?is.*?",  # English question patterns
                r"how.*?is.*?"
            ],
            
            IntentType.DETAILED_INFO: [
                r"(详细|complete|全面|comprehensive).*?(信息|内容|资料)",
                r"(完整|所有|全部).*?(介绍|说明|内容)",
                r"(深入|thorough).*?(了解|分析)",
                r"(更多|more).*?(信息|details)"
            ],
            
            IntentType.STRUCTURED_DATA: [
                r"(表格|table|列表|list).*?(数据|信息)",
                r"(结构化|structured).*?(数据|提取)",
                r"(价格|price).*?(对比|比较|列表)",
                r"(统计|statistics|数据分析)",
                r"(导出|export).*?(数据|excel|csv)"
            ],
            
            IntentType.FULL_PAGE_CONTENT: [
                r"(整个|全部|complete).*?(页面|网页|html)",
                r"(所有|all).*?(内容|content)",
                r"(保存|save).*?(页面|网页)",
                r"(下载|download).*?(页面|html)"
            ],
            
            IntentType.SPECIFIC_ELEMENT: [
                r"(提取|extract).*?(特定|specific|某个).*?(元素|element)",
                r"(获取|get).*?(标题|title|链接|link|图片|image)",
                r"(找到|find).*?(按钮|button|输入框|input)",
                r"(选择器|selector|元素定位)"
            ],
            
            IntentType.SCREENSHOT: [
                r"(截图|screenshot|capture)",
                r"(拍照|photo|图像|image).*?(页面|screen)",
                r"(保存|save).*?(屏幕|截图)"
            ],
            
            IntentType.NAVIGATION: [
                r"(打开|open|访问|visit|go to)",
                r"(导航|navigate).*?(到|至)",
                r"(跳转|jump|redirect)",
                r"(浏览|browse)"
            ],
            
            IntentType.FORM_INTERACTION: [
                r"(填写|fill|输入|input).*?(表单|form)",
                r"(登录|login|注册|register)",
                r"(提交|submit|发送|send)",
                r"(点击|click).*?(按钮|button|链接|link)"
            ]
        }
        
        # Response format indicators
        self.format_patterns = {
            "json": [r"json格式", r"结构化", r"structured"],
            "table": [r"表格", r"列表", r"table", r"list"],
            "markdown": [r"markdown", r"格式化", r"formatted"],
            "natural_language": [r"自然语言", r"简单回答", r"直接告诉我"]
        }

    def classify_intent(self, user_text: str, page_data: Dict[str, Any] = None) -> IntentResult:
        """
        Classify user intent based on natural language input
        
        Args:
            user_text: User's natural language input
            page_data: Current page data for context
            
        Returns:
            IntentResult with classified intent and parameters
        """
        user_text_lower = user_text.lower()
        
        # Score each intent type
        intent_scores = {}
        matched_keywords = []
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, user_text_lower)
                if matches:
                    score += len(matches) * 1.0
                    matched_keywords.extend([m if isinstance(m, str) else m[0] for m in matches])
            
            if score > 0:
                intent_scores[intent_type] = score
        
        # Determine response format preference
        response_format = "natural_language"
        for fmt, patterns in self.format_patterns.items():
            if any(re.search(pattern, user_text_lower) for pattern in patterns):
                response_format = fmt
                break
        
        # Select best intent
        if intent_scores:
            best_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
            confidence = min(intent_scores[best_intent] / len(self.intent_patterns[best_intent]), 1.0)
        else:
            # Default fallback based on context
            best_intent = self._fallback_intent_detection(user_text_lower, page_data)
            confidence = 0.5
        
        # Extract additional parameters
        additional_params = self._extract_additional_params(user_text, best_intent)
        
        return IntentResult(
            intent_type=best_intent,
            confidence=confidence,
            keywords=list(set(matched_keywords)),
            response_format=response_format,
            additional_params=additional_params
        )
    
    def _fallback_intent_detection(self, user_text: str, page_data: Dict[str, Any]) -> IntentType:
        """Fallback intent detection when no patterns match"""
        
        # Check for question patterns indicating info request
        if any(word in user_text for word in ["什么", "怎样", "如何", "多少", "哪里", "什么时候"]):
            if any(word in user_text for word in ["详细", "完整", "全部"]):
                return IntentType.DETAILED_INFO
            else:
                return IntentType.SUMMARY_INFO
        
        # Check for action patterns
        if any(word in user_text for word in ["点击", "输入", "填写", "选择"]):
            return IntentType.FORM_INTERACTION
        
        # Check for navigation patterns
        if any(word in user_text for word in ["打开", "访问", "进入", "跳转"]):
            return IntentType.NAVIGATION
        
        # Default to summary info for information requests
        return IntentType.SUMMARY_INFO
    
    def _extract_additional_params(self, user_text: str, intent_type: IntentType) -> Dict[str, Any]:
        """Extract additional parameters based on intent type"""
        params = {}
        
        if intent_type == IntentType.STRUCTURED_DATA:
            # Extract data type preferences
            if "表格" in user_text or "table" in user_text.lower():
                params["structure_type"] = "table"
            elif "列表" in user_text or "list" in user_text.lower():
                params["structure_type"] = "list"
            else:
                params["structure_type"] = "auto"
        
        elif intent_type == IntentType.SUMMARY_INFO:
            # Extract summary length preference
            if any(word in user_text for word in ["简单", "简要", "brief"]):
                params["summary_length"] = "brief"
            elif any(word in user_text for word in ["详细一点", "more details"]):
                params["summary_length"] = "moderate"
            else:
                params["summary_length"] = "brief"
        
        elif intent_type == IntentType.SPECIFIC_ELEMENT:
            # Extract element type
            element_types = {
                "title": ["标题", "title"],
                "link": ["链接", "link", "url"],
                "image": ["图片", "image", "img"],
                "button": ["按钮", "button"],
                "text": ["文本", "text", "内容"]
            }
            
            for elem_type, keywords in element_types.items():
                if any(keyword in user_text.lower() for keyword in keywords):
                    params["element_type"] = elem_type
                    break
        
        return params