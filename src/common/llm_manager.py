#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM管理器

负责管理多种LLM提供商的调用，包括Gemini、OpenAI、Qwen和Ollama。
"""

import json
import time
import threading
import queue
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from src.common.config import get_config
from src.common.logger import get_logger
from src.common.performance_monitor import get_performance_monitor


class LLMProvider(ABC):
    """LLM提供商抽象基类"""

    @abstractmethod
    def get_name(self) -> str:
        """获取提供商名称"""
        pass

    @abstractmethod
    def call_llm(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """调用LLM"""
        pass


class GeminiProvider(LLMProvider):
    """Gemini提供商"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = get_logger()

        # Optional import for Gemini
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            self.genai = None
            self.logger.warning("Google Generative AI SDK not installed")

    def get_name(self) -> str:
        return "gemini"

    def call_llm(self, prompt: str, model_name: str) -> Dict[str, Any]:
        if self.genai is None:
            raise ImportError("Google Generative AI SDK not installed")

        try:
            self.genai.configure(api_key=self.api_key)
            model = self.genai.GenerativeModel(model_name)

            # 添加超时控制
            result_queue = queue.Queue()
            error_queue = queue.Queue()

            def api_call():
                try:
                    resp = model.generate_content(prompt)
                    result_queue.put(resp)
                except Exception as e:
                    error_queue.put(e)

            # 在单独线程中执行 API 调用
            thread = threading.Thread(target=api_call)
            thread.daemon = True
            thread.start()

            # 等待结果，最多 10 秒
            thread.join(timeout=10)

            if thread.is_alive():
                raise TimeoutError("Gemini API call timeout")

            if not error_queue.empty():
                raise error_queue.get()

            if not result_queue.empty():
                resp = result_queue.get()
                text = getattr(resp, "text", "") or ""
                return {"text": text, "raw_response": resp}
            else:
                raise Exception("No response from Gemini API")

        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI提供商（兼容Qwen等OpenAI兼容接口）"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = get_logger()

        # Optional import for OpenAI
        self.openai_module = None
        try:
            import openai
            self.openai_module = openai
        except ImportError:
            self.logger.warning("OpenAI SDK not installed")

    def get_name(self) -> str:
        return "openai"

    def call_llm(self, prompt: str, model_name: str) -> Dict[str, Any]:
        if self.openai_module is None:
            raise ImportError("OpenAI SDK not installed")

        try:
            # 配置客户端
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = self.openai_module.OpenAI(**client_kwargs)

            # 调用API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                timeout=10
            )

            if response.choices and response.choices[0].message:
                text = response.choices[0].message.content or ""
                return {"text": text, "raw_response": response}
            else:
                raise Exception("No response from OpenAI API")

        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Ollama提供商"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.logger = get_logger()

    def get_name(self) -> str:
        return "ollama"

    def call_llm(self, prompt: str, model_name: str) -> Dict[str, Any]:
        try:
            import requests
        except ImportError:
            raise ImportError("Requests library not installed")

        try:
            # 从配置中读取超时时间，默认为120秒
            timeout = int(get_config("OLLAMA_TIMEOUT", "120"))
            
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }

            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            text = data.get("response", "")
            return {"text": text, "raw_response": data}

        except Exception as e:
            self.logger.error(f"Ollama API call failed: {e}")
            raise


class LLMManager:
    """LLM管理器"""

    def __init__(self):
        self.logger = get_logger()
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化所有可用的LLM提供商"""
        # Gemini
        gemini_api_key = get_config("GEMINI_API_KEY")
        if gemini_api_key:
            try:
                self.providers["gemini"] = GeminiProvider(gemini_api_key)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini provider: {e}")

        # OpenAI
        openai_api_key = get_config("OPENAI_API_KEY")
        if openai_api_key:
            try:
                openai_base_url = get_config("OPENAI_BASE_URL")
                self.providers["openai"] = OpenAIProvider(openai_api_key, openai_base_url)
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Qwen (作为OpenAI兼容接口)
        qwen_api_key = get_config("QWEN_API_KEY")
        if qwen_api_key:
            try:
                qwen_base_url = get_config("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
                self.providers["qwen"] = OpenAIProvider(qwen_api_key, qwen_base_url)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Qwen provider: {e}")

        # Ollama
        ollama_enabled = get_config("OLLAMA_ENABLED", "false")
        self.logger.info(f"OLLAMA_ENABLED config value: {ollama_enabled}")
        if ollama_enabled and str(ollama_enabled).lower() == "true":
            try:
                ollama_base_url = get_config("OLLAMA_BASE_URL", "http://localhost:11434")
                self.providers["ollama"] = OllamaProvider(ollama_base_url)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Ollama provider: {e}")

        self.logger.info(f"Initialized LLM providers: {list(self.providers.keys())}")

    def get_available_providers(self) -> List[str]:
        """获取可用的LLM提供商列表"""
        return list(self.providers.keys())

    def call_llm(self, prompt: str, provider: str = "gemini", model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        调用指定的LLM提供商
        
        Args:
            prompt: 提示词
            provider: 提供商名称 (gemini, openai, qwen, ollama)
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 包含text和raw_response的字典
        """
        if provider not in self.providers:
            raise ValueError(
                f"LLM provider '{provider}' not available. Available providers: {list(self.providers.keys())}")

        # 获取默认模型名称
        if not model_name:
            model_name = self._get_default_model(provider)

        self.logger.debug(f"Calling LLM: provider={provider}, model={model_name}")

        # 记录开始时间
        start_time = time.time()
        prompt_tokens = int(len(prompt.split()) * 1.3)  # 粗略估算token数

        try:
            # 调用LLM
            result = self.providers[provider].call_llm(prompt, model_name)

            # 记录性能指标
            response_time = time.time() - start_time
            text = result.get("text", "")
            completion_tokens = int(len(text.split()) * 1.3)

            perf_monitor = get_performance_monitor()
            perf_monitor.record_llm_call(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time=response_time,
                model_name=f"{provider}/{model_name}",
                success=True
            )

            self.logger.debug(f"LLM call successful: provider={provider}, time={response_time:.2f}s")
            return result

        except Exception as e:
            # 记录性能指标（失败）
            response_time = time.time() - start_time
            perf_monitor = get_performance_monitor()
            perf_monitor.record_llm_call(
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                response_time=response_time,
                model_name=f"{provider}/{model_name}",
                success=False,
                error_message=str(e)
            )

            self.logger.error(f"LLM call failed: provider={provider}, error={e}")
            raise

    def _get_default_model(self, provider: str) -> str:
        """获取指定提供商的默认模型"""
        defaults = {
            "gemini": get_config("GEMINI_MODEL", "gemini-1.5-flash"),
            "openai": get_config("OPENAI_MODEL", "gpt-3.5-turbo"),
            "qwen": get_config("QWEN_MODEL", "qwen-turbo"),
            "ollama": get_config("OLLAMA_MODEL", "llama2")
        }
        return defaults.get(provider, "default")

    def extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """
        从LLM响应中提取JSON代码块
        
        Args:
            text: LLM返回的文本
            
        Returns:
            Dict[str, Any]: 解析后的JSON对象
        """
        import re

        # 提取JSON代码块
        json_blocks = re.findall(r"```json\s*\n(.*?)```", text, re.DOTALL)
        if json_blocks:
            text = json_blocks[0]

        # 尝试解析JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # 打印原始响应数据以便诊断问题
            self.logger.warning(f"Failed to parse JSON from LLM response: {e}")
            self.logger.warning(f"Raw LLM response:\n{text}")
            self.logger.warning(f"Response length: {len(text)} characters")
            raise


# 全局LLM管理器实例
llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """获取全局LLM管理器实例"""
    return llm_manager
