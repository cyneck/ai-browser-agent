#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extraction Engine

模板驱动的信息提取引擎，支持基于模板的信息提取和格式化
"""

import re
import json
from typing import Dict, Any, List, Optional
from src.common.logger import get_logger


class ExtractionEngine:
    """基于模板的信息提取引擎"""
    
    def __init__(self):
        self.logger = get_logger()
        self.extraction_templates = self._load_extraction_templates()
    
    def _load_extraction_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载信息提取模板 - 从配置文件加载"""
        import os
        from src.common.config import get_config
        
        # 尝试从JSON文件加载
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
        template_file = os.path.join(config_dir, "extraction_templates.json")
        
        try:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"无法从文件加载模板: {e}")
        
        # 回退到环境变量配置
        templates_str = get_config("EXTRACTION_TEMPLATES", "{}")
        try:
            return json.loads(templates_str)
        except json.JSONDecodeError:
            self.logger.warning("无法解析提取模板配置，使用空模板")
            return {}
    
    def extract_information(self, search_results: List[Dict[str, Any]], keywords: List[str]) -> Optional[str]:
        """
        基于模板提取信息
        
        Args:
            search_results: 搜索结果列表
            keywords: 关键词列表，用于匹配提取模板
            
        Returns:
            提取到的信息字符串，如果未找到则返回None
        """
        if not search_results or not keywords:
            return None
        
        # 合并所有搜索结果的文本
        combined_text = ""
        for result in search_results:
            title = result.get("title", "")
            description = result.get("description", "")
            combined_text += f"{title} {description} "
        
        combined_text = combined_text.strip()
        
        # 根据关键词找到匹配的模板
        for keyword in keywords:
            keyword = keyword.lower()
            for template_key, template in self.extraction_templates.items():
                if keyword in template_key.lower() or template_key.lower() in keyword:
                    return self._apply_template(combined_text, template)
        
        # 如果没有匹配到特定模板，使用通用提取
        return self._generic_extraction(combined_text)
    
    def _apply_template(self, text: str, template: Dict[str, Any]) -> Optional[str]:
        """应用提取模板"""
        if not template:
            return None
            
        patterns = template.get("patterns", [])
        fields = template.get("fields", [])
        
        if not patterns or not fields:
            return None
            
        extracted_data = {}
        
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text)
                if matches:
                    for i, field in enumerate(fields):
                        if i < len(matches[0]) if isinstance(matches[0], tuple) else i < len(matches):
                            value = matches[0][i] if isinstance(matches[0], tuple) else matches[0]
                            if field not in extracted_data:
                                extracted_data[field] = value
            except re.error:
                self.logger.warning(f"无效的正则表达式: {pattern}")
                continue
        
        if extracted_data:
            format_str = template.get("format", "{k}: {v}")
            return ", ".join([format_str.format(k=k, v=v) for k, v in extracted_data.items()])
        
        return None
    
    def _generic_extraction(self, text: str) -> Optional[str]:
        """通用信息提取"""
        from src.common.config import get_config
        
        if not text or not text.strip():
            return None
            
        # 获取配置参数
        max_length = int(get_config("EXTRACTION_MAX_LENGTH", "200"))
        extract_numbers = get_config("EXTRACT_NUMBERS_BY_DEFAULT", "true").lower() == "true"
        
        # 提取数字信息
        if extract_numbers:
            numbers = re.findall(r"\d+(?:\.\d+)?", text)
            if numbers:
                return f"找到数字信息: {', '.join(numbers)}"
        
        # 提取文本摘要
        text = text.strip()
        if len(text) > max_length:
            return text[:max_length] + "..."
        
        return text if text else None
    
    def get_supported_extraction_types(self) -> List[str]:
        """获取支持的提取类型"""
        return list(self.extraction_templates.keys()) + ["通用"]
    
    def add_template(self, template_name: str, patterns: List[str], fields: List[str]) -> None:
        """添加新的提取模板"""
        self.extraction_templates[template_name] = {
            "patterns": patterns,
            "fields": fields
        }
        self.logger.info(f"添加新模板: {template_name}")


# 创建全局实例
extraction_engine = ExtractionEngine()