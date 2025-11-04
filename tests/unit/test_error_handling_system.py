#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理系统综合测试

测试完整的错误处理和恢复系统，包括异常处理框架、智能恢复管理器和集成错误处理器。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime

from src.common.exceptions import (
    BrowserAgentError, ErrorContext, ErrorCategory, ErrorSeverity,
    ElementNotFoundError, TimeoutError, NetworkError
)
from src.action.error_handler import ErrorHandler
from src.action.recovery_manager import RecoveryManager, RecoveryStrategy
from src.action.error_integration import IntegratedErrorHandler, get_integrated_error_handler


class TestErrorHandlingSystem(unittest.TestCase):
    """错误处理系统综合测试"""
    
    def setUp(self):
        """测试前准备"""
        self.error_handler = ErrorHandler()
        self.recovery_manager = RecoveryManager()
        self.integrated_handler = IntegratedErrorHandler()
        
        # 模拟指令和上下文
        self.test_instruction = {
            "action": "click",
            "selector": "#test-button",
            "description": "点击测试按钮"
        }
        
        self.test_context = {
            "page_url": "https://example.com",
            "page_title": "测试页面",
            "session_id": "test_session_123"
        }
    
    def test_exception_framework(self):
        """测试异常处理框架"""
        
        # 测试自定义异常创建
        context = ErrorContext()
        context.set_page_context("https://example.com", "测试页面")
        
        error = ElementNotFoundError("#missing-element", context=context)
        
        self.assertEqual(error.category, ErrorCategory.BROWSER)
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertIn("无法找到元素", error.message)
        self.assertTrue(len(error.recovery_suggestions) > 0)
        
        # 测试错误转换为字典
        error_dict = error.to_dict()
        self.assertIn("error_type", error_dict)
        self.assertIn("category", error_dict)
        self.assertIn("context", error_dict)
        self.assertIn("recovery_suggestions", error_dict)
    
    def test_error_handler_basic_functionality(self):
        """测试错误处理器基本功能"""
        
        # 创建测试异常
        test_error = ElementNotFoundError("#test-element")
        
        # 处理错误
        result = self.error_handler.handle_error(
            test_error, self.test_instruction, self.test_context
        )
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("error_id", result)
        self.assertIn("diagnosis", result)
        self.assertIn("recovery_suggestions", result)
        self.assertEqual(result["category"], "browser")
        
        # 验证错误报告被创建
        reports = self.error_handler.get_error_reports(limit=10)
        self.assertTrue(len(reports) > 0)
        self.assertEqual(reports[0]["error_id"], result["error_id"])
    
    def test_recovery_manager_plan_creation(self):
        """测试恢复管理器计划创建"""
        
        # 创建测试错误
        test_error = TimeoutError("页面加载", 30.0)
        
        # 创建恢复计划
        plan = self.recovery_manager.create_recovery_plan(test_error, self.test_context)
        
        # 验证计划
        self.assertIsNotNone(plan.plan_id)
        self.assertTrue(len(plan.strategies) > 0)
        self.assertIn(RecoveryStrategy.EXPONENTIAL_BACKOFF, plan.strategies)
        
        # 验证计划存储
        stored_plan = self.recovery_manager.get_recovery_status(plan.plan_id)
        self.assertIsNotNone(stored_plan)
        self.assertEqual(stored_plan["plan_id"], plan.plan_id)
    
    def test_recovery_manager_execution(self):
        """测试恢复管理器执行"""
        
        # 创建模拟执行器回调
        mock_executor = Mock()
        mock_executor.return_value = {"success": True, "message": "恢复成功"}
        
        # 创建测试错误和计划
        test_error = ElementNotFoundError("#test-element")
        plan = self.recovery_manager.create_recovery_plan(test_error, self.test_context)
        
        # 执行恢复计划
        result = self.recovery_manager.execute_recovery_plan(plan.plan_id, mock_executor)
        
        # 验证执行结果
        self.assertTrue(result["success"])
        self.assertIn("strategy_used", result)
        
        # 验证执行器被调用
        self.assertTrue(mock_executor.called)
    
    def test_integrated_error_handler(self):
        """测试集成错误处理器"""
        
        # 创建模拟执行器回调
        mock_executor = Mock()
        mock_executor.return_value = {"success": True, "message": "自动恢复成功"}
        
        # 创建测试异常
        test_exception = Exception("测试异常")
        
        # 使用集成处理器处理错误
        result = self.integrated_handler.handle_error_with_recovery(
            test_exception, self.test_instruction, self.test_context,
            executor_callback=mock_executor, auto_recovery=True
        )
        
        # 验证结果包含恢复信息
        self.assertIn("auto_recovery_attempted", result)
        self.assertIn("final_status", result)
        
        # 如果有恢复计划，验证自动恢复
        if result.get("recovery_plan"):
            self.assertTrue(result.get("auto_recovery_attempted", False))
    
    def test_error_statistics(self):
        """测试错误统计功能"""
        
        # 处理多个错误
        errors = [
            ElementNotFoundError("#element1"),
            TimeoutError("操作1", 10.0),
            NetworkError("网络连接失败")
        ]
        
        for error in errors:
            self.error_handler.handle_error(error, self.test_instruction, self.test_context)
        
        # 获取统计信息
        stats = self.error_handler.get_error_statistics()
        
        # 验证统计信息
        self.assertEqual(stats["total_errors"], 3)
        self.assertIn("errors_by_category", stats)
        self.assertIn("errors_by_severity", stats)
        
        # 验证分类统计
        self.assertTrue(stats["errors_by_category"]["browser"] >= 1)
        self.assertTrue(stats["errors_by_category"]["timeout"] >= 1)
        self.assertTrue(stats["errors_by_category"]["network"] >= 1)
    
    def test_user_feedback_mechanism(self):
        """测试用户反馈机制"""
        
        # 创建错误
        test_error = ElementNotFoundError("#feedback-test")
        result = self.error_handler.handle_error(
            test_error, self.test_instruction, self.test_context
        )
        
        error_id = result["error_id"]
        
        # 提供用户反馈
        feedback_result = self.integrated_handler.provide_user_feedback(
            error_id, "用户已手动解决此问题"
        )
        
        # 验证反馈记录
        self.assertTrue(feedback_result["success"])
        
        # 验证反馈被保存
        report = self.integrated_handler.get_error_report(error_id)
        self.assertIsNotNone(report)
        self.assertEqual(report["user_feedback"], "用户已手动解决此问题")
    
    def test_recovery_suggestions(self):
        """测试恢复建议功能"""
        
        # 创建不同类型的错误，验证建议
        test_cases = [
            (ElementNotFoundError("#missing"), "等待元素加载"),
            (TimeoutError("超时操作", 30.0), "增加超时时间"),
            (NetworkError("连接失败"), "检查网络连接")
        ]
        
        for error, expected_suggestion in test_cases:
            result = self.error_handler.handle_error(
                error, self.test_instruction, self.test_context
            )
            
            suggestions = result["recovery_suggestions"]
            self.assertTrue(len(suggestions) > 0)
            
            # 验证包含预期建议
            suggestion_texts = [s.get("description", "") for s in suggestions]
            self.assertTrue(
                any(expected_suggestion in text for text in suggestion_texts),
                f"未找到预期建议: {expected_suggestion}"
            )
    
    def test_error_export_and_import(self):
        """测试错误报告导出功能"""
        
        # 创建一些错误
        for i in range(3):
            error = ElementNotFoundError(f"#element-{i}")
            self.error_handler.handle_error(
                error, self.test_instruction, self.test_context
            )
        
        # 导出报告
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            self.integrated_handler.export_comprehensive_report(export_path)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(export_path))
            
            # 验证文件内容
            import json
            with open(export_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn("export_info", data)
            self.assertIn("statistics", data)
            self.assertIn("error_reports", data)
            self.assertTrue(len(data["error_reports"]) >= 3)
            
        finally:
            # 清理临时文件
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    def test_circuit_breaker_functionality(self):
        """测试熔断器功能"""
        
        # 创建会失败的执行器
        failing_executor = Mock()
        failing_executor.side_effect = Exception("持续失败")
        
        # 创建多个相同类型的错误来触发熔断器
        for i in range(6):  # 超过默认阈值5
            error = NetworkError("网络错误")
            plan = self.recovery_manager.create_recovery_plan(error, self.test_context)
            
            try:
                self.recovery_manager.execute_recovery_plan(plan.plan_id, failing_executor)
            except:
                pass  # 忽略失败，我们只是想触发熔断器
        
        # 验证熔断器统计
        stats = self.recovery_manager.get_recovery_statistics()
        self.assertTrue(stats["circuit_breaker_trips"] > 0)
    
    def test_global_error_handler_singleton(self):
        """测试全局错误处理器单例"""
        
        # 获取两个实例
        handler1 = get_integrated_error_handler()
        handler2 = get_integrated_error_handler()
        
        # 验证是同一个实例
        self.assertIs(handler1, handler2)
        
        # 验证功能正常
        self.assertIsInstance(handler1, IntegratedErrorHandler)
    
    def test_performance_monitoring_integration(self):
        """测试性能监控集成"""
        
        # 创建错误并处理
        start_time = time.time()
        
        test_error = TimeoutError("性能测试", 10.0)
        result = self.error_handler.handle_error(
            test_error, self.test_instruction, self.test_context
        )
        
        end_time = time.time()
        
        # 验证处理时间合理
        processing_time = end_time - start_time
        self.assertLess(processing_time, 1.0)  # 应该在1秒内完成
        
        # 验证结果包含时间戳
        self.assertIn("timestamp", result)
        
        # 验证时间戳格式
        timestamp = datetime.fromisoformat(result["timestamp"])
        self.assertIsInstance(timestamp, datetime)


if __name__ == '__main__':
    unittest.main()