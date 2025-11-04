# AI 浏览器代理

## **1. 背景与目标**

**1.1 背景**

在传统的网页自动化领域，脚本的编写和维护高度依赖于人工。由于网站结构的动态变化，选择器经常失效，导致自动化任务的脆弱性。现有的 AI 自动化工具或因缺乏灵活性，或因安全隐患，难以在复杂的任务场景中大规模应用。

本项目旨在解决这一痛点，构建一个安全、智能、可控的 AI 自动化代理，为用户提供一个基于自然语言的网页交互接口。

**1.2 项目目标**

核心目标是开发一个能够理解人类语言、自主决策并执行复杂网页任务的 AI 代理。具体包括：

  * **实现高鲁棒性**：通过 AI 理解网页语义，降低对硬编码选择器的依赖。
  * **支持多轮对话**：通过会话状态管理，实现多步、复杂的自动化流程。
  * **确保高安全性**：通过代码沙盒和规范化指令，防止恶意或非预期代码的执行。
  * **提供可审计性**：生成的代码和执行日志应可被追溯和审查。

## **2. 功能需求**

### **2.1 用户界面 (UI) 需求**

  * 提供一个简单的命令行或基于 Web 的交互界面，用于接收用户的自然语言指令。
  * 实时显示代理的执行状态和过程日志。

### **2.2 核心功能需求**

  * **自然语言理解**：能够解析用户的自然语言指令，理解其背后的高层意图（例如，"帮我登录京东"）。
  * **多轮对话支持**：能够基于之前的对话内容和执行结果，理解并执行后续指令（例如，"现在点击购物车"）。
  * **网页交互能力**：支持导航、输入、点击、选择等基本操作，以及等待、截屏、文件上传等高级操作。
  * **错误处理与修正**：当执行失败时，能够识别错误原因，并返回给 AI 模型进行自我修正，或向用户提供有用的反馈。

## **3. 技术架构与设计**

本项目采用分层架构，清晰划分各模块的职责。详细的架构设计请参考 [架构设计文档](./docs/architecture.md)。

### **3.1 架构分层**

  * **感知层 (Perception Layer)**：负责将网页数据转化为 AI 可理解的结构化数据。
  * **推理层 (Reasoning Layer)**：负责将用户意图转化为可执行的指令。
  * **执行层 (Action Layer)**：负责安全地执行指令并与浏览器交互。

### **3.2 功能模块设计**

| **层级** | **功能模块** | **输入** | **输出** | **核心技术** |
| :--- | :--- | :--- | :--- | :--- |
| **感知层** | **网页解析与意图提取** | Playwright 原始数据 (HTML, 辅助功能树) | 精简的 JSON 格式"页面意图图谱" | Playwright, Python 解析器 |
| **推理层** | **任务提取与指令构建** | 用户指令、页面意图图谱、对话历史 | 严格规范的 JSON 格式指令 | LLM (如 GPT-4), Prompt Engineering |
| **执行层** | **ActionExecutor** | 浏览器 `page` 对象、会话状态、JSON 指令 | 执行结果 (成功/失败) | Playwright, 模板引擎, 安全验证 |
| | **SafetyValidator** | JSON 指令 | 安全验证后的指令 | 输入验证、字符串转义 |
| | **StateManager** | 程序状态数据 | 持久化状态 | 内存状态管理、文件持久化 |
| | **HumanBehaviorSimulator** | 操作类型、配置参数 | 模拟行为 | 随机延迟、鼠标移动模拟、打字模拟 |
| | **DebugInfoSaver** | 执行步骤、页面对象 | 调试信息文件 | PIL图像处理、页面内容保存 |

## **4. 关键技术细节**

  * **指令规范**：LLM 的输出被严格限定为我们定义的 **JSON 格式**，包含 `action`、`selector`、`value` 等字段。
  * **会话管理**：
      * **浏览器会话**：使用 Playwright 的 `launch_persistent_context` 来管理浏览器状态。
      * **程序会话**：使用 StateManager 管理程序状态，支持内存存储和文件持久化。
  * **安全机制**：
      * **输入验证**：所有进入执行层的指令都经过 SafetyValidator 的结构和安全验证。
      * **字符串转义**：对选择器和值进行长度限制和特殊字符转义，防止注入攻击。
      * **操作限制**：只支持预定义的操作类型，防止执行任意代码。
  * **人类行为模拟**：通过 HumanBehaviorSimulator 模拟真实用户行为，包括：
      * 操作间隔延迟
      * 随机暂停
      * 自然的鼠标移动
      * 人类化的打字速度
      * 页面加载等待
  * **错误处理**：统一的错误处理机制，能够捕获和处理执行过程中的各种异常。
  * **多步执行**：支持单步和多步指令执行，能够处理复杂的操作序列。
  * **调试支持**：在DEBUG_MODE=true时，自动保存每步操作的截图和MHTML页面信息，方便问题定位和调试。

## **5. 项目结构**

详细的项目结构请参考 [项目结构文档](./docs/project_structure.md)。

```
ai-browser-agent/
├── docs/                       # 项目文档
├── src/                        # 源代码
│   ├── perception/             # 感知层
│   ├── reasoning/              # 推理层
│   ├── action/                 # 执行层
│   ├── common/                 # 公共组件
│   ├── plugins/                # 插件系统
│   ├── api/                    # API接口
│   └── main.py                 # 主程序入口
├── tests/                      # 测试代码
├── scripts/                    # 脚本工具
├── pyproject.toml              # 项目依赖管理
└── README.md                   # 项目说明
```

## **6. 安装与使用**

### **6.1 环境要求**

- Python 3.9+
- 支持的操作系统：Windows, macOS, Linux

### **6.2 安装步骤**

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/ai-browser-agent.git
   cd ai-browser-agent
   ```

2. 安装依赖
   ```bash
   # 使用Poetry（推荐）
   poetry install
   
   # 或使用pip
   pip install -e .
   ```

3. 安装Playwright浏览器
   ```bash
   playwright install
   ```

4. 配置环境变量
   ```bash
   # 创建.env文件
   cp .env.example .env
   
   # 编辑.env文件，填入你的API密钥
   ```

### **6.3 使用方法**

1. 启动命令行界面
   ```bash
   python -m src.main --cli
   ```

2. 启动Web界面
   ```bash
   python -m src.main --web
   ```

3. 使用示例
   ```
   > 帮我登录京东
   请输入您的京东账号：user123
   请输入您的密码：******
   [执行中...]
   登录成功！
   
   > 搜索iPhone 15
   [执行中...]
   已完成搜索，找到约100个结果。
   ```

## **7. 文档和指南**

### **7.1 完整文档**

- **[使用指南](./docs/usage_guide.md)** - 详细的使用说明和示例
- **[API文档](./docs/api_documentation.md)** - 完整的API接口文档
- **[开发者指南](./docs/developer_guide.md)** - 开发环境设置和贡献指南
- **[部署指南](./docs/deployment_guide.md)** - 生产环境部署和运维
- **[架构设计](./docs/architecture.md)** - 系统架构和技术细节

### **7.2 快速链接**

- **API交互文档**: http://localhost:8000/docs (启动服务后访问)
- **项目结构**: [docs/project_structure.md](./docs/project_structure.md)
- **测试指南**: [docs/testing_guide.md](./docs/testing_guide.md)
- **安全设计**: [docs/security_design.md](./docs/security_design.md)

## **8. 开发和贡献**

### **8.1 快速开发设置**

```bash
# 克隆仓库
git clone https://github.com/cyneck/ai-browser-agent.git
cd ai-browser-agent

# 安装开发依赖
poetry install --with dev

# 安装pre-commit钩子
pre-commit install

# 运行测试
pytest

# 启动开发服务器
python -m src.main --dev
```

### **8.2 贡献流程**

详细的贡献指南请参考 [CONTRIBUTING.md](./CONTRIBUTING.md)

1. Fork仓库并创建功能分支
2. 按照代码规范开发功能
3. 添加测试并确保通过
4. 更新相关文档
5. 提交Pull Request

## **9. 许可证**

本项目采用MIT许可证 - 详见LICENSE文件

## **10. 联系方式**

如有问题或建议，请通过以下方式联系我们：

- 项目负责人：Eric - cyneck@qq.com
- 项目仓库：https://github.com/cyneck/ai-browser-agent