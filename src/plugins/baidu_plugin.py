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
        支持多种搜索框选择器，使用 Enter 键执行搜索。
        """
        return [
            {"action": "wait", "selector": "#kw, input[name='wd'], #chat-textarea", "timeout": 5000, "description": "等待百度搜索框出现"},
            {"action": "fill", "selector": "#kw, input[name='wd'], #chat-textarea", "value": query, "description": f"在百度搜索框输入 '{query}'"},
            {"action": "key", "selector": "#kw, input[name='wd'], #chat-textarea", "value": "Enter", "description": "按回车键执行搜索"},
            {"action": "wait", "value": 3000, "description": "等待搜索结果加载"}
        ]