from typing import Dict, Any, List, Optional
from src.plugins.base_website_plugin import BaseWebsitePlugin

class BingPlugin(BaseWebsitePlugin):
    """
    Bing 网站的特定插件。
    """

    def can_handle_url(self, url: str) -> bool:
        """
        判断当前插件是否能处理给定的URL。
        """
        return "bing.com" in url

    def get_site_name_mapping(self) -> Dict[str, str]:
        """
        返回 Bing 的中文名称到URL的映射。
        """
        return {
            "必应": "https://www.bing.com",
            "bing": "https://www.bing.com",
        }

    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为 Bing 网站构建搜索动作的步骤列表。
        """
        return [
            {"action": "wait", "selector": "input[name='q'], #sb_form_q", "timeout": 5000, "description": "等待Bing搜索框出现"},
            {"action": "fill", "selector": "input[name='q'], #sb_form_q", "value": query, "description": f"在Bing搜索框输入 '{query}'"},
            {"action": "click", "selector": "#sb_form_go, input[type='submit'][value='搜索']", "description": "点击Bing搜索按钮"}
        ]
