# 执行层架构设计（Action Layer）

## 目标

- 安全、稳定、可审计地执行推理层输出的规范化指令。
- 提供模板化的动作库，限制执行范围与能力，避免任意代码执行。
- 维护浏览器与程序会话状态，标准化错误处理与恢复建议。

## 组件

- InstructionTemplateLibrary（指令模板库）
  - 按动作类型组织的 Jinja2 模板集：`navigate.j2`、`click.j2`、`type.j2`、`select.j2`、`wait.j2`、`screenshot.j2`、`extract.j2`、`scroll.j2`、`back.j2`、`forward.j2`、`refresh.j2`、`close.j2`、`error.j2`。
  - 仅模板内允许的 API 可被调用，降低风险。

- ActionExecutor（动作执行器）
  - 接收规范化指令，渲染模板并在受控命名空间中执行。
  - 支持单步与多步；返回统一的 `ExecutionResult`。
  - 集成 `StateManager` 与 `ErrorHandler`。

- StateManager（状态管理器）
  - 维护程序会话状态（键值存储），支持持久化（JSON）。
  - 接口：`get/set/delete/clear/save/load`。

- ErrorHandler（错误处理器）
  - 统一错误封装、诊断与恢复建议（如重试、切换选择器、添加等待）。

- ExecutionContext（执行上下文）
  - 组合 `page`、`session_state`、`template_env`、工具函数，作为模板执行命名空间的一部分。

## 接口

```python
class ActionExecutor:
    def __init__(self, page, state_manager: Optional[StateManager] = None, error_handler: Optional[ErrorHandler] = None): ...
    def get_supported_actions(self) -> List[str]: ...
    def execute(self, instruction: Dict[str, Any], session_state: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]: ...

class StateManager:
    def get_state(self, key: str, default: Any = None) -> Any: ...
    def set_state(self, key: str, value: Any) -> None: ...
    def delete_state(self, key: str) -> None: ...
    def clear_state(self) -> None: ...
    def save_state(self, file_path: str) -> None: ...
    def load_state(self, file_path: str) -> None: ...

class ErrorHandler:
    def handle_error(self, error: Exception, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]: ...
    def diagnose_error(self, error: Exception, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]: ...
    def suggest_recovery(self, error_diagnosis: Dict[str, Any]) -> Dict[str, Any]: ...
```

## 数据模型（ExecutionResult）

```json
{
  "success": true,
  "message": "操作结果说明",
  "error": null,
  "data": {},
  "screenshot": null,
  "step_results": []
}
```

## 工作流

1) 接收指令 → 选择模板 → 渲染 → 在受控命名空间执行
2) 捕获异常 → ErrorHandler 诊断与恢复建议 → 标准化返回
3) 可选截图与状态更新 → 返回结果

## 安全与可审计

- 禁止任意代码：仅通过模板暴露的 API 可调用。
- 结果统一返回并可记录；必要字段脱敏。
- 模板与动作集白名单，易于审计与控制。

## MVP 与演进

- MVP：提供 `StateManager` 与 `ErrorHandler` 基础实现，`ActionExecutor` 集成；模板库已具备核心动作。
- 演进：
  - 细化错误分类与自动恢复策略（如自动等待/滚动/重定位）。
  - 更丰富的模板参数（等待策略、可见性校验、断言）。
  - 执行回放与事件流（与监控器集成）。



