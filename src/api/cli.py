#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行交互界面

提供基于命令行的用户交互界面，接收用户的自然语言文本并显示执行结果。
注意术语区分：
- text: 用户输入的自然语言文本
- cli: 命令行交互方式

增强功能：
- 命令历史记录和自动补全
- 多种输出格式支持
- 改进的用户交互流程
"""

import sys
import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import readline
import atexit

from src.common.logger import get_logger
from src.reasoning.agent import BrowserAgent


class CLIInterface:
    """命令行交互界面类"""
    
    def __init__(self, output_format: str = "text"):
        """初始化命令行界面
        
        Args:
            output_format: 输出格式 ('text', 'json', 'csv', 'markdown')
        """
        self.logger = get_logger()
        self.agent = BrowserAgent()
        self.session_state: Dict[str, Any] = {}
        self.output_format = output_format
        self.command_history: List[str] = []
        self.history_file = Path.home() / ".ai_browser_agent_history"
        
        # 设置命令历史和自动补全
        self._setup_readline()
        
        # 常用命令提示
        self.common_commands = [
            "打开 https://",
            "搜索 ",
            "点击 ",
            "填写 ",
            "截图",
            "提取内容",
            "返回上一页",
            "刷新页面",
            "关闭标签页",
            "等待 ",
            "滚动到 ",
            "下载 ",
            "保存为PDF",
            "切换到标签页 ",
            "新建标签页",
            "获取页面信息",
            "清除缓存",
            "设置窗口大小 ",
            "模拟按键 ",
            "右键点击 "
        ]
    
    def start(self):
        """启动命令行交互循环"""
        self.logger.info("启动命令行界面")
        self._print_welcome_message()
        
        try:
            # 初始化浏览器
            self.agent.initialize()
            
            # 交互循环
            while True:
                # 获取用户输入
                user_input = self._get_user_input()
                
                # 检查特殊命令
                if self._handle_special_commands(user_input):
                    continue
                
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

    def _setup_readline(self):
        """设置readline历史记录和自动补全"""
        try:
            # 设置历史记录文件
            if self.history_file.exists():
                readline.read_history_file(str(self.history_file))
            
            # 设置历史记录长度
            readline.set_history_length(1000)
            
            # 设置自动补全
            readline.set_completer(self._completer)
            readline.parse_and_bind("tab: complete")
            
            # 注册退出时保存历史记录
            atexit.register(self._save_history)
            
        except ImportError:
            # Windows系统可能没有readline
            self.logger.warning("readline模块不可用，命令历史功能将被禁用")
    
    def _save_history(self):
        """保存命令历史"""
        try:
            readline.write_history_file(str(self.history_file))
        except (ImportError, OSError):
            pass
    
    def _completer(self, text: str, state: int) -> Optional[str]:
        """自动补全函数"""
        if state == 0:
            # 第一次调用，生成匹配列表
            self.matches = [cmd for cmd in self.common_commands if cmd.startswith(text)]
            
            # 也从历史记录中查找匹配
            for cmd in self.command_history:
                if cmd.startswith(text) and cmd not in self.matches:
                    self.matches.append(cmd)
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def _print_welcome_message(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("🤖 AI浏览器代理 - 智能网页自动化助手")
        print("=" * 60)
        print("💡 使用提示:")
        print("  • 输入自然语言指令，如：'打开百度并搜索天气'")
        print("  • 使用Tab键自动补全常用命令")
        print("  • 输入'帮助'查看更多命令")
        print("  • 输入'退出'或'exit'结束会话")
        print("  • 使用Ctrl+C随时中断")
        print("=" * 60)
        print(f"📊 当前输出格式: {self.output_format}")
        print("=" * 60)
    
    def _handle_special_commands(self, user_input: str) -> bool:
        """处理特殊命令
        
        Returns:
            bool: 如果处理了特殊命令返回True，否则返回False
        """
        cmd = user_input.lower().strip()
        
        if cmd in ["帮助", "help", "?"]:
            self._show_help()
            return True
        elif cmd in ["历史", "history"]:
            self._show_history()
            return True
        elif cmd.startswith("格式 ") or cmd.startswith("format "):
            format_name = cmd.split(" ", 1)[1] if " " in cmd else ""
            self._change_output_format(format_name)
            return True
        elif cmd in ["清屏", "clear", "cls"]:
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
        elif cmd in ["状态", "status"]:
            self._show_status()
            return True
        
        return False
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n📖 命令帮助:")
        print("=" * 50)
        print("🔧 特殊命令:")
        print("  帮助/help/?     - 显示此帮助信息")
        print("  历史/history    - 显示命令历史")
        print("  格式 <类型>     - 更改输出格式 (text/json/csv/markdown)")
        print("  清屏/clear/cls  - 清除屏幕")
        print("  状态/status     - 显示当前状态")
        print("  退出/exit/quit  - 退出程序")
        print()
        print("🌐 常用网页操作:")
        print("  打开 <网址>     - 导航到指定网页")
        print("  搜索 <关键词>   - 在当前页面搜索")
        print("  点击 <元素>     - 点击页面元素")
        print("  填写 <内容>     - 填写表单")
        print("  截图           - 截取当前页面")
        print("  提取内容       - 提取页面内容")
        print("  返回上一页     - 浏览器后退")
        print("  刷新页面       - 刷新当前页面")
        print()
        print("📋 输出格式:")
        print("  text     - 纯文本格式 (默认)")
        print("  json     - JSON格式")
        print("  csv      - CSV格式")
        print("  markdown - Markdown格式")
        print("=" * 50)
    
    def _show_history(self):
        """显示命令历史"""
        if not self.command_history:
            print("📝 暂无命令历史")
            return
        
        print("\n📝 命令历史 (最近10条):")
        print("=" * 50)
        for i, cmd in enumerate(self.command_history[-10:], 1):
            print(f"  {i:2d}. {cmd}")
        print("=" * 50)
    
    def _change_output_format(self, format_name: str):
        """更改输出格式"""
        valid_formats = ["text", "json", "csv", "markdown"]
        
        if format_name not in valid_formats:
            print(f"❌ 无效的输出格式: {format_name}")
            print(f"💡 支持的格式: {', '.join(valid_formats)}")
            return
        
        self.output_format = format_name
        print(f"✅ 输出格式已更改为: {format_name}")
    
    def _show_status(self):
        """显示当前状态"""
        print("\n📊 当前状态:")
        print("=" * 40)
        print(f"  输出格式: {self.output_format}")
        print(f"  命令历史: {len(self.command_history)} 条")
        print(f"  会话状态: {len(self.session_state)} 个变量")
        print(f"  浏览器状态: {'已初始化' if hasattr(self.agent, 'page') else '未初始化'}")
        print("=" * 40)

    def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            user_input = input("🤖 > ")
            
            # 添加到历史记录
            if user_input.strip() and user_input.strip() not in self.command_history:
                self.command_history.append(user_input.strip())
                
            return user_input
        except EOFError:
            return "exit"

    def _process_text(self, text: str):
        """处理用户自然语言文本"""
        try:
            print("⏳ 执行中...")
            start_time = datetime.now()

            # 执行自然语言文本，这里会将文本转换为可执行的JSON指令
            result = self.agent.execute(text, self.session_state)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 根据输出格式显示结果
            self._display_result(result, execution_time)

            # 更新会话状态
            if "session_state" in result:
                self.session_state.update(result["session_state"])

        except Exception as e:
            self.logger.error(f"处理自然语言文本时发生错误: {str(e)}")
            self._display_error(str(e))
    
    def _display_result(self, result: Dict[str, Any], execution_time: float):
        """根据输出格式显示结果"""
        if self.output_format == "json":
            self._display_json_result(result, execution_time)
        elif self.output_format == "csv":
            self._display_csv_result(result, execution_time)
        elif self.output_format == "markdown":
            self._display_markdown_result(result, execution_time)
        else:  # text format (default)
            self._display_text_result(result, execution_time)
    
    def _display_text_result(self, result: Dict[str, Any], execution_time: float):
        """以文本格式显示结果"""
        if result.get("success", False):
            message = result.get("message", "执行成功")
            
            # 检查是否有意图感知的响应
            intent_info = result.get("intent_info")
            if intent_info and intent_info.get("intent_type") == "SUMMARY_INFO":
                print(f"✅ {message}")
            else:
                print(f"✅ {message}")
                
            # 显示提取的内容
            if not (intent_info and intent_info.get("intent_type") == "SUMMARY_INFO" and message and message != "执行成功"):
                content = result.get("content") or result.get("extracted_content")
                if content:
                    self._display_extracted_content(content)
        else:
            error_msg = result.get('error', '未知错误')
            print(f"❌ 执行失败: {error_msg}")
        
        print(f"⏱️  执行时间: {execution_time:.2f}秒")
    
    def _display_json_result(self, result: Dict[str, Any], execution_time: float):
        """以JSON格式显示结果"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "result": result
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    
    def _display_csv_result(self, result: Dict[str, Any], execution_time: float):
        """以CSV格式显示结果"""
        print("timestamp,execution_time,success,message,error")
        print(f"{datetime.now().isoformat()},{execution_time},{result.get('success', False)},\"{result.get('message', '')}\",\"{result.get('error', '')}\"")
        
        # 如果有提取的内容，也以CSV格式显示
        content = result.get("content") or result.get("extracted_content")
        if content and isinstance(content, list):
            print("\n--- 提取的内容 ---")
            print("index,title,description,url")
            for i, item in enumerate(content):
                if isinstance(item, dict):
                    title = item.get('title', '').replace('"', '""')
                    desc = item.get('description', '').replace('"', '""')
                    url = item.get('url', '').replace('"', '""')
                    print(f"{i},\"{title}\",\"{desc}\",\"{url}\"")
    
    def _display_markdown_result(self, result: Dict[str, Any], execution_time: float):
        """以Markdown格式显示结果"""
        print(f"## 执行结果")
        print(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"**执行时间**: {execution_time:.2f}秒")
        print(f"**状态**: {'✅ 成功' if result.get('success', False) else '❌ 失败'}")
        
        if result.get("success", False):
            message = result.get("message", "执行成功")
            print(f"**消息**: {message}")
            
            # 显示提取的内容
            content = result.get("content") or result.get("extracted_content")
            if content:
                print(f"\n### 提取的内容")
                if isinstance(content, list):
                    for i, item in enumerate(content, 1):
                        if isinstance(item, dict):
                            print(f"\n#### {i}. {item.get('title', '无标题')}")
                            if item.get('description'):
                                print(f"**描述**: {item.get('description')}")
                            if item.get('url'):
                                print(f"**链接**: [{item.get('url')}]({item.get('url')})")
                else:
                    print(f"```\n{content}\n```")
        else:
            error_msg = result.get('error', '未知错误')
            print(f"**错误**: {error_msg}")
        
        print("\n---")
    
    def _display_error(self, error_msg: str):
        """显示错误信息"""
        if self.output_format == "json":
            error_output = {
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": error_msg
            }
            print(json.dumps(error_output, ensure_ascii=False, indent=2))
        elif self.output_format == "csv":
            print("timestamp,success,error")
            print(f"{datetime.now().isoformat()},false,\"{error_msg}\"")
        elif self.output_format == "markdown":
            print(f"## 执行错误")
            print(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"**错误**: {error_msg}")
            print("\n---")
        else:
            print(f"❌ 处理自然语言文本时发生错误: {error_msg}")
    
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

