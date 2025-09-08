#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块

负责加载和管理项目的配置信息，支持从环境变量和配置文件中读取配置。
"""

import os
from pathlib import Path
from typing import Dict, Any

import dotenv


def load_config() -> Dict[str, Any]:
    """
    加载配置信息
    
    从.env文件和环境变量中加载配置信息
    
    Returns:
        Dict[str, Any]: 配置信息字典
    """
    # 项目根目录
    root_dir = Path(__file__).resolve().parent.parent.parent
    
    # 加载.env文件
    dotenv_path = root_dir / ".env"
    if dotenv_path.exists():
        dotenv.load_dotenv(dotenv_path)
    
    # 创建配置字典
    config = {}
    
    # 必需的配置项及其默认值
    required_configs = {
        # LLM配置
        "LLM_PROVIDER": "gemini",  # gemini, openai, qwen, ollama
        "GEMINI_API_KEY": "",  # 可选，留空将使用降级路径
        "GEMINI_MODEL": "gemini-1.5-flash",
        "OPENAI_API_KEY": "",
        "OPENAI_BASE_URL": "",
        "OPENAI_MODEL": "gpt-3.5-turbo",
        "QWEN_API_KEY": "",
        "QWEN_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "QWEN_MODEL": "qwen-turbo",
        "OLLAMA_ENABLED": "false",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "qwen3:4b",  # 更新为实际安装的模型
        "OLLAMA_TIMEOUT": "120",  # 添加OLLAMA_TIMEOUT配置项，默认120秒
        
        "BROWSER_TYPE": "chromium",
        "HEADLESS": "false",
        "USER_DATA_DIR": str(root_dir / "browser_data"),
        "LOG_LEVEL": "INFO",
        "LOG_FILE": str(root_dir / "logs" / "agent.log"),
        "WEB_HOST": "127.0.0.1",
        "WEB_PORT": "8000",
        "MAX_EXECUTION_TIME": "60",
        
        # 调试配置
        "DEBUG_MODE": "false",  # 启用调试模式，保存截图和页面信息
        
        # 人类行为模拟配置
        "HUMAN_BEHAVIOR_ENABLED": "true",
        "HUMAN_BEHAVIOR_MODE": "moderate",  # conservative, moderate, aggressive
        "HUMAN_BASE_DELAY_MIN": "0.3",
        "HUMAN_BASE_DELAY_MAX": "1.2",
        "HUMAN_ACTION_INTERVAL_MIN": "0.5",
        "HUMAN_ACTION_INTERVAL_MAX": "3.0",
        "HUMAN_TYPING_SPEED_MIN": "3",
        "HUMAN_TYPING_SPEED_MAX": "8",
        "HUMAN_MOUSE_MOVE_ENABLED": "true",
        "HUMAN_RANDOM_PAUSE_PROBABILITY": "0.15",
        "HUMAN_RANDOM_PAUSE_MIN": "2.0",
        "HUMAN_RANDOM_PAUSE_MAX": "8.0",
    }
    
    # 从环境变量中读取配置
    for key, default in required_configs.items():
        value = os.environ.get(key, default)
        if value is None:
            raise ValueError(f"缺少必需的配置项: {key}")
        config[key] = value
    
    # 转换布尔值
    bool_configs = ["HEADLESS", "HUMAN_BEHAVIOR_ENABLED", "HUMAN_MOUSE_MOVE_ENABLED", "OLLAMA_ENABLED", "DEBUG_MODE"]
    for key in bool_configs:
        if key in config:
            if str(config[key]).lower() in ("true", "1", "yes"):
                config[key] = True
            else:
                config[key] = False
    
    # 转换整数值
    for key in ["WEB_PORT", "MAX_EXECUTION_TIME", "OLLAMA_TIMEOUT"]:  # 添加OLLAMA_TIMEOUT
        config[key] = int(config[key])
        
    # 转换浮点数值
    float_configs = [
        "HUMAN_BASE_DELAY_MIN", "HUMAN_BASE_DELAY_MAX",
        "HUMAN_ACTION_INTERVAL_MIN", "HUMAN_ACTION_INTERVAL_MAX",
        "HUMAN_TYPING_SPEED_MIN", "HUMAN_TYPING_SPEED_MAX",
        "HUMAN_RANDOM_PAUSE_PROBABILITY", "HUMAN_RANDOM_PAUSE_MIN", 
        "HUMAN_RANDOM_PAUSE_MAX"
    ]
    for key in float_configs:
        if key in config:
            config[key] = float(config[key])
    

    
    return config


def get_config(key: str, default: Any = None) -> Any:
    """
    获取指定的配置项
    
    Args:
        key: 配置项的键名
        default: 默认值，如果配置项不存在则返回此值
        
    Returns:
        Any: 配置项的值
    """
    config = load_config()
    return config.get(key, default)


def get_human_behavior_config() -> Dict[str, Any]:
    """
    获取人类行为模拟配置
    
    Returns:
        Dict[str, Any]: 人类行为模拟配置字典
    """
    config = load_config()
    
    behavior_config = {
        "enabled": config.get("HUMAN_BEHAVIOR_ENABLED", True),
        "behavior_mode": config.get("HUMAN_BEHAVIOR_MODE", "moderate"),
        "base_delay_min": config.get("HUMAN_BASE_DELAY_MIN", 0.3),
        "base_delay_max": config.get("HUMAN_BASE_DELAY_MAX", 1.2),
        "action_interval_min": config.get("HUMAN_ACTION_INTERVAL_MIN", 0.5),
        "action_interval_max": config.get("HUMAN_ACTION_INTERVAL_MAX", 3.0),
        "typing_speed_min": config.get("HUMAN_TYPING_SPEED_MIN", 3),
        "typing_speed_max": config.get("HUMAN_TYPING_SPEED_MAX", 8),
        "mouse_move_enabled": config.get("HUMAN_MOUSE_MOVE_ENABLED", True),
        "random_pause_probability": config.get("HUMAN_RANDOM_PAUSE_PROBABILITY", 0.15),
        "random_pause_min": config.get("HUMAN_RANDOM_PAUSE_MIN", 2.0),
        "random_pause_max": config.get("HUMAN_RANDOM_PAUSE_MAX", 8.0),
    }
    
    return behavior_config