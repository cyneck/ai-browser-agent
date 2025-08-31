from typing import Dict, Any, List, Optional
from typing import Dict, List, Any, Optional
from src.plugins.base_website_plugin import BaseWebsitePlugin

class XiaohongshuPlugin(BaseWebsitePlugin):
    """
    小红书网站的特定插件。
    支持网络访问限制的多重回退策略。
    """

    def can_handle_url(self, url: str) -> bool:
        """
        判断当前插件是否能处理给定的URL。
        """
        return "xiaohongshu.com" in url

    def get_site_name_mapping(self) -> Dict[str, str]:
        """
        返回小红书的中文名称到URL的映射。
        """
        return {
            "小红书": "https://www.xiaohongshu.com",
        }
    
    def has_access_restrictions(self) -> bool:
        """
        小红书存在网络访问限制（错误代码300012）。
        """
        return True

    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为小红书网站构建搜索动作的步骤列表。
        由于小红书存在网络访问限制（错误代码300012），使用多重回退策略。
        """
        return [
            {"action": "wait_for_login", "description": "等待用户手动登录"},
            {"action": "wait", "selector": "input[placeholder*='搜索']", "timeout": 10000, "description": "等待小红书搜索框出现"},
            {"action": "fill", "selector": "input[placeholder*='搜索']", "value": query, "description": f"在小红书搜索框输入 '{query}'"},
            {"action": "click", "selector": "button:has-text('搜索')", "description": "点击搜索按钮"}
        ]
    
    def build_fallback_strategies(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        构建小红书搜索的多重回退策略，应对网络访问限制。
        
        Args:
            query: 搜索关键词
            
        Returns:
            包含多个回退策略的步骤列表
        """
        return [
            {
                "description": "策略1: 通过百度搜索小红书内容",
                "steps": [
                    {"action": "navigate", "value": "https://www.baidu.com", "description": "导航到百度"},
                    {"action": "wait", "selector": "#kw", "timeout": 5000, "description": "等待百度搜索框"},
                    {"action": "fill", "selector": "#kw", "value": f"site:xiaohongshu.com {query}", "description": f"搜索小红书站内内容: {query}"},
                    {"action": "click", "selector": "#su", "description": "点击百度搜索"}
                ]
            },
            {
                "description": "策略2: 通过必应搜索小红书内容", 
                "steps": [
                    {"action": "navigate", "value": "https://www.bing.com", "description": "导航到必应"},
                    {"action": "wait", "selector": "input[name='q']", "timeout": 5000, "description": "等待必应搜索框"},
                    {"action": "fill", "selector": "input[name='q']", "value": f"小红书 {query}", "description": f"搜索小红书相关内容: {query}"},
                    {"action": "click", "selector": "#sb_form_go", "description": "点击必应搜索"}
                ]
            },
            {
                "description": "策略3: 尝试访问小红书移动版",
                "steps": [
                    {"action": "navigate", "value": "https://m.xiaohongshu.com", "description": "尝试访问小红书移动版"},
                    {"action": "wait", "value": 3000, "description": "等待页面加载"},
                    {"action": "wait", "selector": "input[placeholder*='搜索'], .search-input", "timeout": 8000, "description": "等待移动版搜索框"},
                    {"action": "fill", "selector": "input[placeholder*='搜索'], .search-input", "value": query, "description": f"在移动版搜索: {query}"},
                    {"action": "click", "selector": ".search-btn, button:has-text('搜索')", "description": "点击移动版搜索按钮"}
                ]
            }
        ]
    
    def build_fallback_search_strategies(self, query: str) -> List[Dict[str, Any]]:
        """
        构建小红书搜索的多重回退策略，应对网络访问限制。
        这是为了兼容测试代码中使用的方法名。
        
        Args:
            query: 搜索关键词
            
        Returns:
            包含多个回退策略的列表，每个策略包含description和steps
        """
        return self.build_fallback_strategies(query)
