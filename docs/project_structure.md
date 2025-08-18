# AI 浏览器代理项目结构

## 目录结构

```
ai-browser-agent/
├── docs/                       # 项目文档
│   ├── architecture.md         # 架构设计文档
│   ├── api_reference.md        # API参考文档
│   └── images/                 # 文档图片
│       └── architecture_overview.png  # 架构概览图
├── src/                        # 源代码
│   ├── perception/             # 感知层
│   │   ├── __init__.py
│   │   ├── web_page_parser.py  # 网页解析器
│   │   ├── intent_extractor.py # 意图提取器
│   │   └── page_monitor.py     # 页面监控器
│   ├── reasoning/              # 推理层
│   │   ├── __init__.py
│   │   ├── dialogue_manager.py # 对话管理器
│   │   ├── task_planner.py     # 任务规划器
│   │   └── instruction_generator.py # 指令生成器
│   ├── action/                 # 执行层
│   │   ├── __init__.py
│   │   ├── templates/          # 指令模板
│   │   │   ├── click.j2        # 点击操作模板
│   │   │   ├── input.j2        # 输入操作模板
│   │   │   └── navigate.j2     # 导航操作模板
│   │   ├── action_executor.py  # 动作执行器
│   │   ├── state_manager.py    # 状态管理器
│   │   └── error_handler.py    # 错误处理器
│   ├── common/                 # 公共组件
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── logger.py           # 日志工具
│   │   └── utils.py            # 通用工具函数
│   ├── plugins/                # 插件系统
│   │   ├── __init__.py
│   │   ├── plugin_manager.py   # 插件管理器
│   │   └── base_plugin.py      # 插件基类
│   ├── api/                    # API接口
│   │   ├── __init__.py
│   │   ├── routes.py           # API路由
│   │   └── models.py           # API数据模型
│   └── main.py                 # 主程序入口
├── tests/                      # 测试代码
│   ├── unit/                   # 单元测试
│   │   ├── test_perception.py  # 感知层测试
│   │   ├── test_reasoning.py   # 推理层测试
│   │   └── test_action.py      # 执行层测试
│   ├── integration/            # 集成测试
│   │   └── test_workflow.py    # 工作流测试
│   └── fixtures/               # 测试数据
│       └── sample_pages/       # 样例网页
├── scripts/                    # 脚本工具
│   ├── setup.sh                # 环境设置脚本
│   └── run_demo.py             # 演示脚本
├── .gitignore                  # Git忽略文件
├── pyproject.toml              # 项目依赖管理
├── README.md                   # 项目说明
└── LICENSE                     # 许可证文件
```

## 关键文件说明

### 感知层 (Perception Layer)

- **web_page_parser.py**: 负责解析网页DOM结构和辅助功能树，提取网页的结构化数据。
- **intent_extractor.py**: 从结构化的网页数据中提取可能的用户意图和交互元素。
- **page_monitor.py**: 监控网页变化，支持动态内容处理。

### 推理层 (Reasoning Layer)

- **dialogue_manager.py**: 管理与用户的多轮对话，维护对话上下文。
- **task_planner.py**: 将用户意图分解为可执行的子任务序列。
- **instruction_generator.py**: 基于LLM将任务转化为规范化的JSON指令。

### 执行层 (Action Layer)

- **templates/**: 存储各类操作的Jinja2模板文件，确保安全执行。
- **action_executor.py**: 执行规范化的指令，与浏览器交互。
- **state_manager.py**: 管理浏览器会话和程序会话状态。
- **error_handler.py**: 处理执行过程中的异常和错误。

### 公共组件 (Common)

- **config.py**: 管理系统配置，包括模型参数、浏览器设置等。
- **logger.py**: 提供日志记录功能，支持不同级别的日志。
- **utils.py**: 包含通用工具函数，如JSON处理、选择器转换等。

### 插件系统 (Plugins)

- **plugin_manager.py**: 管理插件的加载、初始化和调用。
- **base_plugin.py**: 定义插件接口，所有插件都应继承此基类。

### API接口 (API)

- **routes.py**: 定义API路由，处理HTTP请求。
- **models.py**: 定义API数据模型，用于请求和响应的验证。

### 主程序 (Main)

- **main.py**: 程序入口点，初始化各个组件并启动服务。

## 依赖管理

项目使用`pyproject.toml`管理依赖，主要依赖包括：

- **Playwright**: 浏览器自动化
- **FastAPI**: Web API框架
- **Jinja2**: 模板引擎
- **Pydantic**: 数据验证
- **OpenAI**: GPT API客户端
- **Redis**: 分布式状态管理（可选）
- **Pytest**: 测试框架

## 开发指南

1. **环境设置**:
   ```bash
   # 克隆仓库
   git clone https://github.com/yourusername/ai-browser-agent.git
   cd ai-browser-agent
   
   # 安装依赖
   pip install -e .
   
   # 安装Playwright浏览器
   playwright install
   ```

2. **运行测试**:
   ```bash
   pytest
   ```

3. **启动服务**:
   ```bash
   python src/main.py
   ```

4. **构建文档**:
   ```bash
   # 如果使用mkdocs
   mkdocs build
   ```

## 贡献指南

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件