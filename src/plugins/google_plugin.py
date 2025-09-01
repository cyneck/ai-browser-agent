from typing import Dict, Any, List, Optional
from src.plugins.base_website_plugin import BaseWebsitePlugin

class GooglePlugin(BaseWebsitePlugin):
    """
    Google 网站的特定插件。
    """

    def can_handle_url(self, url: str) -> bool:
        """
        判断当前插件是否能处理给定的URL。
        """
        return "google." in url # Use "google." to match google.com, google.co.uk, etc.

    def get_site_name_mapping(self) -> Dict[str, str]:
        """
        返回 Google 的中文名称到URL的映射。
        """
        return {
            "谷歌": "https://www.google.com",
            "google": "https://www.google.com",
        }

    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为 Google 网站构建搜索动作的步骤列表。
        使用 Enter 键而不是点击按钮，更符合用户习惯。
        """
        return [
            {"action": "wait", "selector": "textarea[name='q'], input[name='q']", "timeout": 5000, "description": "等待Google搜索框出现"},
            {"action": "fill", "selector": "textarea[name='q'], input[name='q']", "value": query, "description": f"在Google搜索框输入 '{query}'"},
            {"action": "key", "selector": "textarea[name='q'], input[name='q']", "value": "Enter", "description": "按回车键执行搜索"},
            {"action": "wait", "value": 3000, "description": "等待搜索结果加载"}
        ]
