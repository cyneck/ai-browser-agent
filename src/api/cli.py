#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行交互界面

提供基于命令行的用户交互界面，接收用户的自然语言指令并显示执行结果。
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
                
                # 处理用户指令
                self._process_instruction(user_input)

        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}")
            print(f"发生错误: {str(e)}")
        finally:
            # 关闭浏览器
            self.agent.cleanup()
            print("会话已结束，谢谢使用！")

    def initialize_and_execute(self, instruction: str):
        """初始化并直接执行单条指令"""
        self.logger.info(f"直接执行指令: {instruction}")
        try:
            self.agent.initialize()
            self._process_instruction(instruction)
        except Exception as e:
            self.logger.error(f"执行指令时发生错误: {str(e)}")
            print(f"执行指令时发生错误: {str(e)}")
        finally:
            self.agent.cleanup()
            print("指令执行完毕。")

    def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            return input("> ")
        except EOFError:
            return "exit"

    def _process_instruction(self, instruction: str):
        """处理用户指令"""
        try:
            print("[执行中...]")

            # 执行指令
            result = self.agent.execute(instruction, self.session_state)

            # 显示结果
            if result.get("success", False):
                print(result.get("message", "执行成功"))
            else:
                print(f"执行失败: {result.get('error', '未知错误')}")

            # 更新会话状态
            if "session_state" in result:
                self.session_state.update(result["session_state"])

        except Exception as e:
            self.logger.error(f"处理指令时发生错误: {str(e)}")
            print(f"处理指令时发生错误: {str(e)}")

        """获取用户输入"""
        try:
            return input("> ")
        except EOFError:
            return "exit"
    
    def _process_instruction(self, instruction: str):
        """处理用户指令"""
        try:
            print("[执行中...]")
            
            # 执行指令
            result = self.agent.execute(instruction, self.session_state)
            
            # 显示结果
            if result.get("success", False):
                print(result.get("message", "执行成功"))
            else:
                print(f"执行失败: {result.get('error', '未知错误')}")
                
            # 更新会话状态
            if "session_state" in result:
                self.session_state.update(result["session_state"])
                
        except Exception as e:
            self.logger.error(f"处理指令时发生错误: {str(e)}")
            print(f"处理指令时发生错误: {str(e)}")