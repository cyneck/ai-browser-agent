#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志模块

提供统一的日志记录功能，支持控制台和文件输出。
"""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logger(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        level: 日志级别，默认为INFO
        log_file: 日志文件路径，如果为None则只输出到控制台
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger("ai_browser_agent")
    logger.setLevel(level)
    
    # 清除已有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # 添加控制台处理器
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # 添加文件处理器
        logger.addHandler(file_handler)
    
    return logger


# 创建默认日志记录器
logger = setup_logger()


def get_logger() -> logging.Logger:
    """
    获取日志记录器
    
    Returns:
        logging.Logger: 日志记录器
    """
    return logger