# 感知层架构设计（Perception Layer）

## 目标

- 将网页的原始状态转化为结构化、稳定、可用于推理与执行的页面语义表示。
- 对动态页面变化进行增量感知与回调通知，降低重复计算成本。
- 提供清晰的接口，便于扩展更多解析器与意图识别能力。

## 组件概览

- WebPageParser：面向“数据提取”的解析器，负责从 Playwright `Page` 获取 DOM、可访问性树、可交互元素、文本摘要与功能区域等原始结构化数据。
- IntentExtractor：面向“语义理解”的抽象器，基于解析数据生成页面意图图谱（Page Intent Graph），识别表单、导航、交互入口与页面类型等。
- PageMonitor：面向“变化感知”的监控器，监听页面生命周期与 DOM 变更，触发增量更新与外部回调。
- PageAnalyzer：感知层门面（Facade/Orchestrator），编排 Parser 与 Extractor，向上层提供统一的 `analyze()` 接口与兼容的数据结构。

## 数据模型

- 解析数据（ParserOutput）：
  - page_url, page_title
  - dom_snapshot（可选、裁剪/哈希）
  - accessibility_tree（可选）
  - interactive_elements（原始层面的交互元素集合）
  - text_content（原始纯文本）
  - functional_areas（header/nav/main/footer/search 等）

- 页面意图图谱（PageIntentGraph）：
  - page_title, page_url
  - interactive_elements：类型、文本、选择器、状态、位置
  - forms：字段、提交按钮、必填标记
  - navigation：links[]
  - content_sections：类型、摘要、选择器
  - page_type：login/search_results/product_detail/homepage/generic …

说明：为保持与既有上层兼容，`PageAnalyzer.analyze()` 将同时输出旧键（`url/title/elements/functional_areas/page_type/text_content`）与新键（`page_title/page_url/interactive_elements/forms/navigation/content_sections`）。

## 接口定义

```python
class WebPageParser:
    def parse(self, page: Page) -> Dict[str, Any]:
        """返回 ParserOutput。"""

class IntentExtractor:
    def extract(self, parser_output: Dict[str, Any]) -> Dict[str, Any]:
        """返回 PageIntentGraph。"""

class PageMonitor:
    def start(self, page: Page) -> None: ...
    def stop(self) -> None: ...
    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None: ...
    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None: ...

class PageAnalyzer:
    def analyze(self, page: Page) -> Dict[str, Any]:
        """编排 parse → extract 并输出兼容数据结构。"""
```

## 工作流

1) PageAnalyzer 调用 WebPageParser.parse 拿到解析数据
2) PageAnalyzer 调用 IntentExtractor.extract 生成意图图谱
3) PageAnalyzer 合并为对上层兼容的输出
4) PageMonitor 在动作后或页面事件后触发重新分析或增量更新

## 扩展与演进

- 解析器插件：允许自定义 `WebPageParser` 的策略（如注入式脚本、影子 DOM 处理、可见性过滤、性能优化）。
- 意图识别扩展：引入轻量规则+ML 混合策略；必要时可调用 VLM/OCR 增强（图片、canvas 文本提取）。
- 缓存与增量：对大型页面分块解析，使用节点哈希减少重复工作；PageMonitor 提供变更集（changed_nodes）。
- 质量与稳定性：
  - 选择器多样化与回退（css/xpath/role/text）
  - 状态标注（enabled/disabled/visible）与置信度

## 与上层的契约

- 推理层只依赖 `PageAnalyzer.analyze()` 的输出；短期内保留旧键，避免大范围改动。
- 执行层执行后由 PageMonitor 触发感知刷新，保证推理使用最新上下文。

## 安全与性能

- 仅在受信任的上下文执行注入脚本；限制提取的数据量（截断文本，移除敏感字段）。
- 控制频率（节流/去抖）与超时，避免阻塞主流程。

## 最小可行实现（MVP）

- 已提供基础实现：交互元素扫描、文本抓取、功能区识别、页面类型判定；并拆分为 Parser/Extractor/Analyzer。
- 后续逐步补充：表单识别鲁棒性、导航链接完善、可访问性树利用、增量更新与缓存。


