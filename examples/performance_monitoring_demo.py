#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能监控系统使用示例

演示如何集成和使用新的性能监控功能，包括：
- 性能指标收集
- 告警系统配置
- 仪表板使用
- 实时监控
"""

import time
import asyncio
from datetime import datetime
from pathlib import Path

from src.common.performance_monitor import get_performance_monitor
from src.monitoring.performance_alerts import get_alert_manager, AlertRule, AlertNotifier
from src.monitoring.performance_dashboard import get_performance_dashboard
from src.action.executor import ActionExecutor
from src.reasoning.instruction_builder import InstructionBuilder


class PerformanceMonitoringDemo:
    """性能监控演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.perf_monitor = get_performance_monitor()
        self.alert_manager = get_alert_manager()
        self.dashboard = get_performance_dashboard()
        
        # 重置所有监控状态
        self.perf_monitor.reset()
        self.alert_manager.stop_monitoring()
        self.dashboard.stop_monitoring()
        
    def setup_monitoring(self):
        """设置监控系统"""
        print("🚀 设置性能监控系统...")
        
        # 添加自定义告警规则
        custom_rule = AlertRule(
            name="演示告警规则",
            metric_type="llm",
            threshold=3.0,
            comparison="gt",
            duration=2,
            severity="warning",
            message="LLM响应时间超过3秒，可能影响用户体验"
        )
        self.alert_manager.add_rule(custom_rule)
        
        # 添加控制台通知
        self.alert_manager.add_alert_callback(AlertNotifier.console_notifier)
        
        # 添加文件通知
        log_file = Path("performance_alerts.log")
        file_notifier = AlertNotifier.file_notifier(str(log_file))
        self.alert_manager.add_alert_callback(file_notifier)
        
        # 启动监控
        self.alert_manager.start_monitoring()
        self.dashboard.start_monitoring()
        
        print("✅ 监控系统已启动")
        print(f"📊 告警日志将保存到: {log_file.absolute()}")
    
    def simulate_llm_calls(self, num_calls: int = 5):
        """模拟LLM调用"""
        print(f"\n🤖 模拟 {num_calls} 次LLM调用...")
        
        for i in range(num_calls):
            # 模拟不同响应时间
            response_time = 0.5 + i * 0.5
            
            start_time = time.time()
            self.perf_monitor.record_llm_call(
                prompt_tokens=50 + i * 10,
                completion_tokens=20 + i * 5,
                response_time=response_time,
                model_name="gemini-pro",
                success=True
            )
            
            print(f"  LLM调用 {i+1}: 响应时间 {response_time:.2f}s")
            time.sleep(0.5)
    
    def simulate_browser_actions(self, num_actions: int = 5):
        """模拟浏览器操作"""
        print(f"\n🌐 模拟 {num_actions} 次浏览器操作...")
        
        actions = ["navigate", "click", "fill", "screenshot", "extract"]
        
        for i, action in enumerate(actions[:num_actions]):
            execution_time = 0.3 + i * 0.2
            page_load_time = 0.1 + i * 0.1
            
            self.perf_monitor.record_browser_action(
                action_type=action,
                selector=f"#{action}-element",
                execution_time=execution_time,
                page_load_time=page_load_time,
                success=True
            )
            
            print(f"  {action}操作: 执行时间 {execution_time:.2f}s, 页面加载 {page_load_time:.2f}s")
            time.sleep(0.3)
    
    def simulate_errors(self, num_errors: int = 3):
        """模拟错误情况"""
        print(f"\n❌ 模拟 {num_errors} 次错误...")
        
        for i in range(num_errors):
            # LLM调用失败
            self.perf_monitor.record_llm_call(
                prompt_tokens=100,
                completion_tokens=0,
                response_time=5.0 + i,
                model_name="gemini-pro",
                success=False,
                error_message=f"API超时错误 {i+1}"
            )
            
            # 浏览器操作失败
            self.perf_monitor.record_browser_action(
                action_type="click",
                selector="#missing-element",
                execution_time=2.0 + i,
                page_load_time=1.0,
                success=False,
                error_message=f"元素未找到 {i+1}"
            )
            
            print(f"  错误 {i+1}: LLM和浏览器操作失败")
            time.sleep(0.5)
    
    def display_current_metrics(self):
        """显示当前性能指标"""
        print("\n📊 当前性能指标:")
        print("-" * 50)
        
        llm_metrics = self.perf_monitor.get_llm_metrics()
        browser_metrics = self.perf_monitor.get_browser_metrics()
        system_metrics = self.perf_monitor.get_system_metrics()
        summary = self.perf_monitor.get_summary()
        
        print("LLM指标:")
        print(f"  总调用次数: {llm_metrics['total_calls']}")
        print(f"  成功调用: {llm_metrics['successful_calls']}")
        print(f"  失败调用: {llm_metrics['failed_calls']}")
        print(f"  平均响应时间: {llm_metrics['avg_response_time']:.2f}s")
        print(f"  总token使用量: {llm_metrics['total_prompt_tokens'] + llm_metrics['total_completion_tokens']}")
        
        print("\n浏览器操作指标:")
        print(f"  总操作次数: {browser_metrics['total_actions']}")
        print(f"  成功操作: {browser_metrics['successful_actions']}")
        print(f"  失败操作: {browser_metrics['failed_actions']}")
        print(f"  平均执行时间: {browser_metrics['avg_execution_time']:.2f}s")
        print(f"  平均页面加载时间: {browser_metrics['avg_page_load_time']:.2f}s")
        
        print("\n系统指标:")
        print(f"  内存使用: {system_metrics['memory_usage_mb']:.1f}MB")
        print(f"  CPU使用率: {system_metrics['cpu_usage_percent']:.1f}%")
        print(f"  运行时间: {system_metrics['uptime_seconds']:.0f}s")
        
        print("\n性能摘要:")
        print(f"  总操作数: {summary['total_operations']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        print(f"  平均响应时间: {summary['avg_response_time']:.2f}s")
    
    def display_alert_status(self):
        """显示告警状态"""
        print("\n🚨 告警状态:")
        print("-" * 30)
        
        status = self.alert_manager.get_status_summary()
        print(f"系统状态: {status['status']}")
        print(f"活跃告警: {status['active_alerts']}")
        print(f"严重告警: {status['critical_alerts']}")
        print(f"警告告警: {status['warning_alerts']}")
        
        active_alerts = self.alert_manager.get_active_alerts()
        if active_alerts:
            print("\n活跃告警详情:")
            for alert in active_alerts:
                print(f"  - {alert.rule_name}: {alert.message}")
        else:
            print("  无活跃告警")
    
    def generate_reports(self):
        """生成性能报告"""
        print("\n📈 生成性能报告...")
        
        # HTML报告
        html_path = self.dashboard.generate_html_report()
        print(f"  HTML报告已生成: {html_path}")
        
        # JSON报告
        json_path = self.dashboard.export_metrics_json()
        print(f"  JSON报告已生成: {json_path}")
        
        # 性能数据导出
        export_path = Path("performance_data.json")
        self.perf_monitor.export_metrics(str(export_path))
        print(f"  性能数据已导出: {export_path.absolute()}")
    
    def run_demo(self):
        """运行完整演示"""
        print("🎯 AI浏览器代理 - 性能监控系统演示")
        print("=" * 50)
        
        try:
            # 1. 设置监控系统
            self.setup_monitoring()
            
            # 2. 模拟正常操作
            self.simulate_llm_calls(3)
            self.simulate_browser_actions(3)
            
            # 3. 显示当前指标
            self.display_current_metrics()
            
            # 4. 模拟异常情况（触发告警）
            print("\n⚠️  模拟异常情况以触发告警...")
            self.simulate_llm_calls(2)  # 包含较慢的响应
            self.simulate_errors(2)
            
            # 等待告警触发
            time.sleep(3)
            
            # 5. 显示告警状态
            self.display_alert_status()
            
            # 6. 生成报告
            self.generate_reports()
            
            print("\n✅ 演示完成！")
            print("\n下一步操作:")
            print("1. 打开生成的HTML报告查看详细图表")
            print("2. 查看 performance_alerts.log 了解告警详情")
            print("3. 使用性能数据文件进行进一步分析")
            
        finally:
            # 清理
            self.alert_manager.stop_monitoring()
            self.dashboard.stop_monitoring()


def main():
    """主函数"""
    demo = PerformanceMonitoringDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()