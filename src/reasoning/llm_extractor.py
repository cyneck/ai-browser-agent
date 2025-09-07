#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM-based Content Extractor

Uses LLM to intelligently extract and format information from web content
based on user requests, replacing hard-coded extraction templates.
"""

import json
from typing import Dict, Any, List, Optional
from src.common.logger import get_logger
from src.common.llm_manager import get_llm_manager
from src.common.config import get_config


class LLMExtractor:
    """LLM-based content extractor that understands user intent and extracts relevant information"""
    
    def __init__(self):
        self.logger = get_logger()
        self.llm_manager = get_llm_manager()
    
    def extract_information(self, search_results: List[Dict], user_query: str) -> Optional[str]:
        """
        Extract information from search results using LLM based on user query
        
        Args:
            search_results: List of search results with title, description, url
            user_query: The original user query that specifies what information to extract
            
        Returns:
            Extracted and formatted information string, or None if extraction fails
        """
        self.logger.info(f"开始使用LLM提取信息，结果数量: {len(search_results)}")
        self.logger.info(f"用户查询: {user_query}")
        
        if not search_results:
            self.logger.warning("没有搜索结果可供提取")
            return None
        
        try:
            # 构建提取提示词
            prompt = self._build_extraction_prompt(search_results, user_query)
            
            # 调用LLM进行信息提取
            provider = get_config("LLM_PROVIDER", "gemini")
            model_name = None
            
            # 如果配置了特定模型，则使用
            if provider == "gemini":
                model_name = get_config("GEMINI_MODEL")
            elif provider == "openai":
                model_name = get_config("OPENAI_MODEL")
            elif provider == "qwen":
                model_name = get_config("QWEN_MODEL")
            elif provider == "ollama":
                model_name = get_config("OLLAMA_MODEL")
            
            self.logger.debug(f"调用LLM进行信息提取: provider={provider}, model={model_name}")
            
            result = self.llm_manager.call_llm(prompt, provider, model_name)
            extracted_text = result.get("text", "").strip()
            
            self.logger.info(f"LLM提取完成，结果长度: {len(extracted_text)}")
            
            # 如果LLM返回了JSON格式的响应，解析它
            if extracted_text.startswith("{") and extracted_text.endswith("}"):
                try:
                    response_data = json.loads(extracted_text)
                    if "extracted_content" in response_data:
                        return response_data["extracted_content"]
                    elif "content" in response_data:
                        return response_data["content"]
                except json.JSONDecodeError:
                    pass
            
            # 如果提取的文本太短，可能是失败了
            if len(extracted_text) < 10:
                self.logger.warning("LLM提取结果过短，可能提取失败")
                return None
                
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"LLM信息提取失败: {e}")
            return None
    
    def _build_extraction_prompt(self, search_results: List[Dict], user_query: str) -> str:
        """
        构建用于信息提取的提示词
        
        Args:
            search_results: 搜索结果列表
            user_query: 用户原始查询
            
        Returns:
            构建好的提示词
        """
        # 构建搜索结果的JSON表示
        results_json = json.dumps(search_results[:5], ensure_ascii=False, indent=2)
        
        prompt = f"""
你是一个智能信息提取助手。你的任务是根据用户的查询从搜索结果中提取最相关的信息，并以清晰、简洁的自然语言格式返回。

用户查询: "{user_query}"

搜索结果:
{results_json}

请根据用户查询分析搜索结果，并提取最相关的信息。你的回答应该：

1. 直接回答用户的问题，不要包含额外的解释
2. 使用自然语言格式，易于理解
3. 如果找到了具体信息（如天气、价格、时间等），请直接给出
4. 如果是概括性问题，请提供最相关的摘要
5. 如果没有找到相关信息，请回复"未找到相关信息"

请以JSON格式返回你的答案，格式如下：
{{
  "extracted_content": "提取的内容"
}}

示例：
用户查询："今日天气是怎么样"
搜索结果包含："今天北京晴转多云，温度23-32°C"
你的回答：
{{
  "extracted_content": "今天天气是晴转多云，温度23°C~32°C"
}}

现在请根据上述搜索结果和用户查询提取信息：
"""
        
        return prompt
    
    def extract_structured_data(self, search_results: List[Dict], structure_type: str = "auto") -> Optional[Dict[str, Any]]:
        """
        提取结构化数据
        
        Args:
            search_results: 搜索结果列表
            structure_type: 结构类型 (table, list, json, auto)
            
        Returns:
            结构化数据字典，或None如果提取失败
        """
        self.logger.info(f"提取结构化数据，类型: {structure_type}")
        
        if not search_results:
            return None
        
        try:
            # 构建结构化数据提取提示词
            prompt = self._build_structured_extraction_prompt(search_results, structure_type)
            
            # 调用LLM进行结构化数据提取
            provider = get_config("LLM_PROVIDER", "gemini")
            model_name = None
            
            # 如果配置了特定模型，则使用
            if provider == "gemini":
                model_name = get_config("GEMINI_MODEL")
            elif provider == "openai":
                model_name = get_config("OPENAI_MODEL")
            elif provider == "qwen":
                model_name = get_config("QWEN_MODEL")
            elif provider == "ollama":
                model_name = get_config("OLLAMA_MODEL")
            
            result = self.llm_manager.call_llm(prompt, provider, model_name)
            extracted_text = result.get("text", "").strip()
            
            # 尝试解析JSON响应
            if extracted_text.startswith("{") and extracted_text.endswith("}"):
                try:
                    return json.loads(extracted_text)
                except json.JSONDecodeError:
                    pass
            
            # 如果不是JSON格式，尝试作为文本处理
            return {"content": extracted_text}
            
        except Exception as e:
            self.logger.error(f"结构化数据提取失败: {e}")
            return None
    
    def _build_structured_extraction_prompt(self, search_results: List[Dict], structure_type: str) -> str:
        """
        构建用于结构化数据提取的提示词
        
        Args:
            search_results: 搜索结果列表
            structure_type: 结构类型
            
        Returns:
            构建好的提示词
        """
        results_json = json.dumps(search_results[:5], ensure_ascii=False, indent=2)
        
        prompt = f"""
你是一个结构化数据提取专家。你的任务是从搜索结果中提取结构化信息。

搜索结果:
{results_json}

请提取搜索结果中的结构化信息，并以指定格式返回。

结构类型: {structure_type}

请以JSON格式返回你的答案，格式如下：
{{
  "structured_data": [
    {{
      "字段1": "值1",
      "字段2": "值2"
    }}
  ],
  "data_type": "提取的数据类型说明"
}}

如果无法提取结构化数据，请返回:
{{
  "structured_data": [],
  "data_type": "无法提取结构化数据"
}}

现在请提取结构化数据：
"""
        
        return prompt