#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动脚本

用于快速启动AI浏览器代理。
"""

import argparse
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import main


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI浏览器代理启动脚本")
    
    # 模式选择
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["cli", "web"], 
        default="cli",
        help="运行模式：cli（命令行界面）或web（Web界面）"
    )
    
    # Web服务器选项
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1",
        help="Web服务器主机地址（仅在web模式下有效）"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Web服务器端口（仅在web模式下有效）"
    )
    
    # 浏览器选项
    parser.add_argument(
        "--browser", 
        type=str, 
        choices=["chromium", "firefox", "webkit"], 
        default="chromium",
        help="使用的浏览器类型"
    )
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="是否以无头模式运行浏览器"
    )
    parser.add_argument(
        "--user-data-dir", 
        type=str, 
        default=None,
        help="浏览器用户数据目录，用于保存会话状态"
    )
    
    # 日志选项
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
        default="INFO",
        help="日志级别"
    )
    parser.add_argument(
        "--log-file", 
        type=str, 
        default=None,
        help="日志文件路径，不指定则输出到控制台"
    )
    
    # 安全选项
    parser.add_argument(
        "--allowed-domains", 
        type=str, 
        default=None,
        help="允许访问的域名列表，以逗号分隔"
    )
    parser.add_argument(
        "--max-execution-time", 
        type=int, 
        default=60,
        help="指令执行最大时间（秒）"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # 设置环境变量
    if args.browser:
        os.environ["BROWSER_TYPE"] = args.browser
    
    if args.headless:
        os.environ["BROWSER_HEADLESS"] = "true"
    
    if args.user_data_dir:
        os.environ["BROWSER_USER_DATA_DIR"] = args.user_data_dir
    
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    if args.log_file:
        os.environ["LOG_FILE"] = args.log_file
    
    if args.allowed_domains:
        os.environ["ALLOWED_DOMAINS"] = args.allowed_domains
    
    if args.max_execution_time:
        os.environ["MAX_EXECUTION_TIME"] = str(args.max_execution_time)
    
    # 启动应用
    main(mode=args.mode, host=args.host, port=args.port)