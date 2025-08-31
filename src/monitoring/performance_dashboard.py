#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能分析仪表板

提供实时性能监控和可视化展示功能，包括：
- LLM调用性能指标
- 浏览器操作性能指标
- 系统资源使用情况
- 实时性能图表展示
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.common.logger import get_logger
from src.common.performance_monitor import get_performance_monitor


class PerformanceDashboard:
    """性能分析仪表板类"""
    
    def __init__(self, update_interval: float = 1.0):
        """
        初始化性能仪表板
        
        Args:
            update_interval: 更新间隔（秒）
        """
        self.logger = get_logger()
        self.perf_monitor = get_performance_monitor()
        self.update_interval = update_interval
        self.running = False
        self._thread = None
        self.metrics_history = []
        self.max_history_size = 1000
        
        # HTML模板路径
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
    def start_monitoring(self):
        """开始性能监控"""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            self.logger.info("性能监控仪表板已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.logger.info("性能监控仪表板已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 收集当前性能指标
                metrics = self._collect_current_metrics()
                self.metrics_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                })
                
                # 限制历史记录大小
                self._enforce_history_limit()
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"性能监控循环出错: {e}")
                time.sleep(self.update_interval)
    
    def _collect_current_metrics(self) -> Dict[str, Any]:
        """收集当前性能指标"""
        return {
            "llm_metrics": self.perf_monitor.get_llm_metrics(),
            "browser_metrics": self.perf_monitor.get_browser_metrics(),
            "system_metrics": self.perf_monitor.get_system_metrics(),
            "summary": self.perf_monitor.get_summary()
        }
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """获取实时性能指标"""
        if self.metrics_history:
            return self.metrics_history[-1]["metrics"]
        return self._collect_current_metrics()
    
    def get_metrics_history(self, duration_hours: int = 1) -> List[Dict[str, Any]]:
        """获取指定时间范围内的历史指标"""
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)
        
        filtered_history = []
        for entry in self.metrics_history:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff_time:
                filtered_history.append(entry)
        
        return filtered_history
    
    def generate_html_report(self, output_path: Optional[str] = None) -> str:
        """生成HTML性能报告"""
        if output_path is None:
            output_path = self.template_dir / "performance_report.html"
        
        html_content = self._generate_html_template()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _generate_html_template(self) -> str:
        """生成HTML模板"""
        current_metrics = self.get_realtime_metrics()
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI浏览器代理 - 性能监控仪表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .dashboard {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .metric-card {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
        }}
        
        .metric-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2c3e50;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #3498db;
            margin-bottom: 0.5rem;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: #7f8c8d;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .chart-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2c3e50;
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }}
        
        .status-healthy {{ background: #27ae60; }}
        .status-warning {{ background: #f39c12; }}
        .status-critical {{ background: #e74c3c; }}
        
        .refresh-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 1rem;
        }}
        
        .refresh-btn:hover {{
            background: #2980b9;
        }}
        
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 AI浏览器代理 - 性能监控仪表板</h1>
        <p>实时监控系统性能指标</p>
    </div>
    
    <div class="dashboard">
        <button class="refresh-btn" onclick="refreshData()">🔄 刷新数据</button>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">LLM调用次数</div>
                <div class="metric-value" id="llm-calls">{current_metrics['llm_metrics']['total_calls']}</div>
                <div class="metric-label">总计调用</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">平均响应时间</div>
                <div class="metric-value" id="avg-response-time">{current_metrics['llm_metrics']['avg_response_time']:.2f}s</div>
                <div class="metric-label">LLM平均响应</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">浏览器操作</div>
                <div class="metric-value" id="browser-actions">{current_metrics['browser_metrics']['total_actions']}</div>
                <div class="metric-label">总计执行</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">平均执行时间</div>
                <div class="metric-value" id="avg-execution-time">{current_metrics['browser_metrics']['avg_execution_time']:.2f}s</div>
                <div class="metric-label">操作平均耗时</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">内存使用</div>
                <div class="metric-value" id="memory-usage">{current_metrics['system_metrics']['avg_memory_usage_mb']:.1f}MB</div>
                <div class="metric-label">当前内存占用</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">成功率</div>
                <div class="metric-value" id="success-rate">{current_metrics['summary']['success_rate']:.1f}%</div>
                <div class="metric-label">总体成功率</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">LLM调用趋势</div>
            <canvas id="llm-chart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">浏览器操作性能</div>
            <canvas id="browser-chart" width="400" height="200"></canvas>
        </div>
        
        <div class="timestamp">
            最后更新: <span id="last-update">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
    </div>
    
    <script>
        let llmChart, browserChart;
        
        function initCharts() {{
            // LLM调用趋势图
            const llmCtx = document.getElementById('llm-chart').getContext('2d');
            llmChart = new Chart(llmCtx, {{
                type: 'line',
                data: {{
                    labels: [],
                    datasets: [{{
                        label: '响应时间 (秒)',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
            
            // 浏览器操作性能图
            const browserCtx = document.getElementById('browser-chart').getContext('2d');
            browserChart = new Chart(browserCtx, {{
                type: 'bar',
                data: {{
                    labels: ['navigate', 'click', 'fill', 'screenshot', 'extract'],
                    datasets: [{{
                        label: '平均执行时间 (秒)',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: [
                            'rgba(231, 76, 60, 0.8)',
                            'rgba(52, 152, 219, 0.8)',
                            'rgba(46, 204, 113, 0.8)',
                            'rgba(155, 89, 182, 0.8)',
                            'rgba(241, 196, 15, 0.8)'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        }}
        
        function refreshData() {{
            // 模拟从API获取数据
            fetch('/api/performance-metrics')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('获取数据失败:', error));
        }}
        
        function updateDashboard(data) {{
            document.getElementById('llm-calls').textContent = data.llm_metrics.total_calls;
            document.getElementById('avg-response-time').textContent = data.llm_metrics.avg_response_time.toFixed(2) + 's';
            document.getElementById('browser-actions').textContent = data.browser_metrics.total_actions;
            document.getElementById('avg-execution-time').textContent = data.browser_metrics.avg_execution_time.toFixed(2) + 's';
            document.getElementById('memory-usage').textContent = data.system_metrics.avg_memory_usage_mb.toFixed(1) + 'MB';
            document.getElementById('success-rate').textContent = data.summary.success_rate.toFixed(1) + '%';
            document.getElementById('last-update').textContent = new Date().toLocaleString();
        }}
        
        // 初始化图表
        initCharts();
        
        // 每5秒自动刷新
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""
        return html
    
    def export_metrics_json(self, output_path: Optional[str] = None) -> str:
        """导出性能指标为JSON文件"""
        if output_path is None:
            output_path = self.template_dir / "performance_metrics.json"
        
        metrics = {
            "export_time": datetime.now().isoformat(),
            "realtime_metrics": self.get_realtime_metrics(),
            "history": self.get_metrics_history(duration_hours=1)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _enforce_history_limit(self):
        """强制得去历史大小限制"""
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]


# 全局性能仪表板实例
_performance_dashboard: Optional[PerformanceDashboard] = None


def get_performance_dashboard() -> PerformanceDashboard:
    """获取全局性能仪表板实例"""
    global _performance_dashboard
    if _performance_dashboard is None:
        _performance_dashboard = PerformanceDashboard()
    return _performance_dashboard