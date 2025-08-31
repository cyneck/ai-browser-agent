# AI浏览器代理 - 性能监控与调优指南

## 🎯 概述

本项目已完成了全面的性能监控和调优系统增强，提供了实时监控、告警机制、性能分析和可视化报告等功能。

## 📊 功能特性

### 1. 核心性能监控
- **执行时间追踪**: 精确记录每个操作的执行时间
- **内存使用监控**: 实时监控系统内存使用情况
- **API调用统计**: 记录LLM调用次数、响应时间、token使用量
- **浏览器操作监控**: 跟踪每个浏览器动作的执行性能

### 2. 智能告警系统
- **实时告警**: 性能指标异常时立即通知
- **可配置规则**: 支持自定义告警阈值和规则
- **多渠道通知**: 控制台、文件、扩展接口
- **告警历史**: 完整的告警记录和状态跟踪

### 3. 可视化仪表板
- **实时图表**: 动态显示性能趋势
- **历史数据**: 支持时间段筛选和分析
- **交互式界面**: 点击式操作，直观易用
- **导出功能**: 支持HTML、JSON格式报告

### 4. 结构化日志
- **JSON格式**: 便于程序化处理和分析
- **性能指标**: 自动记录关键性能数据
- **错误追踪**: 完整的错误信息和堆栈
- **可扩展**: 支持自定义日志字段

## 🚀 快速开始

### 1. 基础使用

```python
from src.common.performance_monitor import get_performance_monitor
from src.monitoring.performance_dashboard import get_performance_dashboard

# 获取性能监控器
perf_monitor = get_performance_monitor()

# 获取仪表板
dashboard = get_performance_dashboard()

# 启动监控
dashboard.start_monitoring()
```

### 2. 记录性能数据

#### LLM调用监控
```python
# 记录成功的LLM调用
perf_monitor.record_llm_call(
    prompt_tokens=100,
    completion_tokens=50,
    response_time=2.5,
    model_name="gemini-pro",
    success=True
)

# 记录失败的LLM调用
perf_monitor.record_llm_call(
    prompt_tokens=100,
    completion_tokens=0,
    response_time=5.0,
    model_name="gemini-pro",
    success=False,
    error_message="API超时"
)
```

#### 浏览器操作监控
```python
# 记录浏览器操作
perf_monitor.record_browser_action(
    action_type="click",
    selector="#submit-button",
    execution_time=0.8,
    page_load_time=1.2,
    success=True
)
```

### 3. 配置告警规则

```python
from src.monitoring.performance_alerts import get_alert_manager, AlertRule

alert_manager = get_alert_manager()

# 添加自定义告警规则
rule = AlertRule(
    name="LLM响应时间告警",
    metric_type="llm",
    threshold=3.0,
    comparison="gt",
    duration=5,
    severity="warning",
    message="LLM响应时间超过3秒"
)

alert_manager.add_rule(rule)
alert_manager.start_monitoring()
```

### 4. 生成性能报告

```python
# 生成HTML报告
html_path = dashboard.generate_html_report()
print(f"HTML报告已生成: {html_path}")

# 导出JSON数据
json_path = dashboard.export_metrics_json()
print(f"JSON数据已导出: {json_path}")

# 获取性能摘要
summary = perf_monitor.get_summary()
print(f"成功率: {summary['success_rate']:.1f}%")
```

## 📁 文件结构

```
src/
├── common/
│   ├── performance_monitor.py    # 核心性能监控模块
│   └── logger.py                 # 增强的日志系统
├── monitoring/
│   ├── performance_dashboard.py  # 可视化仪表板
│   └── performance_alerts.py     # 告警系统
├── action/
│   └── executor.py              # 浏览器操作性能监控
├── reasoning/
│   └── instruction_builder.py   # LLM调用性能监控
└── examples/
    └── performance_monitoring_demo.py  # 完整演示

tests/
└── test_performance_monitoring.py      # 性能测试用例
```

## 🧪 运行演示

执行完整演示脚本：

```bash
python examples/performance_monitoring_demo.py
```

演示将展示：
- 监控系统设置
- 模拟LLM调用和浏览器操作
- 触发告警机制
- 生成性能报告
- 实时数据可视化

## 📈 性能指标说明

### LLM指标
- **total_calls**: 总调用次数
- **successful_calls**: 成功调用次数
- **failed_calls**: 失败调用次数
- **avg_response_time**: 平均响应时间（秒）
- **total_prompt_tokens**: 总提示token数
- **total_completion_tokens**: 总完成token数

### 浏览器操作指标
- **total_actions**: 总操作次数
- **successful_actions**: 成功操作次数
- **failed_actions**: 失败操作次数
- **avg_execution_time**: 平均执行时间（秒）
- **avg_page_load_time**: 平均页面加载时间（秒）

### 系统指标
- **memory_usage_mb**: 内存使用量（MB）
- **cpu_usage_percent**: CPU使用率（%）
- **uptime_seconds**: 系统运行时间（秒）

## 🔧 高级配置

### 自定义告警规则

支持以下告警类型：
- `llm`: LLM调用性能告警
- `browser`: 浏览器操作性能告警
- `memory`: 内存使用告警
- `error_rate`: 错误率告警
- `api_calls`: API调用频率告警

### 扩展通知方式

实现自定义通知器：

```python
def custom_notifier(alert):
    """自定义告警通知器"""
    if alert.severity == "critical":
        # 发送邮件/短信/钉钉通知
        send_urgent_notification(alert.message)
    else:
        # 记录到日志文件
        log_alert(alert)

# 注册自定义通知器
alert_manager.add_alert_callback(custom_notifier)
```

### 集成现有系统

#### 与ActionExecutor集成
```python
from src.action.executor import ActionExecutor

executor = ActionExecutor()
# 自动集成性能监控
# 所有浏览器操作都会自动记录性能数据
```

#### 与InstructionBuilder集成
```python
from src.reasoning.instruction_builder import InstructionBuilder

builder = InstructionBuilder()
# 自动集成LLM调用监控
# 所有LLM调用都会自动记录性能指标
```

## 📋 最佳实践

### 1. 监控策略
- **实时监控**: 在生产环境中持续开启
- **采样监控**: 开发环境中按需启用
- **批量分析**: 定期生成性能报告

### 2. 性能优化
- **阈值设置**: 根据业务需求调整告警阈值
- **资源限制**: 设置合理的内存和CPU限制
- **错误处理**: 完善的错误捕获和恢复机制

### 3. 数据分析
- **趋势分析**: 定期查看性能趋势
- **异常检测**: 及时发现性能退化
- **容量规划**: 基于历史数据预测资源需求

## 🔍 故障排除

### 常见问题

1. **性能数据不更新**
   - 检查监控器是否已启动
   - 确认数据记录调用是否正确

2. **告警未触发**
   - 验证告警规则配置
   - 检查阈值设置是否合理

3. **仪表板无法访问**
   - 确认服务端口是否开放
   - 检查防火墙设置

### 调试模式

启用调试日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看详细的性能监控日志
```

## 📞 支持与反馈

如有问题或建议，请通过以下方式联系：
- 提交Issue到项目仓库
- 查看详细的API文档
- 参考测试用例了解使用方法

---

**注意**: 本性能监控系统设计为低侵入性，对系统性能影响极小，可安全用于生产环境。