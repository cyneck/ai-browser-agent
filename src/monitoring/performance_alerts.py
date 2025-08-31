#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能告警系统

监控关键性能指标并在异常时发出告警，包括：
- LLM响应时间异常
- 浏览器操作超时
- 内存使用率过高
- 错误率激增
- API调用频率异常
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.common.logger import get_logger
from src.common.performance_monitor import get_performance_monitor


@dataclass
class AlertRule:
    """告警规则配置"""
    name: str
    metric_type: str  # 'llm', 'browser', 'system'
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration: int  # 持续时间（秒）
    severity: str  # 'info', 'warning', 'critical'
    message: str
    enabled: bool = True


@dataclass
class Alert:
    """告警信息"""
    id: str
    rule_name: str
    severity: str
    message: str
    timestamp: datetime
    value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class PerformanceAlertManager:
    """性能告警管理器"""
    
    def __init__(self, check_interval: float = 5.0):
        """
        初始化告警管理器
        
        Args:
            check_interval: 检查间隔（秒）
        """
        self.logger = get_logger()
        self.perf_monitor = get_performance_monitor()
        self.check_interval = check_interval
        self.running = False
        self._thread = None
        
        # 告警规则
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # 告警回调
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 默认告警规则
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认告警规则"""
        default_rules = [
            AlertRule(
                name="LLM响应时间过长",
                metric_type="llm",
                threshold=10.0,  # 10秒
                comparison="gt",
                duration=30,
                severity="warning",
                message="LLM响应时间超过10秒，可能影响用户体验"
            ),
            AlertRule(
                name="LLM响应时间严重超时",
                metric_type="llm",
                threshold=30.0,  # 30秒
                comparison="gt",
                duration=60,
                severity="critical",
                message="LLM响应时间超过30秒，系统性能严重下降"
            ),
            AlertRule(
                name="浏览器操作超时",
                metric_type="browser",
                threshold=15.0,  # 15秒
                comparison="gt",
                duration=45,
                severity="warning",
                message="浏览器操作平均执行时间超过15秒"
            ),
            AlertRule(
                name="内存使用率过高",
                metric_type="system",
                threshold=500.0,  # 500MB
                comparison="gt",
                duration=120,
                severity="warning",
                message="内存使用超过500MB，可能存在内存泄漏"
            ),
            AlertRule(
                name="错误率过高",
                metric_type="system",
                threshold=20.0,  # 20%
                comparison="gt",
                duration=60,
                severity="critical",
                message="系统错误率超过20%，需要立即检查"
            ),
            AlertRule(
                name="API调用频率异常",
                metric_type="llm",
                threshold=60.0,  # 每分钟60次
                comparison="gt",
                duration=60,
                severity="warning",
                message="LLM调用频率过高，可能触发API限制"
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
        self.logger.info(f"添加告警规则: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        self.logger.info(f"移除告警规则: {rule_name}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self):
        """开始告警监控"""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            self.logger.info("性能告警系统已启动")
    
    def stop_monitoring(self):
        """停止告警监控"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.logger.info("性能告警系统已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._check_all_rules()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"告警监控循环出错: {e}")
                time.sleep(self.check_interval)
    
    def _check_all_rules(self):
        """检查所有告警规则"""
        current_metrics = self.perf_monitor.get_summary()
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                value = self._get_metric_value(rule.metric_type, current_metrics)
                if value is None:
                    continue
                
                if self._evaluate_rule(rule, value):
                    self._trigger_alert(rule, value)
                else:
                    self._resolve_alert(rule.name)
                    
            except Exception as e:
                self.logger.error(f"检查规则 {rule.name} 时出错: {e}")
    
    def _get_metric_value(self, metric_type: str, metrics: Dict[str, Any]) -> Optional[float]:
        """获取指标值"""
        try:
            if metric_type == "llm":
                llm_metrics = self.perf_monitor.get_llm_metrics()
                return llm_metrics.get("avg_response_time", 0)
            
            elif metric_type == "browser":
                browser_metrics = self.perf_monitor.get_browser_metrics()
                return browser_metrics.get("avg_execution_time", 0)
            
            elif metric_type == "system":
                system_metrics = self.perf_monitor.get_system_metrics()
                if "memory_usage_mb" in system_metrics:
                    return system_metrics["memory_usage_mb"]
                elif "error_rate" in metrics:
                    return metrics["error_rate"]
            
            return None
            
        except Exception:
            return None
    
    def _evaluate_rule(self, rule: AlertRule, value: float) -> bool:
        """评估规则是否触发"""
        if rule.comparison == "gt":
            return value > rule.threshold
        elif rule.comparison == "lt":
            return value < rule.threshold
        elif rule.comparison == "eq":
            return value == rule.threshold
        return False
    
    def _trigger_alert(self, rule: AlertRule, value: float):
        """触发告警"""
        if rule.name in self.active_alerts:
            # 更新现有告警
            alert = self.active_alerts[rule.name]
            alert.timestamp = datetime.now()
            alert.value = value
        else:
            # 创建新告警
            alert = Alert(
                id=f"{rule.name}_{int(time.time())}",
                rule_name=rule.name,
                severity=rule.severity,
                message=rule.message,
                timestamp=datetime.now(),
                value=value,
                threshold=rule.threshold
            )
            self.active_alerts[rule.name] = alert
            self.alert_history.append(alert)
            
            self.logger.warning(f"告警触发: {rule.name} (值: {value}, 阈值: {rule.threshold})")
            
            # 执行回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"执行告警回调时出错: {e}")
    
    def _resolve_alert(self, rule_name: str):
        """解决告警"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[rule_name]
            
            self.logger.info(f"告警解决: {rule_name}")
            
            # 执行解决回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"执行告警解决回调时出错: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        return self.alert_history[-limit:]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        active_alerts = self.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == "critical"]
        warning_alerts = [a for a in active_alerts if a.severity == "warning"]
        
        return {
            "status": "healthy" if not active_alerts else "warning" if not critical_alerts else "critical",
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "warning_alerts": len(warning_alerts),
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules if r.enabled])
        }


class AlertNotifier:
    """告警通知器"""
    
    @staticmethod
    def console_notifier(alert: Alert):
        """控制台告警通知"""
        if not alert.resolved:
            print(f"🚨 [{alert.severity.upper()}] {alert.message}")
            print(f"   当前值: {alert.value}, 阈值: {alert.threshold}")
            print(f"   时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"✅ 告警已解决: {alert.rule_name}")
    
    @staticmethod
    def file_notifier(log_file: str):
        """文件告警通知"""
        def notifier(alert: Alert):
            with open(log_file, 'a', encoding='utf-8') as f:
                status = "RESOLVED" if alert.resolved else "TRIGGERED"
                f.write(f"[{status}] {alert.severity.upper()} - {alert.message}")
                f.write(f" | Value: {alert.value}, Threshold: {alert.threshold}")
                f.write(f" | Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return notifier


# 全局告警管理器实例
_alert_manager: Optional[PerformanceAlertManager] = None


def get_alert_manager() -> PerformanceAlertManager:
    """获取全局告警管理器实例"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = PerformanceAlertManager()
    return _alert_manager