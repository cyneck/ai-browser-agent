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
    
    # New enhanced intent types
    SEARCH = "search"                       # User wants to search for information
    COMPARISON = "comparison"               # User wants to compare items/options
    MONITORING = "monitoring"               # User wants to monitor changes/updates
    AUTOMATION = "automation"               # User wants to automate a workflow
    ANALYSIS = "analysis"                   # User wants data analysis/insights
    TRANSLATION = "translation"             # User wants content translation
    SOCIAL_INTERACTION = "social_interaction" # User wants to interact with social media
    SHOPPING = "shopping"                   # User wants to shop/purchase items
    ENTERTAINMENT = "entertainment"         # User wants entertainment content
    EDUCATION = "education"                 # User wants educational content
    
    # Multi-intent support
    MULTI_INTENT = "multi_intent"           # User has multiple intents in one request
    
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
    
    # Enhanced fields for multi-intent and context support
    secondary_intents: List[IntentType] = None  # For multi-intent scenarios
    context_factors: Dict[str, Any] = None      # Context that influenced classification
    confidence_breakdown: Dict[IntentType, float] = None  # Confidence for each intent
    suggested_actions: List[str] = None         # Suggested follow-up actions


class IntentClassifier:
    """Classifies user intent to determine appropriate response strategy"""
    
    def __init__(self):
        self.logger = get_logger()
        
        # Enhanced intent patterns for classification
        self.intent_patterns = {
            IntentType.SUMMARY_INFO: [
                r"(\w+).*?(怎么样|如何|情况|多少|现在|是什么|怎样)",  # Generic question patterns
                r"(简单|简要|概况|摘要).*?(介绍|说明|信息)",
                r"(今天|现在|当前).*?(是什么|怎样|如何)",
                r"\w+\s+(today|now|current)",  # Generic English patterns
                r"(today|now)\s+\w+",  # Alternative English pattern
                r"what.*?is.*?",  # English question patterns
                r"how.*?is.*?",
                r"(告诉我|给我说说).*?(关于|about)",
                r"(简单了解|快速了解).*?"
            ],
            
            IntentType.DETAILED_INFO: [
                r"(详细|complete|全面|comprehensive).*?(信息|内容|资料)",
                r"(完整|所有|全部).*?(介绍|说明|内容)",
                r"(深入|thorough).*?(了解|分析)",
                r"(更多|more).*?(信息|details)",
                r"(具体|详尽|深度).*?(分析|解释|说明)",
                r"(完整版|详细版).*?"
            ],
            
            IntentType.STRUCTURED_DATA: [
                r"(表格|table|列表|list).*?(数据|信息)",
                r"(结构化|structured).*?(数据|提取)",
                r"(价格|price).*?(对比|比较|列表)",
                r"(统计|statistics|数据分析)",
                r"(导出|export).*?(数据|excel|csv)",
                r"(整理成|格式化为).*?(表格|列表)",
                r"(排序|排列|分类).*?(数据|信息)"
            ],
            
            IntentType.FULL_PAGE_CONTENT: [
                r"(整个|全部|complete).*?(页面|网页|html)",
                r"(所有|all).*?(内容|content)",
                r"(保存|save).*?(页面|网页)",
                r"(下载|download).*?(页面|html)",
                r"(完整|全文).*?(内容|文本)"
            ],
            
            IntentType.SPECIFIC_ELEMENT: [
                r"(提取|extract).*?(特定|specific|某个).*?(元素|element)",
                r"(获取|get).*?(标题|title|链接|link|图片|image)",
                r"(找到|find).*?(按钮|button|输入框|input)",
                r"(选择器|selector|元素定位)",
                r"(定位|locate).*?(元素|控件)"
            ],
            
            IntentType.SCREENSHOT: [
                r"(截图|screenshot|capture)",
                r"(拍照|photo|图像|image).*?(页面|screen)",
                r"(保存|save).*?(屏幕|截图)",
                r"(截取|capture).*?(当前|页面)"
            ],
            
            IntentType.NAVIGATION: [
                r"(打开|open|访问|visit|go to)",
                r"(导航|navigate).*?(到|至)",
                r"(跳转|jump|redirect)",
                r"(浏览|browse)",
                r"(进入|enter).*?(网站|页面)",
                r"(切换到|switch to).*?"
            ],
            
            IntentType.FORM_INTERACTION: [
                r"(填写|fill|输入|input).*?(表单|form)",
                r"(登录|login|注册|register)",
                r"(提交|submit|发送|send)",
                r"(点击|click).*?(按钮|button|链接|link)",
                r"(选择|select).*?(选项|option)",
                r"(勾选|check).*?(复选框|checkbox)"
            ],
            
            # New enhanced intent patterns
            IntentType.SEARCH: [
                r"(搜索|search|查找|find).*?",
                r"(检索|retrieve).*?(信息|内容)",
                r"(查询|query).*?",
                r"(寻找|look for).*?",
                r"(搜搜|百度|谷歌|google).*?"
            ],
            
            IntentType.COMPARISON: [
                r"(比较|compare|对比).*?",
                r"(哪个更好|which is better)",
                r"(差异|difference|区别).*?",
                r"(优缺点|pros and cons)",
                r"(对比分析|comparative analysis)"
            ],
            
            IntentType.MONITORING: [
                r"(监控|monitor|观察|watch).*?",
                r"(跟踪|track).*?(变化|changes)",
                r"(实时|real-time).*?(更新|update)",
                r"(定期检查|periodic check)",
                r"(状态监测|status monitoring)"
            ],
            
            IntentType.AUTOMATION: [
                r"(自动|auto|automatic).*?(执行|perform)",
                r"(批量|batch).*?(操作|operation)",
                r"(定时|scheduled).*?(任务|task)",
                r"(工作流|workflow).*?",
                r"(脚本|script).*?(运行|run)"
            ],
            
            IntentType.ANALYSIS: [
                r"(分析|analyze|analysis).*?",
                r"(统计|statistics).*?(数据|data)",
                r"(趋势|trend).*?(分析|analysis)",
                r"(洞察|insights).*?",
                r"(报告|report).*?(生成|generate)"
            ],
            
            IntentType.TRANSLATION: [
                r"(翻译|translate|translation).*?",
                r"(转换|convert).*?(语言|language)",
                r"(中英文|chinese english).*?",
                r"(多语言|multilingual).*?"
            ],
            
            IntentType.SOCIAL_INTERACTION: [
                r"(社交|social).*?(媒体|media)",
                r"(微博|weibo|twitter).*?",
                r"(朋友圈|moments).*?",
                r"(点赞|like|评论|comment).*?",
                r"(分享|share).*?(到|to)"
            ],
            
            IntentType.SHOPPING: [
                r"(购买|buy|purchase).*?",
                r"(购物|shopping).*?",
                r"(价格|price).*?(查询|check)",
                r"(商品|product).*?(信息|info)",
                r"(下单|order).*?",
                r"(加购物车|add to cart)"
            ],
            
            IntentType.ENTERTAINMENT: [
                r"(娱乐|entertainment).*?",
                r"(视频|video).*?(观看|watch)",
                r"(音乐|music).*?(播放|play)",
                r"(游戏|game).*?",
                r"(电影|movie).*?(推荐|recommend)"
            ],
            
            IntentType.EDUCATION: [
                r"(学习|learn|study).*?",
                r"(教育|education).*?",
                r"(课程|course).*?",
                r"(教程|tutorial).*?",
                r"(知识|knowledge).*?(获取|acquire)"
            ]
        }
        
        # Response format indicators
        self.format_patterns = {
            "json": [r"json格式", r"结构化", r"structured"],
            "table": [r"表格", r"列表", r"table", r"list"],
            "markdown": [r"markdown", r"格式化", r"formatted"],
            "natural_language": [r"自然语言", r"简单回答", r"直接告诉我"]
        }

    def classify_intent(self, user_text: str, page_data: Dict[str, Any] = None, 
                       conversation_history: List[Dict[str, str]] = None) -> IntentResult:
        """
        Enhanced classify user intent with context awareness and multi-intent support
        
        Args:
            user_text: User's natural language input
            page_data: Current page data for context
            conversation_history: Previous conversation for context
            
        Returns:
            IntentResult with classified intent and parameters
        """
        user_text_lower = user_text.lower()
        
        # Score each intent type and extract domain keywords
        intent_scores = {}
        matched_keywords = []
        domain_keywords = self._extract_domain_keywords(user_text_lower)
        
        # Enhanced pattern matching with context weighting
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, user_text_lower)
                if matches:
                    base_score = len(matches) * 1.0
                    # Apply context weighting
                    context_weight = self._get_context_weight(intent_type, page_data, conversation_history)
                    score += base_score * context_weight
                    matched_keywords.extend([m if isinstance(m, str) else m[0] for m in matches])
            
            if score > 0:
                intent_scores[intent_type] = score
        
        # Combine pattern-matched keywords with domain keywords
        all_keywords = list(set(matched_keywords + domain_keywords))
        
        # Determine response format preference
        response_format = self._determine_response_format(user_text_lower)
        
        # Enhanced intent selection with multi-intent detection
        primary_intent, confidence, secondary_intents = self._select_intents(
            intent_scores, user_text_lower, page_data
        )
        
        # Extract additional parameters
        additional_params = self._extract_additional_params(user_text, primary_intent)
        
        # Extract context factors that influenced classification
        context_factors = self._extract_context_factors(page_data, conversation_history)
        
        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(primary_intent, secondary_intents, page_data)
        
        return IntentResult(
            intent_type=primary_intent,
            confidence=confidence,
            keywords=all_keywords,
            response_format=response_format,
            additional_params=additional_params,
            secondary_intents=secondary_intents,
            context_factors=context_factors,
            confidence_breakdown=intent_scores,
            suggested_actions=suggested_actions
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
    
    def _extract_domain_keywords(self, user_text: str) -> List[str]:
        """Extract domain-specific keywords from user text"""
        domain_keywords = []
        
        # Weather related keywords
        weather_keywords = ["天气", "temperature", "weather", "温度", "气温", "气候"]
        if any(keyword in user_text for keyword in weather_keywords):
            domain_keywords.extend(weather_keywords)
        
        # Price related keywords
        price_keywords = ["价格", "price", "股价", "费用", "cost", "元", "¥", "$"]
        if any(keyword in user_text for keyword in price_keywords):
            domain_keywords.extend(price_keywords)
        
        # News related keywords
        news_keywords = ["新闻", "news", "消息", "headline"]
        if any(keyword in user_text for keyword in news_keywords):
            domain_keywords.extend(news_keywords)
        
        # Time related keywords
        time_keywords = ["时间", "time", "日期", "date", "when"]
        if any(keyword in user_text for keyword in time_keywords):
            domain_keywords.extend(time_keywords)
        
        return domain_keywords
    
    def _get_context_weight(self, intent_type: IntentType, page_data: Dict[str, Any], 
                           conversation_history: List[Dict[str, str]]) -> float:
        """Calculate context weight for intent scoring"""
        weight = 1.0
        
        if not page_data:
            return weight
            
        current_url = page_data.get("url", "")
        page_type = page_data.get("page_type", "")
        
        # Boost search intent on search engine pages
        if intent_type == IntentType.SEARCH:
            if any(domain in current_url for domain in ["baidu.com", "google.com", "bing.com"]):
                weight *= 1.5
        
        # Boost shopping intent on e-commerce pages
        elif intent_type == IntentType.SHOPPING:
            if any(domain in current_url for domain in ["taobao.com", "tmall.com", "jd.com", "amazon.com"]):
                weight *= 1.5
        
        # Boost social interaction intent on social media pages
        elif intent_type == IntentType.SOCIAL_INTERACTION:
            if any(domain in current_url for domain in ["weibo.com", "xiaohongshu.com", "twitter.com", "facebook.com"]):
                weight *= 1.5
        
        # Boost form interaction intent on pages with forms
        elif intent_type == IntentType.FORM_INTERACTION:
            if page_data.get("has_forms", False):
                weight *= 1.3
        
        # Consider conversation history for context continuity
        if conversation_history:
            recent_intents = self._extract_recent_intents(conversation_history)
            if intent_type in recent_intents:
                weight *= 1.2  # Slight boost for intent continuity
        
        return weight
    
    def _determine_response_format(self, user_text: str) -> str:
        """Enhanced response format determination"""
        response_format = "natural_language"
        
        # Check for explicit format requests
        for fmt, patterns in self.format_patterns.items():
            if any(re.search(pattern, user_text) for pattern in patterns):
                response_format = fmt
                break
        
        # Infer format from intent patterns
        if any(word in user_text for word in ["对比", "比较", "列表", "排序"]):
            response_format = "table"
        elif any(word in user_text for word in ["详细", "完整", "深入"]):
            response_format = "detailed_text"
        elif any(word in user_text for word in ["简单", "简要", "快速"]):
            response_format = "natural_language"
        
        return response_format
    
    def _select_intents(self, intent_scores: Dict[IntentType, float], user_text: str, 
                       page_data: Dict[str, Any]) -> tuple:
        """Enhanced intent selection with multi-intent detection"""
        if not intent_scores:
            # Default fallback based on context
            primary_intent = self._fallback_intent_detection(user_text, page_data)
            return primary_intent, 0.5, []
        
        # Sort intents by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, primary_score = sorted_intents[0]
        
        # Calculate confidence
        total_score = sum(intent_scores.values())
        confidence = min(primary_score / total_score, 1.0) if total_score > 0 else 0.5
        
        # Detect secondary intents (multi-intent scenarios)
        secondary_intents = []
        threshold = primary_score * 0.6  # Secondary intents must be at least 60% of primary
        
        for intent_type, score in sorted_intents[1:]:
            if score >= threshold and len(secondary_intents) < 3:  # Limit to 3 secondary intents
                secondary_intents.append(intent_type)
        
        # Check for explicit multi-intent patterns
        if self._has_multi_intent_patterns(user_text):
            if not secondary_intents:
                # If we detected multi-intent patterns but no secondary intents, 
                # mark as multi-intent with lower confidence
                primary_intent = IntentType.MULTI_INTENT
                confidence *= 0.8
        
        return primary_intent, confidence, secondary_intents
    
    def _has_multi_intent_patterns(self, user_text: str) -> bool:
        """Detect patterns indicating multiple intents in one request"""
        multi_intent_patterns = [
            r"(然后|接着|之后|再|and then|after that)",
            r"(同时|并且|还要|also|as well)",
            r"(另外|此外|besides|additionally)",
            r"(以及|和|以及|and|plus)"
        ]
        
        return any(re.search(pattern, user_text) for pattern in multi_intent_patterns)
    
    def _extract_recent_intents(self, conversation_history: List[Dict[str, str]]) -> List[IntentType]:
        """Extract recent intents from conversation history"""
        recent_intents = []
        
        # Look at last 3 exchanges
        for entry in conversation_history[-6:]:  # 3 exchanges = 6 entries (user + assistant)
            if entry.get("role") == "assistant":
                content = entry.get("content", "")
                # Try to extract intent from assistant response
                # This is a simplified approach - in practice, you might store intent metadata
                if "搜索" in content or "search" in content.lower():
                    recent_intents.append(IntentType.SEARCH)
                elif "导航" in content or "navigate" in content.lower():
                    recent_intents.append(IntentType.NAVIGATION)
                # Add more intent extraction logic as needed
        
        return recent_intents
    
    def _extract_context_factors(self, page_data: Dict[str, Any], 
                                conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract context factors that influenced classification"""
        factors = {}
        
        if page_data:
            factors["current_url"] = page_data.get("url", "")
            factors["page_type"] = page_data.get("page_type", "")
            factors["has_forms"] = page_data.get("has_forms", False)
            factors["has_search_box"] = bool(page_data.get("search_elements"))
        
        if conversation_history:
            factors["conversation_length"] = len(conversation_history)
            factors["recent_topics"] = self._extract_recent_topics(conversation_history)
        
        return factors
    
    def _extract_recent_topics(self, conversation_history: List[Dict[str, str]]) -> List[str]:
        """Extract recent topics from conversation history"""
        topics = []
        
        for entry in conversation_history[-4:]:  # Last 2 exchanges
            if entry.get("role") == "user":
                content = entry.get("content", "")
                # Extract key topics/entities
                # This is simplified - could use NER or more sophisticated topic extraction
                words = content.split()
                topics.extend([word for word in words if len(word) > 2])
        
        return list(set(topics))[:5]  # Return top 5 unique topics
    
    def _generate_suggested_actions(self, primary_intent: IntentType, 
                                   secondary_intents: List[IntentType], 
                                   page_data: Dict[str, Any]) -> List[str]:
        """Generate suggested follow-up actions based on intent"""
        suggestions = []
        
        # Primary intent suggestions
        if primary_intent == IntentType.SEARCH:
            suggestions.extend(["refine_search", "filter_results", "sort_results"])
        elif primary_intent == IntentType.NAVIGATION:
            suggestions.extend(["bookmark_page", "share_link", "take_screenshot"])
        elif primary_intent == IntentType.SHOPPING:
            suggestions.extend(["compare_prices", "read_reviews", "add_to_cart"])
        elif primary_intent == IntentType.ANALYSIS:
            suggestions.extend(["export_data", "create_chart", "generate_report"])
        
        # Secondary intent suggestions
        for intent in secondary_intents:
            if intent == IntentType.SCREENSHOT:
                suggestions.append("take_screenshot")
            elif intent == IntentType.STRUCTURED_DATA:
                suggestions.append("export_structured_data")
        
        # Context-based suggestions
        if page_data:
            current_url = page_data.get("url", "")
            if "search" in current_url:
                suggestions.append("refine_search_query")
            if page_data.get("has_forms"):
                suggestions.append("auto_fill_form")
        
        return list(set(suggestions))[:5]  # Return top 5 unique suggestions