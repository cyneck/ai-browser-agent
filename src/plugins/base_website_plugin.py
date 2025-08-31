from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseWebsitePlugin(ABC):
    """
    所有网站特定插件的抽象基类。
    定义了插件必须实现的方法，以提供网站特定的行为。
    """

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """
        判断当前插件是否能处理给定的URL。
        
        Args:
            url: 当前页面的URL。
            
        Returns:
            如果插件能处理该URL，则返回True，否则返回False。
        """
        pass

    @abstractmethod
    def get_site_name_mapping(self) -> Dict[str, str]:
        """
        返回该网站的中文名称到URL的映射。
        
        Returns:
            一个字典，键为网站的中文名称，值为对应的URL。
        """
        pass

    @abstractmethod
    def build_search_action(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为该网站构建搜索动作的步骤列表。
        
        Args:
            query: 用户输入的搜索关键词。
            
        Returns:
            一个包含搜索步骤的列表，如果无法构建则返回None。
        """
        pass
    
    def has_access_restrictions(self) -> bool:
        """
        检查该网站是否存在访问限制。
        
        Returns:
            如果网站存在访问限制则返回True，否则返回False。
        """
        return False
    
    def build_fallback_strategies(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        为存在访问限制的网站构建回退策略。
        
        Args:
            query: 用户输入的搜索关键词。
            
        Returns:
            包含多个回退策略的列表，每个策略包含description和steps。
            如果不需要回退策略则返回None。
        """
        return None
