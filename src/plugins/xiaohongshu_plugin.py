from typing import Dict, Any, List, Optional
from src.plugins.base_website_plugin import BaseWebsitePlugin

class XiaohongshuPlugin(BaseWebsitePlugin):
    """
    小红书网站的特定插件。
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

    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为小红书网站构建搜索动作的步骤列表。
        """
        return [
            {"action": "wait_for_login", "description": "等待用户手动登录"},
            {"action": "wait", "selector": "input[placeholder*='搜索']", "timeout": 10000, "description": "等待小红书搜索框出现"},
            {"action": "fill", "selector": "input[placeholder*='搜索']", "value": query, "description": f"在小红书搜索框输入 '{query}'"},
            {"action": "click", "selector": "button:has-text('搜索')", "description": "点击搜索按钮"}
        ]
