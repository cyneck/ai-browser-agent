from typing import Dict, Any, List, Optional
from src.plugins.base_website_plugin import BaseWebsitePlugin

class BaiduPlugin(BaseWebsitePlugin):
    """
    Baidu 网站的特定插件。
    """

    def can_handle_url(self, url: str) -> bool:
        """
        判断当前插件是否能处理给定的URL。
        """
        return "baidu.com" in url

    def get_site_name_mapping(self) -> Dict[str, str]:
        """
        返回 Baidu 的中文名称到URL的映射。
        """
        return {
            "百度": "https://www.baidu.com",
            "百度网站": "https://www.baidu.com",
            "baidu": "https://www.baidu.com",
        }

    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为 Baidu 网站构建搜索动作的步骤列表。
        使用智能选择器策略，优先选择传统搜索框，避免多元素匹配问题。
        """
        return [
            {"action": "wait", "selector": "#kw, #chat-textarea", "timeout": 5000, "description": "等待百度搜索框出现"},
            {"action": "smart_fill", "query": query, "description": f"智能填充百度搜索框: '{query}'"},
            {"action": "smart_submit", "description": "智能提交搜索"},
            {"action": "wait", "value": 3000, "description": "等待搜索结果加载"}
        ]