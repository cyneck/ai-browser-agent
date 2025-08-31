#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能监控系统测试用例

验证性能监控模块的准确性、可靠性和功能性，包括：
- 性能指标收集的准确性
- 告警系统的触发逻辑
- 数据存储和检索
- 边界条件处理
"""

import time
import json
import pytest
import tempfile
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path

from src.common.performance_monitor import (
    PerformanceMonitor, PerformanceMetrics, LLMMetrics, 
    BrowserActionMetrics, get_performance_monitor
)
from src.monitoring.performance_alerts import (
    PerformanceAlertManager, AlertRule, Alert, 
    AlertNotifier, get_alert_manager
)
from src.monitoring.performance_dashboard import PerformanceDashboard


def get_performance_dashboard():
    """获取性能仪表板实例"""
    return PerformanceDashboard()


class TestPerformanceMonitor:
    """性能监控模块测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.monitor = PerformanceMonitor()
        self.monitor.clear_history()
    
    def test_llm_metrics_recording(self):
        """测试LLM指标记录"""
        start_time = time.time()
        
        # 记录LLM调用
        self.monitor.record_llm_call(
            prompt_tokens=100,
            completion_tokens=50,
            response_time=2.5,
            model_name="gemini-pro",
            success=True
        )
        
        # 执行一个操作以确保有数据
        self.monitor.start_operation("test_operation")
        time.sleep(0.1)
        self.monitor.end_operation(success=True)
        
        # 验证LLM指标
        summary = self.monitor.get_summary()
        assert summary["total_llm_calls"] == 1
        assert abs(summary["avg_llm_response_time"] - 2.5) < 0.01
    
    def test_browser_action_metrics(self):
        """测试浏览器操作指标记录"""
        # 记录浏览器操作
        self.monitor.record_browser_action(
            action_type="click",
            selector="button#submit",
            execution_time=1.2,
            page_load_time=0.5,
            success=True
        )
        
        # 执行一个操作以确保有数据
        self.monitor.start_operation("test_operation")
        time.sleep(0.1)
        self.monitor.end_operation(success=True)
        
        summary = self.monitor.get_summary()
        
        assert summary["total_browser_actions"] == 1
        assert abs(summary["avg_browser_action_time"] - 1.2) < 0.01  # Browser action time, not operation time
    
    def test_system_metrics(self):
        """测试系统指标收集"""
        # 执行一个操作来记录系统指标
        self.monitor.start_operation("test_operation")
        time.sleep(0.1)
        self.monitor.end_operation(success=True)
        
        # 验证系统指标
        summary = self.monitor.get_summary()
        assert "avg_memory_usage_mb" in summary
        assert summary["avg_memory_usage_mb"] > 0
        assert "counters" in summary
    
    def test_performance_summary(self):
        """测试性能摘要"""
        # 添加一些测试数据
        self.monitor.record_llm_call(100, 50, 2.0, "test", True)
        self.monitor.record_browser_action("click", "#btn", 1.0, 0.5, True)
        
        # 执行一个操作以确保有数据
        self.monitor.start_operation("test_operation")
        time.sleep(0.1)
        self.monitor.end_operation(success=True)
        
        summary = self.monitor.get_summary()
        
        assert "total_operations" in summary
        assert "success_rate" in summary
        assert "avg_response_time" in summary
        assert 0 <= summary["success_rate"] <= 100
    
    def test_metrics_reset(self):
        """测试指标重置"""
        self.monitor.record_llm_call(100, 50, 2.0, "test", True)
        self.monitor.clear_history()
        
        summary = self.monitor.get_summary()
        assert summary["total_llm_calls"] == 0
    
    def test_memory_usage_tracking(self):
        """测试内存使用跟踪"""
        # 执行一个操作来记录内存使用
        self.monitor.start_operation("memory_test")
        # 分配一些内存
        data = [i for i in range(1000)]
        time.sleep(0.1)
        self.monitor.end_operation(success=True)
        
        # 验证内存使用被记录
        summary = self.monitor.get_summary()
        assert "avg_memory_usage_mb" in summary
        assert summary["avg_memory_usage_mb"] > 0
    
    def test_concurrent_access(self):
        """测试并发访问安全性"""
        def record_metrics():
            for i in range(10):
                self.monitor.record_llm_call(100, 50, 1.0, "test", True)
                self.monitor.record_browser_action("click", "#btn", 0.5, 0.2, True)
                time.sleep(0.01)
        
        threads = [threading.Thread(target=record_metrics) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        summary = self.monitor.get_summary()
        assert summary["total_llm_calls"] == 50
        assert summary["total_browser_actions"] == 50
    

class TestPerformanceAlerts:
    """性能告警系统测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.alert_manager = PerformanceAlertManager(check_interval=0.1)
        self.test_alerts = []
        
        # 添加测试回调
        def test_callback(alert: Alert):
            self.test_alerts.append(alert)
        
        self.alert_manager.add_alert_callback(test_callback)
    
    def test_alert_rule_creation(self):
        """测试告警规则创建"""
        rule = AlertRule(
            name="测试规则",
            metric_type="llm",
            threshold=5.0,
            comparison="gt",
            duration=1,
            severity="warning",
            message="测试告警"
        )
        
        self.alert_manager.add_rule(rule)
        
        assert len(self.alert_manager.rules) > 0
        assert any(r.name == "测试规则" for r in self.alert_manager.rules)
    
    def test_alert_triggering(self):
        """测试告警触发"""
        # 添加测试规则
        rule = AlertRule(
            name="LLM超时测试",
            metric_type="llm",
            threshold=1.0,
            comparison="gt",
            duration=0.1,
            severity="warning",
            message="LLM响应超时"
        )
        
        self.alert_manager.add_rule(rule)
        
        # 模拟LLM响应时间过长
        with patch.object(self.alert_manager.perf_monitor, 'get_llm_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "avg_response_time": 2.0,
                "total_calls": 1,
                "successful_calls": 1,
                "failed_calls": 0
            }
            
            # 启动监控并等待触发
            self.alert_manager.start_monitoring()
            time.sleep(0.2)
            self.alert_manager.stop_monitoring()
            
            # 验证告警被触发
            active_alerts = self.alert_manager.get_active_alerts()
            assert len(active_alerts) > 0
            assert any(a.rule_name == "LLM超时测试" for a in active_alerts)
    
    def test_alert_resolution(self):
        """测试告警解决"""
        # 创建测试告警
        alert = Alert(
            id="test_alert",
            rule_name="测试规则",
            severity="warning",
            message="测试告警",
            timestamp=datetime.now(),
            value=10.0,
            threshold=5.0
        )
        
        self.alert_manager.active_alerts["测试规则"] = alert
        
        # 解决告警
        self.alert_manager._resolve_alert("测试规则")
        
        assert len(self.alert_manager.get_active_alerts()) == 0
        assert alert.resolved == True
        assert alert.resolved_at is not None
    
    def test_multiple_rules(self):
        """测试多个规则同时工作"""
        rules = [
            AlertRule("规则1", "llm", 5.0, "gt", 0.1, "warning", "告警1"),
            AlertRule("规则2", "browser", 3.0, "gt", 0.1, "warning", "告警2")
        ]
        
        for rule in rules:
            self.alert_manager.add_rule(rule)
        
        # 模拟触发条件
        with patch.object(self.alert_manager.perf_monitor, 'get_llm_metrics') as mock_llm, \
             patch.object(self.alert_manager.perf_monitor, 'get_browser_metrics') as mock_browser:
            
            mock_llm.return_value = {"avg_response_time": 6.0, "total_calls": 1}
            mock_browser.return_value = {"avg_execution_time": 4.0, "total_actions": 1}
            
            self.alert_manager.start_monitoring()
            time.sleep(0.2)
            self.alert_manager.stop_monitoring()
            
            active_alerts = self.alert_manager.get_active_alerts()
            assert len(active_alerts) == 2
    
    def test_alert_history(self):
        """测试告警历史记录"""
        # 创建一些告警
        for i in range(3):
            alert = Alert(
                id=f"alert_{i}",
                rule_name=f"规则_{i}",
                severity="warning",
                message=f"告警{i}",
                timestamp=datetime.now(),
                value=i,
                threshold=1.0
            )
            self.alert_manager.alert_history.append(alert)
        
        history = self.alert_manager.get_alert_history(limit=2)
        assert len(history) == 2
    
    def test_rule_enabling_disabling(self):
        """测试规则启用/禁用"""
        rule = AlertRule(
            name="启用测试",
            metric_type="llm",
            threshold=1.0,
            comparison="gt",
            duration=0.1,
            severity="warning",
            message="测试"
        )
        
        self.alert_manager.add_rule(rule)
        
        # 禁用规则
        rule.enabled = False
        
        # 不应该触发告警
        self.alert_manager.start_monitoring()
        time.sleep(0.2)
        self.alert_manager.stop_monitoring()
        
        assert len(self.alert_manager.get_active_alerts()) == 0
    
    def test_notifier_system(self):
        """测试通知系统"""
        notifications = []
        
        def custom_notifier(alert: Alert):
            notifications.append(alert)
        
        self.alert_manager.add_alert_callback(custom_notifier)
        
        # 添加一个规则
        rule = AlertRule(
            name="测试规则",
            metric_type="llm",
            threshold=1.0,
            comparison="gt",
            duration=0.1,
            severity="critical",
            message="测试告警"
        )
        self.alert_manager.add_rule(rule)
        
        # 模拟触发条件
        with patch.object(self.alert_manager.perf_monitor, 'get_llm_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "avg_response_time": 2.0,  # 大于阈值 1.0
                "total_calls": 1
            }
            
            # 手动触发检查
            self.alert_manager._check_all_rules()
        
        assert len(notifications) > 0


class TestPerformanceDashboard:
    """性能仪表板测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.dashboard = PerformanceDashboard(update_interval=0.1)
    
    def test_dashboard_initialization(self):
        """测试仪表板初始化"""
        assert self.dashboard.running == False
        assert len(self.dashboard.metrics_history) == 0
        assert self.dashboard.update_interval == 0.1
    
    def test_monitoring_start_stop(self):
        """测试监控启动停止"""
        self.dashboard.start_monitoring()
        assert self.dashboard.running == True
        
        time.sleep(0.2)
        
        self.dashboard.stop_monitoring()
        assert self.dashboard.running == False
    
    def test_metrics_collection(self):
        """测试指标收集"""
        self.dashboard.start_monitoring()
        time.sleep(0.3)
        self.dashboard.stop_monitoring()
        
        # 应该收集到一些指标
        assert len(self.dashboard.metrics_history) > 0
        
        latest = self.dashboard.get_realtime_metrics()
        assert "llm_metrics" in latest
        assert "browser_metrics" in latest
        assert "system_metrics" in latest
    
    def test_history_filtering(self):
        """测试历史数据过滤"""
        # 添加一些历史数据
        for i in range(5):
            self.dashboard.metrics_history.append({
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "metrics": {"test": i}
            })
        
        # 获取最近1小时的数据
        recent = self.dashboard.get_metrics_history(duration_hours=0.5)
        assert len(recent) <= 3  # 应该过滤掉较旧的数据
    
    def test_html_report_generation(self):
        """测试HTML报告生成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.html"
            
            generated_path = self.dashboard.generate_html_report(str(output_path))
            
            assert Path(generated_path).exists()
            assert Path(generated_path).stat().st_size > 0
            
            # 验证HTML内容
            with open(generated_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "AI浏览器代理 - 性能监控仪表板" in content
                assert "chart.js" in content  # 检查Chart.js引用
    
    def test_json_export(self):
        """测试JSON导出"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_metrics.json"
            
            exported_path = self.dashboard.export_metrics_json(str(output_path))
            
            assert Path(exported_path).exists()
            
            with open(exported_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert "export_time" in data
                assert "realtime_metrics" in data
                assert "history" in data
    
    def test_history_size_limit(self):
        """测试历史大小限制"""
        # 添加超过限制的测试数据
        for i in range(self.dashboard.max_history_size + 100):
            self.dashboard.metrics_history.append({
                "timestamp": datetime.now().isoformat(),
                "metrics": {"test": i}
            })
        
        # 强制执行历史限制
        self.dashboard._enforce_history_limit()
        
        # 应该被限制到最大大小
        assert len(self.dashboard.metrics_history) <= self.dashboard.max_history_size


class TestIntegration:
    """集成测试类"""
    
    def test_full_performance_pipeline(self):
        """测试完整的性能监控流程"""
        # 获取所有组件
        monitor = get_performance_monitor()
        alert_manager = get_alert_manager()
        dashboard = get_performance_dashboard()
        
        # 重置状态
        monitor.reset()
        alert_manager.stop_monitoring()
        dashboard.stop_monitoring()
        
        # 启动所有监控
        alert_manager.start_monitoring()
        dashboard.start_monitoring()
        
        try:
            # 模拟一些操作
            for i in range(5):
                monitor.record_llm_call(100, 50, 1.0 + i * 0.1, "test", True)
                monitor.record_browser_action("click", f"#btn{i}", 0.5 + i * 0.05, 0.2, True)
                
                # 添加实际操作记录
                monitor.start_operation(f"operation_{i}")
                time.sleep(0.01)  # 短暂的操作时间
                monitor.end_operation(success=True)
                
                time.sleep(0.1)
            
            # 验证数据一致性
            summary = monitor.get_summary()
            assert summary["total_operations"] == 5  # 5 operations
            assert summary["total_llm_calls"] == 5  # 5 LLM calls
            assert summary["total_browser_actions"] == 5  # 5 browser actions
            assert summary["success_rate"] == 1.0  # 100% success rate
            
            # 验证仪表板收集到数据
            time.sleep(0.2)
            assert len(dashboard.metrics_history) > 0
            
        finally:
            # 清理
            alert_manager.stop_monitoring()
            dashboard.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])