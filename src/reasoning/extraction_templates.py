#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extraction Templates

Configurable templates for extracting different types of information from search results.
This replaces hardcoded extraction logic with flexible, template-driven patterns.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from src.common.logger import get_logger


@dataclass
class ExtractionPattern:
    """Defines a pattern for extracting information"""
    name: str
    regex_patterns: List[str]
    keywords: List[str]
    format_template: str
    fallback_template: str = "未能提取到相关信息"


@dataclass
class ExtractionRule:
    """Defines a rule for when and how to apply extraction patterns"""
    intent_keywords: List[str]
    patterns: List[ExtractionPattern]
    priority: int = 1


class ExtractionEngine:
    """Generic extraction engine that uses configurable templates"""
    
    def __init__(self):
        self.logger = get_logger()
        self.extraction_rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[ExtractionRule]:
        """Load default extraction rules (can be extended or replaced)"""
        return [
            # Weather information extraction
            ExtractionRule(
                intent_keywords=["天气", "weather", "温度", "temperature"],
                patterns=[
                    ExtractionPattern(
                        name="temperature_range",
                        regex_patterns=[
                            r"(\d+)°?\s*[~\-到至]\s*(\d+)°?",
                            r"温度\s*(\d+)\s*[-~至到]\s*(\d+)",
                            r"(\d+)\s*度\s*[-~至到]\s*(\d+)\s*度"
                        ],
                        keywords=["温度", "temperature", "度", "°"],
                        format_template="温度{temp1}°~{temp2}°"
                    ),
                    ExtractionPattern(
                        name="weather_condition", 
                        regex_patterns=[
                            r"(晴天|阴天|雨天|雪天|多云|晴|阴|雨|雪|雷|风)",
                            r"(sunny|cloudy|rainy|snowy|clear|overcast)"
                        ],
                        keywords=["天气", "weather"],
                        format_template="天气{condition}"
                    )
                ],
                priority=1
            ),
            
            # Price information extraction  
            ExtractionRule(
                intent_keywords=["价格", "price", "股价", "费用", "cost"],
                patterns=[
                    ExtractionPattern(
                        name="price_amount",
                        regex_patterns=[
                            r"(\d+(?:\.\d+)?)\s*元",
                            r"¥(\d+(?:\.\d+)?)",
                            r"\$(\d+(?:\.\d+)?)",
                            r"(\d+(?:\.\d+)?)\s*美元",
                            r"价格.*?(\d+(?:\.\d+)?)",
                            r"股价.*?(\d+(?:\.\d+)?)"
                        ],
                        keywords=["价格", "price", "元", "¥", "$"],
                        format_template="价格{price}元"
                    )
                ],
                priority=1
            ),
            
            # News/title extraction
            ExtractionRule(
                intent_keywords=["新闻", "news", "消息", "headline"],
                patterns=[
                    ExtractionPattern(
                        name="news_headline",
                        regex_patterns=[
                            r"^(.{10,100})$",  # Title-like text between 10-100 chars
                        ],
                        keywords=["新闻", "news"],
                        format_template="最新消息：{headline}"
                    )
                ],
                priority=1
            ),
            
            # Date/time extraction
            ExtractionRule(
                intent_keywords=["时间", "time", "日期", "date", "when"],
                patterns=[
                    ExtractionPattern(
                        name="datetime",
                        regex_patterns=[
                            r"(\d{4}年\d{1,2}月\d{1,2}日)",
                            r"(\d{1,2}月\d{1,2}日)",
                            r"(今天|明天|昨天)",
                            r"(\d{1,2}:\d{2})"
                        ],
                        keywords=["时间", "time", "日期"],
                        format_template="时间：{datetime}"
                    )
                ],
                priority=1
            )
        ]
    
    def extract_information(self, results: List[Dict], intent_keywords: List[str]) -> Optional[str]:
        """
        Extract information from search results based on intent keywords
        
        Args:
            results: List of search results with title, description, url
            intent_keywords: Keywords indicating user intent
            
        Returns:
            Extracted and formatted information string, or None if no match
        """
        if not results:
            return None
        
        # Find matching extraction rules
        matching_rules = self._find_matching_rules(intent_keywords)
        
        if not matching_rules:
            return self._extract_generic_summary(results)
        
        # Apply extraction patterns from matching rules
        for rule in sorted(matching_rules, key=lambda r: r.priority, reverse=True):
            extracted = self._apply_extraction_rule(results, rule)
            if extracted:
                return extracted
        
        # Fallback to generic summary
        return self._extract_generic_summary(results)
    
    def _find_matching_rules(self, intent_keywords: List[str]) -> List[ExtractionRule]:
        """Find extraction rules that match the intent keywords"""
        matching_rules = []
        
        for rule in self.extraction_rules:
            # Check if any intent keyword matches rule keywords
            if any(
                keyword.lower() in [rk.lower() for rk in rule.intent_keywords]
                for keyword in intent_keywords
            ):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _apply_extraction_rule(self, results: List[Dict], rule: ExtractionRule) -> Optional[str]:
        """Apply an extraction rule to search results"""
        # Combine all result text for analysis
        combined_texts = []
        for result in results[:3]:  # Check first 3 results
            title = result.get("title", "")
            desc = result.get("description", "")
            combined_texts.append(f"{title} {desc}")
        
        extracted_data = {}
        
        # Apply each pattern in the rule
        for pattern in rule.patterns:
            pattern_result = self._apply_pattern(combined_texts, pattern)
            if pattern_result:
                extracted_data.update(pattern_result)
        
        # Format the extracted data if we have any
        if extracted_data:
            return self._format_extracted_data(extracted_data, rule.patterns)
        
        return None
    
    def _apply_pattern(self, texts: List[str], pattern: ExtractionPattern) -> Optional[Dict[str, Any]]:
        """Apply a single extraction pattern to texts"""
        for text in texts:
            text_lower = text.lower()
            
            # Check if pattern keywords are present
            if not any(keyword.lower() in text_lower for keyword in pattern.keywords):
                continue
            
            # Try each regex pattern
            for regex_pattern in pattern.regex_patterns:
                try:
                    match = re.search(regex_pattern, text, re.IGNORECASE)
                    if match:
                        return self._extract_match_data(match, pattern)
                except re.error:
                    self.logger.warning(f"Invalid regex pattern: {regex_pattern}")
                    continue
        
        return None
    
    def _extract_match_data(self, match: re.Match, pattern: ExtractionPattern) -> Dict[str, Any]:
        """Extract data from a regex match based on pattern type"""
        groups = match.groups()
        
        if pattern.name == "temperature_range" and len(groups) >= 2:
            return {"temp1": groups[0], "temp2": groups[1]}
        elif pattern.name == "weather_condition" and len(groups) >= 1:
            return {"condition": groups[0]}
        elif pattern.name == "price_amount" and len(groups) >= 1:
            return {"price": groups[0]}
        elif pattern.name == "news_headline" and len(groups) >= 1:
            return {"headline": groups[0][:100]}  # Limit length
        elif pattern.name == "datetime" and len(groups) >= 1:
            return {"datetime": groups[0]}
        else:
            # Generic extraction - use first group or full match
            value = groups[0] if groups else match.group(0)
            return {"value": value}
    
    def _format_extracted_data(self, data: Dict[str, Any], patterns: List[ExtractionPattern]) -> str:
        """Format extracted data using pattern templates"""
        formatted_parts = []
        
        for pattern in patterns:
            try:
                # Try to format using pattern template
                formatted = pattern.format_template.format(**data)
                if formatted and formatted != pattern.format_template:  # Ensure substitution occurred
                    formatted_parts.append(formatted)
            except KeyError:
                # Template variables not available in data
                continue
        
        if formatted_parts:
            return "，".join(formatted_parts)
        
        # Fallback: use raw values
        if "value" in data:
            return str(data["value"])
        
        return "未能格式化提取的信息"
    
    def _extract_generic_summary(self, results: List[Dict]) -> str:
        """Extract generic summary when no specific patterns match"""
        if not results:
            return "未找到相关信息"
        
        first_result = results[0]
        title = first_result.get("title", "")
        desc = first_result.get("description", "")
        
        if desc and len(desc) > 50:
            return desc[:200] + ("..." if len(desc) > 200 else "")
        elif title:
            return f"相关信息：{title}"
        else:
            return "找到相关结果，但无法提取摘要信息"
    
    def add_extraction_rule(self, rule: ExtractionRule):
        """Add a new extraction rule (for extensibility)"""
        self.extraction_rules.append(rule)
    
    def get_supported_extraction_types(self) -> List[str]:
        """Get list of supported extraction types"""
        extraction_types = set()
        for rule in self.extraction_rules:
            extraction_types.update(rule.intent_keywords)
        return list(extraction_types)