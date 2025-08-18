# 推理层架构设计（Reasoning Layer）

## 目标

- 将用户自然语言意图在当前页面上下文中转译为可执行、可验证、可审计的规范化指令。
- 支持多轮对话、任务分解与自我修正，保证安全、稳定、可扩展。
- 与感知层、执行层解耦，通过清晰接口协作，形成 Sense-Think-Act 闭环。

## 设计原则

- 职责单一：对话、规划、生成、校验解耦，便于替换与演进。
- 可验证：所有输出在进入执行层前必须通过严格的模式与安全校验。
- 可观测：完整保留推理轨迹与版本，便于审计与回放。
- 可扩展：模块化、插件化，允许引入新规划器/生成器/校验器。

## 组件与职责

- DialogueManager（对话管理器）
  - 维护多轮对话与会话上下文（用户历史、偏好、变量）。
  - 解析用户输入得到高层意图（UserIntent）。
  - 输出：UserIntent、对话上下文摘要（用于提示词蒸馏）。

- TaskPlanner（任务规划器）
  - 将 UserIntent 联合 PageIntentGraph 分解为任务计划（TaskPlan）。
  - 提供任务优先级、依赖关系、成功条件与可观测信号。
  - 输出：TaskPlan（steps、variables、success_criteria）。

- InstructionGenerator（指令生成器）
  - 基于 TaskPlan 与页面意图图谱生成一步或多步的规范化 JSON 指令。
  - 采用模板化/函数调用方式约束输出；内置选择器与值的回退策略。
  - 输出：Instruction 或 {steps: Instruction[]}。

- SafetyValidator（安全校验器）
  - 结构校验：字段完整性、值域与类型、超时/重试策略。
  - 安全校验：域名白名单、危险操作屏蔽、隐私数据处理。
  - 兼容性校验：与执行层模板库支持的动作集对齐。

- Critic（评审器，可选）
  - 离线“心智执行”模拟，发现明显错误（缺少等待、选择器冲突）。
  - 失败时触发小步自我修正（Self-Refine），限制重试次数。

- LoopController（思考循环控制）
  - 驱动 Sense-Think-Act 循环：接收感知→规划/生成→校验/评审→输出执行。
  - 根据执行层反馈与 PageMonitor 事件决定是否重规划或追加指令。

## 数据模型

- UserIntent
  - fields：command（原始指令）、goal（抽象目标）、constraints（约束）、entities（实体）。

- TaskPlan
  - fields：goal、steps[]（action/target/value/desc）、variables[]、success_criteria[]、dependencies、hints。

- Instruction（与 interface_design.md 保持一致）
  - 单步或多步规范化动作；包含 selector/value/options/description。

- ReasoningTrace（推理轨迹）
  - fields：messages[]、decisions[]、alternatives[]、validation_reports[]、timestamps。

## 关键接口

```python
class DialogueManager:
    def add_user_message(self, message: str) -> None: ...
    def add_system_message(self, message: str) -> None: ...
    def get_dialogue_history(self, max_turns: Optional[int] = None) -> List[Dict[str, Any]]: ...
    def clear_history(self) -> None: ...
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:  # -> UserIntent
        ...

class TaskPlanner:
    async def plan_tasks(self, user_intent: Dict[str, Any], page_intent_graph: Dict[str, Any]) -> Dict[str, Any]: ...  # -> TaskPlan
    def decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]: ...
    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

class InstructionGenerator:
    async def generate_instructions(self, task_plan: Dict[str, Any], page_intent_graph: Dict[str, Any], dialogue_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...
    async def generate_single_instruction(self, task: Dict[str, Any], page_intent_graph: Dict[str, Any]) -> Dict[str, Any]: ...
    def validate_instruction(self, instruction: Dict[str, Any]) -> bool: ...

class SafetyValidator:
    def validate(self, instruction: Dict[str, Any], page_intent_graph: Dict[str, Any]) -> Dict[str, Any]: ...  # raise 或返回 {ok, errors}

class Critic:
    def review(self, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]: ...  # {ok, suggestions}

class LoopController:
    async def next(self, user_input: str, page_intent_graph: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]: ...  # -> Instruction(s)
```

## 工作流（Sense-Think-Act）

1) Sense（来自感知层）：获取最新 PageIntentGraph 与页面状态。
2) Think：
   - DialogueManager 解析用户输入 → UserIntent
   - TaskPlanner 生成 TaskPlan（含变量、步骤与成功条件）
   - InstructionGenerator 产出候选指令
   - SafetyValidator + Critic 校验/评审（必要时小步自修正）
3) Act（交付执行层）：输出符合模板库的 JSON 指令；执行后监听 PageMonitor 事件，必要时进入下一轮。

## 与其他层的契约

- 输入（来自感知层）：`PageIntentGraph` 与 `page_state`。
- 输出（面向执行层）：`Instruction | {steps: Instruction[]}`。
- 反馈（来自执行层/监控器）：执行结果与页面变更事件，用于重规划或继续步骤。

## 安全机制

- 域白名单与 URL 校验（沿用 `InstructionBuilder._validate_url_safety`）。
- 动作白名单与模板对齐（仅允许模板库中存在的动作）。
- 敏感信息处理：变量标记与最小暴露；日志脱敏；禁入对话历史的原始秘钥。

## 性能与稳定性

- 提示词蒸馏：对话历史与页面数据做摘要/裁剪，限制 token。
- 选择器回退与重试：css → role → text → xpath，配合 `wait` 注入。
- 结果缓存：常见网站/页面类型的 Few-shot/模板缓存；TaskPlan 复用。
- 控制循环：最大思考步数与总超时；失败快速退出并给出诊断。

## MVP 方案与演进

- MVP：
  - 保留现有 `InstructionBuilder` 作为 Reasoning Facade。
  - 在其内部引入轻量 `DialogueManager` 与 `TaskPlanner` 骨架（可先返回直通策略）。
  - 将现有校验逻辑抽出为 `SafetyValidator`，保持向后兼容原接口 `build(...)`。
- 后续迭代：
  - 引入 Critic 与自修正回路；
  - 更强的 TaskPlanner（分层分解/反思式规划）；
  - 将 LLM 调用改为函数调用/工具使用，增强确定性与可控性。

## 测试策略

- 单元测试：
  - DialogueManager：历史维护与意图提取（mock LLM）。
  - TaskPlanner：分解与优先级（规则/样例驱动）。
  - InstructionGenerator：给定 TaskPlan 与 PageIntentGraph 产出稳定 JSON（模式验证）。
  - SafetyValidator：边界与异常用例（域名、动作、缺字段）。
- 集成测试：
  - 典型用例（导航、搜索、登录）端到端走通；失败用例验证保护网生效。

## 兼容性说明

- 对上层调用者保持 `InstructionBuilder.build(user_instruction, page_data, session_state)` 不变。
- 内部逐步替换为 DialogueManager + TaskPlanner + InstructionGenerator 的编排实现。

