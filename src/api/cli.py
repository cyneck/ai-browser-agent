#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行交互界面

提供基于命令行的用户交互界面，接收用户的自然语言文本并显示执行结果。
注意术语区分：
- text: 用户输入的自然语言文本
- cli: 命令行交互方式
"""

import sys
from typing import Dict, Any, Optional

from src.common.logger import get_logger
from src.reasoning.agent import BrowserAgent


class CLIInterface:
    """命令行交互界面类"""
    
    def __init__(self):
        """初始化命令行界面"""
        self.logger = get_logger()
        self.agent = BrowserAgent()
        self.session_state: Dict[str, Any] = {}
    
    def start(self):
        """启动命令行交互循环"""
        self.logger.info("启动命令行界面")
        print("欢迎使用AI浏览器代理！输入'退出'或'exit'结束会话。")
        
        try:
            # 初始化浏览器
            self.agent.initialize()
            
            # 交互循环
            while True:
                # 获取用户输入
                user_input = self._get_user_input()
                
                # 检查是否退出
                if user_input.lower() in ["退出", "exit", "quit"]:
                    break
                
                # 处理用户自然语言文本
                self._process_text(user_input)

        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}")
            print(f"发生错误: {str(e)}")
        finally:
            # 关闭浏览器
            self.agent.cleanup()
            print("会话已结束，谢谢使用！")

    def initialize_and_execute(self, text: str):
        """初始化并直接执行单条自然语言文本"""
        self.logger.info(f"直接执行自然语言文本: {text}")
        try:
            self.agent.initialize()
            self._process_text(text)
        except Exception as e:
            self.logger.error(f"执行自然语言文本时发生错误: {str(e)}")
            print(f"执行自然语言文本时发生错误: {str(e)}")
        finally:
            self.agent.cleanup()
            print("自然语言文本执行完毕。")
    
    def start_interactive_text_mode(self, initial_text: str):
        """启动交互式文本模式，支持多轮对话"""
        self.logger.info(f"启动交互式文本模式，初始文本: {initial_text}")
        print("欢迎使用AI浏览器代理交互式模式！")
        print("您可以继续输入指令进行多轮对话，输入'退出'或'exit'结束会话。")
        print("="*60)
        
        try:
            # 初始化浏览器
            self.agent.initialize()
            
            # 执行初始文本
            print(f"执行初始指令: {initial_text}")
            self._process_text(initial_text)
            print("="*60)
            
            # 进入交互循环
            while True:
                print("\n请输入下一条指令:")
                user_input = self._get_user_input()
                
                # 检查是否退出
                if user_input.lower() in ["退出", "exit", "quit", ""]:
                    break
                
                # 处理用户自然语言文本
                print("="*60)
                self._process_text(user_input)
                print("="*60)

        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}")
            print(f"发生错误: {str(e)}")
        finally:
            # 关闭浏览器
            self.agent.cleanup()
            print("\n交互式会话已结束，谢谢使用！")

    def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            return input("> ")
        except EOFError:
            return "exit"

    def _process_text(self, text: str):
        """处理用户自然语言文本"""
        try:
            print("[执行中...]")
            result = self.agent.execute(text, self.session_state)
            
            if result.get("success"):
                self._display_success(result)
            else:
                print(f"❌ 执行失败: {result.get('error', '未知错误')}")
            
            # 更新会话状态
            if "session_state" in result:
                self.session_state.update(result["session_state"])
        except Exception as e:
            self.logger.error(f"处理自然语言文本时发生错误: {str(e)}")
            print(f"❌ 处理自然语言文本时发生错误: {str(e)}")
    
    def _display_success(self, result: Dict[str, Any]):
        """显示成功结果"""
        message = result.get("message", "执行成功")
        print(f"✅ {message}")
        
        # 显示提取的内容（除非是摘要信息且已有格式化消息）
        intent_info = result.get("intent_info")
        should_show_content = not (
            intent_info and 
            intent_info.get("intent_type") == "SUMMARY_INFO" and 
            message and message != "执行成功"
        )
        
        if should_show_content:
            content = result.get("content") or result.get("extracted_content")
            if content:
                self._display_extracted_content(content)
    
    def _display_extracted_content(self, content):
        """显示提取的内容，格式化输出"""
        if isinstance(content, list) and content:
            print("\n📋 提取的内容:")
            for i, item in enumerate(content[:5], 1):  # 只显示前5个结果
                if isinstance(item, dict):
                    title = item.get('title', '').strip()
                    description = item.get('description', '').strip()
                    url = item.get('url', '').strip()
                    
                    print(f"\n{i}. {title}")
                    if description:
                        # 限制描述长度
                        desc = description[:100] + '...' if len(description) > 100 else description
                        print(f"   📝 {desc}")
                    if url:
                        print(f"   🔗 {url}")
            
            if len(content) > 5:
                print(f"\n... 还有 {len(content) - 5} 个结果未显示")
        elif isinstance(content, str) and content.strip():
            print(f"\n📄 内容: {content[:200]}..." if len(content) > 200 else f"\n📄 内容: {content}")

