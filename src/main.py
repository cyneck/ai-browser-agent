#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI浏览器代理主程序入口

提供命令行和Web界面两种交互方式，用于接收用户的自然语言指令并执行网页自动化任务。
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 确保src目录在Python路径中
src_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(src_dir))

# 导入项目模块
from src.common.config import load_config
from src.common.logger import setup_logger


def setup_environment():
    """设置环境变量和日志"""
    # 加载配置
    config = load_config()
    
    # 设置日志
    log_level = getattr(logging, config.get("LOG_LEVEL", "INFO"))
    log_file = config.get("LOG_FILE", "./logs/agent.log")
    setup_logger(log_level, log_file)
    
    return config


def start_cli_mode():
    """启动命令行交互模式"""
    from src.api.cli import CLIInterface
    
    cli = CLIInterface()
    cli.start()


def start_web_mode(host, port):
    """启动Web交互模式"""
    from src.api.web import WebInterface
    
    web = WebInterface()
    web.start(host, port)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI浏览器智能体")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cli", action="store_true", help="启动命令行界面")
    group.add_argument("--web", action="store_true", help="启动Web界面")
    parser.add_argument("--text", type=str, help="要执行的自然语言文本（仅在cli模式下有效）")
    parser.add_argument("--interactive", action="store_true", help="启用交互式模式，与--text结合使用可进行多轮对话")
    args = parser.parse_args()
    
    # 设置环境
    config = setup_environment()
    
    # 根据参数启动相应的界面
    if args.cli:
        if args.text:
            from src.api.cli import CLIInterface
            cli = CLIInterface()
            if args.interactive:
                # 交互式文本模式：执行初始文本后继续交互
                cli.start_interactive_text_mode(args.text)
            else:
                # 单次执行模式：执行完毕后退出
                cli.initialize_and_execute(args.text)
        else:
            # 普通CLI交互模式
            start_cli_mode()
    elif args.web:
        host = config.get("WEB_HOST", "127.0.0.1")
        port = int(config.get("WEB_PORT", 8000))
        start_web_mode(host, port)


if __name__ == "__main__":
    main()