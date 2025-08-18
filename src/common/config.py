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
        "GEMINI_API_KEY": "",  # 可选，留空将使用降级路径
        "BROWSER_TYPE": "chromium",
        "HEADLESS": "false",
        "USER_DATA_DIR": str(root_dir / "browser_data"),
        "LOG_LEVEL": "INFO",
        "LOG_FILE": str(root_dir / "logs" / "agent.log"),
        "WEB_HOST": "127.0.0.1",
        "WEB_PORT": "8000",
        "ALLOWED_DOMAINS": "*",  # 默认允许所有域名
        "MAX_EXECUTION_TIME": "60",
    }
    
    # 从环境变量中读取配置
    for key, default in required_configs.items():
        value = os.environ.get(key, default)
        if value is None:
            raise ValueError(f"缺少必需的配置项: {key}")
        config[key] = value
    
    # 转换布尔值
    if str(config["HEADLESS"]).lower() in ("true", "1", "yes"):
        config["HEADLESS"] = True
    else:
        config["HEADLESS"] = False
    
    # 转换整数值
    for key in ["WEB_PORT", "MAX_EXECUTION_TIME"]:
        config[key] = int(config[key])
    
    # 转换列表值
    if config["ALLOWED_DOMAINS"] != "*":
        config["ALLOWED_DOMAINS"] = [domain.strip() for domain in config["ALLOWED_DOMAINS"].split(",")]
    
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