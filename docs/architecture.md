# AI 浏览器代理技术架构设计

## 1. 系统架构概述

本系统采用分层架构设计，将功能划分为三个主要层次：感知层、推理层和执行层。这种分层设计使系统具有良好的模块化特性，便于开发、测试和维护。

![系统架构图](./images/architecture_overview.png)

### 1.1 核心架构原则

- **关注点分离**：每一层负责特定的功能，降低系统复杂度
- **松耦合设计**：层与层之间通过定义良好的接口通信
- **可扩展性**：支持新功能和能力的平滑集成
- **安全优先**：在设计的各个层面考虑安全因素

## 2. 详细架构设计

### 2.1 感知层 (Perception Layer)

感知层负责将网页数据转化为AI可理解的结构化数据，是系统与网页交互的基础。

#### 2.1.1 组件设计

- **网页解析器 (WebPageParser)**
  - 功能：解析网页DOM结构和辅助功能树
  - 输入：Playwright获取的原始HTML和辅助功能树
  - 输出：结构化的网页数据

- **意图提取器 (IntentExtractor)**
  - 功能：从网页结构中提取可能的用户意图和交互元素
  - 输入：结构化的网页数据
  - 输出：页面意图图谱（JSON格式）

- **页面监控器 (PageMonitor)**
  - 功能：监控网页变化，支持动态内容处理
  - 输入：网页事件流
  - 输出：网页状态变更通知

#### 2.1.2 数据结构

**页面意图图谱 (Page Intent Graph)**：
```json
{
  "page_title": "示例页面",
  "page_url": "https://example.com",
  "interactive_elements": [
    {
      "type": "button",
      "text": "登录",
      "intent": "authentication",
      "selector": {
        "xpath": "//button[contains(text(), '登录')]",
        "css": "#login-button",
        "accessibility_id": "login-button"
      },
      "state": "enabled",
      "position": {"x": 100, "y": 200}
    },
    // 其他交互元素...
  ],
  "forms": [
    {
      "intent": "user_login",
      "fields": [
        {
          "name": "username",
          "type": "text",
          "required": true,
          "selector": {"css": "#username"}
        },
        {
          "name": "password",
          "type": "password",
          "required": true,
          "selector": {"css": "#password"}
        }
      ],
      "submit": {"selector": {"css": "#login-form button[type='submit']"}}  
    }
  ],
  "navigation": {
    "links": [
      {
        "text": "首页",
        "url": "/",
        "selector": {"css": "nav a.home"}
      }
      // 其他导航链接...
    ]
  },
  "content_sections": [
    {
      "type": "main_content",
      "text_summary": "页面主要内容的摘要...",
      "selector": {"css": "main"}
    }
    // 其他内容区域...
  ]
}
```

### 2.2 推理层 (Reasoning Layer)

推理层是系统的核心智能部分，负责理解用户意图并将其转化为可执行的指令。

#### 2.2.1 组件设计

- **对话管理器 (DialogueManager)**
  - 功能：管理与用户的多轮对话，维护对话上下文
  - 输入：用户自然语言指令，历史对话记录
  - 输出：结构化的用户意图

- **任务规划器 (TaskPlanner)**
  - 功能：将用户意图分解为可执行的子任务序列
  - 输入：用户意图，页面意图图谱
  - 输出：任务执行计划

- **指令生成器 (InstructionGenerator)**
  - 功能：基于LLM将任务转化为规范化的JSON指令
  - 输入：任务执行计划，页面意图图谱，对话历史
  - 输出：符合规范的JSON格式指令

#### 2.2.2 数据结构

**JSON指令格式**：
```json
{
  "action": "click", // 动作类型
  "selector": {
    "type": "css", // 选择器类型
    "value": "#login-button" // 选择器值
  },
  "value": null, // 对于输入类操作的值
  "options": { // 可选参数
    "timeout": 5000,
    "force": false
  },
  "description": "点击登录按钮" // 人类可读的描述
}
```

**任务执行计划**：
```json
{
  "goal": "在京东网站登录账户",
  "steps": [
    {
      "action": "navigate",
      "url": "https://www.jd.com",
      "description": "导航到京东首页"
    },
    {
      "action": "click",
      "target": "登录按钮",
      "description": "点击页面上的登录按钮"
    },
    {
      "action": "input",
      "target": "用户名输入框",
      "value": "${username}", // 变量引用
      "description": "输入用户名"
    },
    {
      "action": "input",
      "target": "密码输入框",
      "value": "${password}", // 变量引用
      "description": "输入密码"
    },
    {
      "action": "click",
      "target": "提交按钮",
      "description": "点击提交按钮完成登录"
    },
    {
      "action": "verify",
      "condition": "页面包含'欢迎回来'文本",
      "description": "验证登录成功"
    }
  ],
  "variables": [
    {"name": "username", "type": "string", "source": "user_input"},
    {"name": "password", "type": "password", "source": "user_input"}
  ]
}
```

### 2.3 执行层 (Action Layer)

执行层负责安全地执行指令并与浏览器交互，是系统的实际执行部分。

#### 2.3.1 组件设计

- **指令模板库 (InstructionTemplateLibrary)**
  - 功能：存储预定义的安全操作模板
  - 输入：N/A
  - 输出：各类操作的Jinja2模板文件

- **动作执行器 (ActionExecutor)**
  - 功能：执行规范化的指令
  - 输入：JSON指令，浏览器page对象，会话状态
  - 输出：执行结果（成功/失败）和相关数据

- **状态管理器 (StateManager)**
  - 功能：管理浏览器会话和程序会话状态
  - 输入：各模块的中间数据和状态更新
  - 输出：持久化的会话状态

- **错误处理器 (ErrorHandler)**
  - 功能：处理执行过程中的异常和错误
  - 输入：执行过程中的异常信息
  - 输出：错误诊断和恢复建议

#### 2.3.2 数据结构

**指令模板示例** (click.j2)：
```jinja2
try:
    element = await page.wait_for_selector("{{ selector.value }}", timeout={{ options.timeout|default(5000) }})
    await element.click(force={{ options.force|default(false) }})
    result = {"status": "success", "message": "Successfully clicked element"}
except Exception as e:
    result = {"status": "error", "message": str(e)}
```

**执行结果格式**：
```json
{
  "status": "success", // 或 "error"
  "message": "操作成功完成", // 或错误信息
  "data": {}, // 可选的返回数据
  "screenshot": "base64编码的截图" // 可选
}
```

## 3. 模块间接口设计

### 3.1 感知层 → 推理层

**接口名称**：`provide_page_context`

**功能**：将感知层解析的页面意图图谱传递给推理层

**参数**：
- `page_intent_graph`: JSON格式的页面意图图谱
- `page_state`: 当前页面状态信息

**返回值**：无

### 3.2 推理层 → 执行层

**接口名称**：`execute_instruction`

**功能**：将推理层生成的指令传递给执行层执行

**参数**：
- `instruction`: JSON格式的指令
- `session_context`: 当前会话上下文

**返回值**：
- `execution_result`: 执行结果

### 3.3 执行层 → 感知层

**接口名称**：`update_page_perception`

**功能**：在执行操作后，触发感知层重新解析页面

**参数**：
- `page_object`: Playwright页面对象

**返回值**：
- `update_status`: 更新状态

## 4. 数据流设计

### 4.1 主要数据流程

1. **用户输入处理流程**：
   - 用户输入自然语言指令
   - 对话管理器处理并维护对话上下文
   - 任务规划器分解为子任务
   - 指令生成器生成JSON指令

2. **指令执行流程**：
   - 动作执行器接收JSON指令
   - 从模板库获取对应模板
   - 渲染模板生成安全代码
   - 执行代码并返回结果

3. **错误处理流程**：
   - 执行过程中发生异常
   - 错误处理器捕获并分析异常
   - 生成错误诊断和恢复建议
   - 返回给推理层进行决策

### 4.2 状态管理

1. **浏览器会话状态**：
   - 使用Playwright的`launch_persistent_context`
   - 保存cookies、localStorage等浏览器状态

2. **程序会话状态**：
   - 使用共享Python字典作为命名空间
   - 在`exec()`调用间保持变量和状态

## 5. 安全机制设计

### 5.1 代码执行安全

- **模板化执行**：不直接执行LLM生成的代码，而是通过预定义的安全模板渲染
- **输入验证**：对所有用户输入和LLM输出进行严格验证
- **权限限制**：限制执行环境的系统访问权限

### 5.2 数据安全

- **敏感数据处理**：对密码等敏感信息进行特殊处理，不记录到日志
- **会话隔离**：确保不同用户的会话相互隔离

### 5.3 沙盒化执行（未来扩展）

- **容器化执行环境**：使用Docker等技术隔离执行环境
- **资源限制**：限制CPU、内存等资源使用

## 6. 扩展性设计

### 6.1 插件系统

设计一个插件接口，允许开发者扩展系统功能：

```python
class Plugin:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def initialize(self, context):
        """初始化插件"""
        pass
    
    def on_before_action(self, action, context):
        """动作执行前的钩子"""
        return action
    
    def on_after_action(self, result, context):
        """动作执行后的钩子"""
        return result
    
    def provide_actions(self):
        """提供自定义动作"""
        return []
```

### 6.2 自定义动作

允许通过插件系统注册自定义动作：

```python
class CustomAction:
    def __init__(self, name, description, template):
        self.name = name
        self.description = description
        self.template = template
    
    def validate_params(self, params):
        """验证参数"""
        pass
    
    def execute(self, params, context):
        """执行动作"""
        pass
```

## 7. 部署架构

### 7.1 开发环境

- **本地开发**：单机部署，适合开发和测试
- **依赖管理**：使用Poetry或Pipenv管理Python依赖

### 7.2 生产环境

- **微服务架构**：将各层拆分为独立服务
- **容器化部署**：使用Docker和Kubernetes管理服务
- **API网关**：统一接口管理和认证

## 8. 技术栈选择

| **组件** | **技术选择** | **原因** |
|----------|--------------|----------|
| **浏览器自动化** | Playwright | 跨浏览器支持，强大的选择器和等待机制 |
| **AI模型** | GPT-4 | 强大的自然语言理解和生成能力 |
| **模板引擎** | Jinja2 | Python生态系统中成熟的模板引擎 |
| **Web框架** | FastAPI | 高性能异步API框架，适合与Playwright集成 |
| **状态管理** | Redis | 分布式环境中的会话状态存储 |
| **日志与监控** | Prometheus + Grafana | 完善的监控和可视化方案 |

## 9. 开发路线图

### 9.1 第一阶段：核心功能实现

- 实现基本的感知层功能，能够解析简单网页
- 实现基本的推理层功能，支持简单指令转换
- 实现基本的执行层功能，支持常见浏览器操作

### 9.2 第二阶段：增强功能与稳定性

- 增强网页解析能力，支持复杂网页结构
- 改进多轮对话支持，提升上下文理解能力
- 增强错误处理和自我修正能力

### 9.3 第三阶段：扩展与优化

- 实现插件系统，支持功能扩展
- 优化性能和资源使用
- 增强安全机制

## 10. 总结

本架构设计文档详细描述了AI浏览器代理的技术架构，包括系统分层、组件设计、数据流、接口设计、安全机制等方面。通过这种架构设计，系统能够实现高鲁棒性、多轮对话支持、高安全性和可审计性的目标，为用户提供一个基于自然语言的网页交互接口。