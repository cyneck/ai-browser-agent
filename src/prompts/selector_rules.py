#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Selector Rules

Contains all rules, principles, and best practices for generating CSS selectors
used in web automation. These rules are based on reliability, precision, and maintainability.
"""

from typing import List, Dict


class SelectorRules:
    """Container for selector generation rules and best practices"""
    
    def __init__(self):
        """Initialize selector rules"""
        pass
    
    def get_selector_principles(self) -> str:
        """Get the complete selector generation principles text
        
        Returns:
            Complete selector principles as formatted string
        """
        return """
        选择器生成原则（按优先级排序）：
        1. **优先使用稳定的唯一标识符**：
           - ID选择器：#submit-button, #search-input
           - name属性：input[name='username'], form[name='loginForm']
           - data-*属性：[data-testid='login-btn'], [data-action='submit']
        
        2. **基于语义和内容的选择器**：
           - 精确文本内容：a:has-text('登录'), button:has-text('搜索')
           - aria-label：[aria-label='搜索'], [aria-label='关闭']
           - 语义标签：button, input[type='submit'], nav
        
        3. **属性部分匹配**：
           - href部分匹配：a[href*='login'], a[href*='/tech']
           - class部分匹配：[class*='btn'], [class*='search']
           - placeholder匹配：[placeholder*='用户名']
        
        4. **提供多重备选策略时要确保精确性**：
           - 使用逗号分隔的多个选择器："a:has-text('科技'), a[href*='/tech/'], [data-nav='tech']"
           - 确保每个备选选择器都足够具体，避免匹配多个元素
           - 如果文本选择器可能匹配多个元素，要结合其他属性提高精确性
        
        5. **避免脆弱的选择器**：
           - 避免纯位置选择器：:nth-child(), :nth-of-type()
           - 避免深层嵌套：body > div > section > nav > ul > li > a
           - 避免过于宽泛的类选择器：.nav-link（会匹配多个元素）
           - 避免不完整的属性匹配：[class*='nav']（太宽泛）
        """
    
    def get_precision_guidelines(self) -> str:
        """Get selector precision guidelines
        
        Returns:
            Precision guidelines as formatted string
        """
        return """
        **重要：确保选择器精确性**
        - 每个选择器都应该尽可能匹配唯一元素
        - 当使用has-text()时，确保文本内容具有唯一性
        - 备选选择器应该同样精确，不要为了容错而牺牲精确性
        - 如果元素确实需要组合定位，优先使用语义属性组合
        """
    
    def get_selector_priority_list(self) -> List[Dict[str, str]]:
        """Get ordered list of selector types by priority
        
        Returns:
            List of dictionaries containing selector type info
        """
        return [
            {
                "priority": 1,
                "category": "稳定的唯一标识符",
                "types": ["ID选择器", "name属性", "data-*属性"],
                "examples": ["#submit-button", "input[name='username']", "[data-testid='login-btn']"],
                "reliability": "最高"
            },
            {
                "priority": 2,
                "category": "基于语义和内容的选择器",
                "types": ["精确文本内容", "aria-label", "语义标签"],
                "examples": ["a:has-text('登录')", "[aria-label='搜索']", "button"],
                "reliability": "高"
            },
            {
                "priority": 3,
                "category": "属性部分匹配",
                "types": ["href部分匹配", "class部分匹配", "placeholder匹配"],
                "examples": ["a[href*='login']", "[class*='btn']", "[placeholder*='用户名']"],
                "reliability": "中"
            }
        ]
    
    def get_fragile_selectors(self) -> List[Dict[str, str]]:
        """Get list of fragile selectors to avoid
        
        Returns:
            List of fragile selector patterns with explanations
        """
        return [
            {
                "pattern": ":nth-child(), :nth-of-type()",
                "category": "位置选择器",
                "reason": "页面结构变化时容易失效",
                "example": "div:nth-child(3)"
            },
            {
                "pattern": "body > div > section > nav > ul > li > a",
                "category": "深层嵌套",
                "reason": "依赖完整的DOM结构，脆弱性高",
                "example": "body > div > section > nav > ul > li > a"
            },
            {
                "pattern": ".nav-link",
                "category": "过于宽泛的类选择器",
                "reason": "可能匹配多个元素，缺乏精确性",
                "example": ".nav-link"
            },
            {
                "pattern": "[class*='nav']",
                "category": "不完整的属性匹配",
                "reason": "匹配范围过广，容易误选",
                "example": "[class*='nav']"
            }
        ]
    
    def get_best_practices(self) -> List[str]:
        """Get selector best practices as a list
        
        Returns:
            List of best practice guidelines
        """
        return [
            "优先使用ID选择器，如果元素有唯一ID",
            "使用data-testid或data-*属性进行测试友好的选择",
            "结合语义标签和属性提高选择器稳定性",
            "避免依赖CSS类名，除非它们是功能性的",
            "使用has-text()时确保文本的唯一性",
            "提供多个备选选择器时，保持同等的精确性",
            "测试选择器确保只匹配目标元素",
            "优先选择aria-label等可访问性属性",
            "避免使用可能变化的样式相关选择器",
            "考虑选择器在不同页面状态下的稳定性"
        ]
    
    def get_selector_examples(self) -> Dict[str, List[str]]:
        """Get examples of good and bad selectors
        
        Returns:
            Dictionary with good and bad selector examples
        """
        return {
            "good_examples": [
                "#search-input",
                "input[name='username']",
                "[data-testid='login-button']",
                "button:has-text('登录')",
                "[aria-label='搜索']",
                "a[href*='/tech/']:has-text('科技')",
                "input[type='submit'][value='提交']"
            ],
            "bad_examples": [
                ".nav-link",
                "div:nth-child(3)",
                "body > div > nav > ul > li",
                "[class*='nav']",
                ".button.blue.large",
                "div div div a",
                "table tr:first-child td"
            ],
            "improved_alternatives": {
                ".nav-link": "a[role='menuitem'] 或 nav a:has-text('具体文本')",
                "div:nth-child(3)": "[data-section='content'] 或 .main-content",
                "body > div > nav > ul > li": "nav li:has-text('菜单项文本')",
                "[class*='nav']": "[data-nav='specific-item'] 或 nav a"
            }
        }
    
    def validate_selector_precision(self, selector: str) -> Dict[str, any]:
        """Validate if a selector follows precision guidelines
        
        Args:
            selector: CSS selector string to validate
            
        Returns:
            Validation result with score and recommendations
        """
        issues = []
        score = 100
        
        # Check for fragile patterns
        fragile_patterns = [
            (":nth-child", "使用位置选择器", 30),
            (":nth-of-type", "使用位置选择器", 30), 
            ("body >", "深层嵌套选择器", 20),
            (" > ", "过度依赖层级关系", 10)
        ]
        
        for pattern, issue, penalty in fragile_patterns:
            if pattern in selector:
                issues.append(issue)
                score -= penalty
        
        # Check for precision
        if selector.count(" ") > 3:
            issues.append("选择器过于复杂")
            score -= 15
        
        # Positive indicators
        positive_patterns = ["#", "[data-", ":has-text", "[aria-label"]
        for pattern in positive_patterns:
            if pattern in selector:
                score += 10
                break
        
        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "recommendation": "good" if score >= 80 else "needs_improvement" if score >= 60 else "poor"
        }
    
    def generate_selector_documentation(self) -> str:
        """Generate complete documentation for selector rules
        
        Returns:
            Complete selector rules documentation
        """
        doc = f"""
# CSS选择器生成规则

{self.get_selector_principles()}

{self.get_precision_guidelines()}

## 最佳实践清单
"""
        for i, practice in enumerate(self.get_best_practices(), 1):
            doc += f"{i}. {practice}\n"
        
        doc += "\n## 选择器示例\n### 推荐的选择器\n"
        for example in self.get_selector_examples()["good_examples"]:
            doc += f"- `{example}`\n"
        
        doc += "\n### 应避免的选择器\n"
        for example in self.get_selector_examples()["bad_examples"]:
            doc += f"- `{example}` ❌\n"
        
        return doc