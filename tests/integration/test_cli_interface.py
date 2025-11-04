#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI界面集成测试

测试命令行界面的完整功能，包括用户交互、输出格式、命令历史等。
"""

import unittest
import sys
import os
import io
import tempfile
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.api.cli import CLIInterface


class TestCLIInterface(unittest.TestCase):
    """CLI界面集成测试类"""

    def setUp(self):
        """测试前准备"""
        self.cli = CLIInterface()
        
        # 模拟BrowserAgent
        self.mock_agent = Mock()
        self.mock_agent.initialize = Mock()
        self.mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "执行成功",
            "content": "测试内容"
        })
        self.mock_agent.cleanup = Mock()
        
        # 替换CLI中的agent
        self.cli.agent = self.mock_agent

    def tearDown(self):
        """测试后清理"""
        # 清理会话状态
        self.cli.session_state.clear()
        self.cli.command_history.clear()

    def test_cli_initialization(self):
        """测试CLI初始化"""
        cli = CLIInterface(output_format="json")
        self.assertEqual(cli.output_format, "json")
        self.assertEqual(cli.session_state, {})
        self.assertIsInstance(cli.command_history, list)
        self.assertIsInstance(cli.common_commands, list)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_single_command_execution(self, mock_stdout, mock_input):
        """测试单条命令执行"""
        # 模拟用户输入
        mock_input.side_effect = ["打开百度", "exit"]
        
        # 执行CLI
        try:
            self.cli.start()
        except SystemExit:
            pass
        
        # 验证代理方法被调用
        self.mock_agent.initialize.assert_called_once()
        self.mock_agent.execute.assert_called_once_with("打开百度", {})
        self.mock_agent.cleanup.assert_called_once()
        
        # 验证输出包含成功信息
        output = mock_stdout.getvalue()
        self.assertIn("执行成功", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_multiple_commands_execution(self, mock_stdout, mock_input):
        """测试多条命令执行"""
        # 模拟用户输入多条命令
        mock_input.side_effect = [
            "打开百度",
            "搜索Python",
            "点击第一个结果",
            "exit"
        ]
        
        # 执行CLI
        try:
            self.cli.start()
        except SystemExit:
            pass
        
        # 验证代理方法被多次调用
        self.assertEqual(self.mock_agent.execute.call_count, 3)
        
        # 验证命令历史记录
        self.assertEqual(len(self.cli.command_history), 3)
        self.assertIn("打开百度", self.cli.command_history)
        self.assertIn("搜索Python", self.cli.command_history)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_special_commands(self, mock_stdout, mock_input):
        """测试特殊命令处理"""
        # 测试帮助命令
        mock_input.side_effect = ["帮助", "exit"]
        
        try:
            self.cli.start()
        except SystemExit:
            pass
        
        output = mock_stdout.getvalue()
        self.assertIn("命令帮助", output)
        self.assertIn("常用网页操作", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_output_format_change(self, mock_stdout, mock_input):
        """测试输出格式切换"""
        # 测试切换到JSON格式
        mock_input.side_effect = ["格式 json", "打开百度", "exit"]
        
        try:
            self.cli.start()
        except SystemExit:
            pass
        
        # 验证格式已切换
        self.assertEqual(self.cli.output_format, "json")
        
        output = mock_stdout.getvalue()
        self.assertIn("输出格式已更改为: json", output)

    def test_direct_execution(self):
        """测试直接执行单条指令"""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli.initialize_and_execute("打开百度")
            
            # 验证代理方法被调用
            self.mock_agent.initialize.assert_called_once()
            self.mock_agent.execute.assert_called_once_with("打开百度", {})
            self.mock_agent.cleanup.assert_called_once()
            
            output = mock_stdout.getvalue()
            self.assertIn("执行成功", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_interactive_text_mode(self, mock_stdout, mock_input):
        """测试交互式文本模式"""
        # 模拟交互式输入
        mock_input.side_effect = ["搜索Python", "点击第一个结果", "exit"]
        
        self.cli.start_interactive_text_mode("打开百度")
        
        # 验证初始指令和后续指令都被执行
        self.assertEqual(self.mock_agent.execute.call_count, 3)
        
        # 验证执行的指令
        calls = self.mock_agent.execute.call_args_list
        self.assertEqual(calls[0][0][0], "打开百度")  # 初始指令
        self.assertEqual(calls[1][0][0], "搜索Python")  # 第一个交互指令
        self.assertEqual(calls[2][0][0], "点击第一个结果")  # 第二个交互指令

    def test_error_handling(self):
        """测试错误处理"""
        # 模拟代理执行失败
        self.mock_agent.execute.side_effect = Exception("模拟错误")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli.initialize_and_execute("打开百度")
            
            output = mock_stdout.getvalue()
            self.assertIn("模拟错误", output)

    def test_different_output_formats(self):
        """测试不同输出格式"""
        test_result = {
            "success": True,
            "message": "执行成功",
            "content": [
                {"title": "测试标题", "description": "测试描述", "url": "https://test.com"}
            ]
        }
        self.mock_agent.execute.return_value = test_result
        
        # 测试文本格式
        self.cli.output_format = "text"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli._process_text("测试指令")
            output = mock_stdout.getvalue()
            self.assertIn("执行成功", output)
            self.assertIn("测试标题", output)
        
        # 测试JSON格式
        self.cli.output_format = "json"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli._process_text("测试指令")
            output = mock_stdout.getvalue()
            self.assertIn('"success": true', output)
        
        # 测试Markdown格式
        self.cli.output_format = "markdown"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli._process_text("测试指令")
            output = mock_stdout.getvalue()
            self.assertIn("## 执行结果", output)
            self.assertIn("**状态**: ✅ 成功", output)

    @patch('builtins.input')
    def test_keyboard_interrupt_handling(self, mock_input):
        """测试键盘中断处理"""
        # 模拟KeyboardInterrupt
        mock_input.side_effect = KeyboardInterrupt()
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli.start()
            
            output = mock_stdout.getvalue()
            self.assertIn("程序被用户中断", output)
            
            # 验证清理方法被调用
            self.mock_agent.cleanup.assert_called_once()

    def test_session_state_management(self):
        """测试会话状态管理"""
        # 模拟返回会话状态
        self.mock_agent.execute.return_value = {
            "success": True,
            "message": "执行成功",
            "session_state": {"current_url": "https://baidu.com", "step": 1}
        }
        
        self.cli._process_text("打开百度")
        
        # 验证会话状态被更新
        self.assertEqual(self.cli.session_state["current_url"], "https://baidu.com")
        self.assertEqual(self.cli.session_state["step"], 1)
        
        # 执行第二个指令，验证状态传递
        self.mock_agent.execute.return_value = {
            "success": True,
            "message": "搜索完成",
            "session_state": {"step": 2}
        }
        
        self.cli._process_text("搜索Python")
        
        # 验证状态被正确更新和合并
        self.assertEqual(self.cli.session_state["current_url"], "https://baidu.com")
        self.assertEqual(self.cli.session_state["step"], 2)

    @patch('readline.read_history_file')
    @patch('readline.write_history_file')
    def test_command_history_persistence(self, mock_write, mock_read):
        """测试命令历史持久化"""
        # 测试历史记录保存
        self.cli.command_history = ["打开百度", "搜索Python"]
        self.cli._save_history()
        
        # 验证写入历史文件被调用
        mock_write.assert_called_once()

    def test_command_completion(self):
        """测试命令自动补全"""
        # 测试补全功能
        matches = []
        
        # 模拟第一次调用
        result = self.cli._completer("打开", 0)
        if result:
            matches.append(result)
        
        # 验证补全结果
        self.assertTrue(any("打开" in match for match in matches if match))

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_status_command(self, mock_stdout, mock_input):
        """测试状态命令"""
        mock_input.side_effect = ["状态", "exit"]
        
        try:
            self.cli.start()
        except SystemExit:
            pass
        
        output = mock_stdout.getvalue()
        self.assertIn("当前状态", output)
        self.assertIn("输出格式", output)
        self.assertIn("命令历史", output)

    def test_content_extraction_display(self):
        """测试内容提取显示"""
        # 测试列表内容显示
        test_content = [
            {"title": "标题1", "description": "描述1", "url": "https://test1.com"},
            {"title": "标题2", "description": "描述2", "url": "https://test2.com"}
        ]
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli._display_extracted_content(test_content)
            
            output = mock_stdout.getvalue()
            self.assertIn("提取的内容", output)
            self.assertIn("标题1", output)
            self.assertIn("标题2", output)
            self.assertIn("https://test1.com", output)

    def test_long_content_truncation(self):
        """测试长内容截断"""
        # 测试长描述截断
        long_description = "a" * 150  # 超过100字符的描述
        test_content = [
            {"title": "测试标题", "description": long_description, "url": "https://test.com"}
        ]
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli._display_extracted_content(test_content)
            
            output = mock_stdout.getvalue()
            self.assertIn("...", output)  # 应该包含截断标记

    def test_csv_output_format(self):
        """测试CSV输出格式"""
        self.cli.output_format = "csv"
        test_result = {
            "success": True,
            "message": "执行成功",
            "content": [
                {"title": "标题1", "description": "描述1", "url": "https://test1.com"}
            ]
        }
        self.mock_agent.execute.return_value = test_result
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.cli._process_text("测试指令")
            
            output = mock_stdout.getvalue()
            self.assertIn("timestamp,execution_time,success", output)
            self.assertIn("true", output)

    @patch('os.system')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_clear_screen_command(self, mock_stdout, mock_input, mock_system):
        """测试清屏命令"""
        mock_input.side_effect = ["清屏", "exit"]
        
        try:
            self.cli.start()
        except SystemExit:
            pass
        
        # 验证系统清屏命令被调用
        mock_system.assert_called()


class TestCLIInterfacePerformance(unittest.TestCase):
    """CLI界面性能测试类"""

    def setUp(self):
        """测试前准备"""
        self.cli = CLIInterface()
        
        # 模拟快速响应的代理
        self.mock_agent = Mock()
        self.mock_agent.initialize = Mock()
        self.mock_agent.execute = Mock(return_value={
            "success": True,
            "message": "执行成功"
        })
        self.mock_agent.cleanup = Mock()
        self.cli.agent = self.mock_agent

    def test_command_processing_speed(self):
        """测试命令处理速度"""
        start_time = time.time()
        
        # 执行多个命令
        for i in range(10):
            self.cli._process_text(f"测试命令{i}")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证处理时间合理（应该很快）
        self.assertLess(processing_time, 1.0)  # 10个命令应该在1秒内处理完

    def test_large_output_handling(self):
        """测试大量输出处理"""
        # 模拟大量内容输出
        large_content = [
            {"title": f"标题{i}", "description": f"描述{i}", "url": f"https://test{i}.com"}
            for i in range(100)
        ]
        
        self.mock_agent.execute.return_value = {
            "success": True,
            "message": "执行成功",
            "content": large_content
        }
        
        start_time = time.time()
        
        with patch('sys.stdout', new_callable=io.StringIO):
            self.cli._process_text("获取大量内容")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证大量输出处理时间合理
        self.assertLess(processing_time, 2.0)

    def test_memory_usage_with_history(self):
        """测试命令历史的内存使用"""
        import sys
        
        # 记录初始内存使用
        initial_size = sys.getsizeof(self.cli.command_history)
        
        # 添加大量命令历史
        for i in range(1000):
            self.cli.command_history.append(f"命令{i}")
        
        # 检查内存增长是否合理
        final_size = sys.getsizeof(self.cli.command_history)
        memory_growth = final_size - initial_size
        
        # 验证内存使用合理（不应该过度增长）
        self.assertLess(memory_growth, 1024 * 1024)  # 不应该超过1MB


if __name__ == "__main__":
    unittest.main(verbosity=2)