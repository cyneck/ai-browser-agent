from typing import Dict, Any, List, Optional
from typing import Dict, List, Any, Optional
from src.plugins.base_website_plugin import BaseWebsitePlugin
from src.common.config import get_config

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
        但可以通过配置XIAOHONGSHU_DIRECT_ACCESS来禁用访问限制。
        """
        # 检查是否配置了直接访问小红书
        direct_access = get_config("XIAOHONGSHU_DIRECT_ACCESS", "false").lower() == "true"
        if direct_access:
            return False
            
        return True

    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为小红书网站构建搜索动作的步骤列表。
        由于小红书存在网络访问限制（错误代码300012），使用多重回退策略。
        """
        # 根据用户需求，构建完整的操作流程：
        # 1. 导航到小红书网站
        # 2. 等待用户登录（扫码或输入账号密码）
        # 3. 等待搜索框出现
        # 4. 在搜索框输入查询词
        # 5. 按回车键执行搜索
        return [
            {"action": "navigate", "value": "https://www.xiaohongshu.com", "description": "导航到小红书网站"},
            {"action": "wait_for_login", "description": "等待用户手动登录"},
            {"action": "wait", "selector": "input[placeholder*='搜索']", "timeout": 10000, "description": "等待小红书搜索框出现"},
            {"action": "fill", "selector": "input[placeholder*='搜索']", "value": query, "description": f"在小红书搜索框输入 '{query}'"},
            {"action": "key", "selector": "input[placeholder*='搜索']", "value": "Enter", "description": "按回车键执行搜索"}
        ]
    
    def build_fallback_strategies(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        构建小红书搜索的多重回退策略，应对网络访问限制。
        
        Args:
            query: 搜索关键词
            
        Returns:
            包含多个回退策略的步骤列表
        """
        # 使用通用的搜索引擎回退策略构建器
        from src.common.search_engines import build_search_fallback_strategy
        search_strategies = build_search_fallback_strategy("xiaohongshu.com", query)
        
        # 添加小红书移动版策略
        mobile_strategy = {
            "description": "策略: 尝试访问小红书移动版",
            "steps": [
                {"action": "navigate", "value": "https://m.xiaohongshu.com", "description": "尝试访问小红书移动版"},
                {"action": "wait", "value": 3000, "description": "等待页面加载"},
                {"action": "wait", "selector": "input[placeholder*='搜索'], .search-input", "timeout": 8000, "description": "等待移动版搜索框"},
                {"action": "fill", "selector": "input[placeholder*='搜索'], .search-input", "value": query, "description": f"在移动版搜索: {query}"},
                {"action": "key", "selector": "input[placeholder*='搜索'], .search-input", "value": "Enter", "description": "按回车键执行搜索"}
            ]
        }
        
        return search_strategies + [mobile_strategy]
    
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