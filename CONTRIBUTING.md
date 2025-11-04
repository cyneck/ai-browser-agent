# 贡献指南

感谢您对AI浏览器代理项目的关注！我们欢迎各种形式的贡献，包括但不限于代码、文档、测试、问题报告和功能建议。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [提交指南](#提交指南)
- [代码审查流程](#代码审查流程)
- [发布流程](#发布流程)
- [社区支持](#社区支持)

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们作为贡献者和维护者承诺，无论年龄、体型、残疾、种族、性别认同和表达、经验水平、国籍、个人形象、种族、宗教或性取向如何，参与我们项目和社区的每个人都能获得无骚扰的体验。

### 我们的标准

有助于创造积极环境的行为包括：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

不可接受的行为包括：

- 使用性化的语言或图像，以及不受欢迎的性关注或性骚扰
- 恶意评论、侮辱/贬损评论，以及个人或政治攻击
- 公开或私下骚扰
- 未经明确许可，发布他人的私人信息，如物理或电子地址
- 在专业环境中可能被认为不合适的其他行为

### 执行

项目维护者有权利和责任删除、编辑或拒绝与本行为准则不符的评论、提交、代码、wiki编辑、问题和其他贡献，或暂时或永久禁止任何他们认为有不当、威胁、冒犯或有害行为的贡献者。

## 如何贡献

### 报告Bug

在报告Bug之前，请检查[现有问题](https://github.com/cyneck/ai-browser-agent/issues)以避免重复报告。

#### Bug报告应包含：

1. **清晰的标题**：简洁描述问题
2. **详细描述**：
   - 预期行为
   - 实际行为
   - 重现步骤
3. **环境信息**：
   - 操作系统
   - Python版本
   - 项目版本
   - 浏览器版本
4. **错误日志**：相关的错误信息和堆栈跟踪
5. **截图**：如果适用，添加截图帮助解释问题

#### Bug报告模板

```markdown
**Bug描述**
简洁清晰地描述Bug。

**重现步骤**
1. 执行 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

**预期行为**
清晰简洁地描述您期望发生的事情。

**实际行为**
清晰简洁地描述实际发生的事情。

**截图**
如果适用，添加截图来帮助解释您的问题。

**环境信息**
- 操作系统: [例如 Windows 10, macOS 12.0, Ubuntu 20.04]
- Python版本: [例如 3.9.7]
- 项目版本: [例如 1.0.0]
- 浏览器: [例如 Chrome 95.0.4638.69]

**错误日志**
```
粘贴相关的错误日志
```

**附加信息**
添加任何其他关于问题的信息。
```

### 功能请求

我们欢迎功能建议！在提交功能请求之前，请：

1. 检查[现有问题](https://github.com/cyneck/ai-browser-agent/issues)
2. 考虑功能是否符合项目目标
3. 提供详细的用例说明

#### 功能请求模板

```markdown
**功能描述**
清晰简洁地描述您想要的功能。

**问题描述**
清晰简洁地描述问题。例如：我总是感到沮丧当[...]

**解决方案**
清晰简洁地描述您想要发生的事情。

**替代方案**
清晰简洁地描述您考虑过的任何替代解决方案或功能。

**用例**
描述具体的使用场景：
1. 作为[用户类型]，我想要[功能]，以便[目标]
2. ...

**附加信息**
添加任何其他关于功能请求的信息、截图或示例。
```

### 代码贡献

#### 贡献类型

1. **Bug修复**：修复已知问题
2. **新功能**：添加新的功能特性
3. **性能优化**：提升系统性能
4. **代码重构**：改进代码结构和可读性
5. **测试改进**：添加或改进测试用例
6. **文档更新**：改进项目文档

#### 贡献流程

1. **Fork项目**
   ```bash
   # 在GitHub上Fork项目
   # 克隆您的Fork
   git clone https://github.com/yourusername/ai-browser-agent.git
   cd ai-browser-agent
   ```

2. **设置开发环境**
   ```bash
   # 安装依赖
   poetry install --with dev
   
   # 安装pre-commit钩子
   pre-commit install
   
   # 安装Playwright浏览器
   playwright install
   ```

3. **创建分支**
   ```bash
   # 创建并切换到新分支
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/bug-description
   ```

4. **开发**
   - 编写代码
   - 添加测试
   - 更新文档
   - 确保代码通过所有检查

5. **测试**
   ```bash
   # 运行测试
   pytest
   
   # 检查代码覆盖率
   pytest --cov=src --cov-report=html
   
   # 代码格式化
   black src/ tests/
   isort src/ tests/
   
   # 类型检查
   mypy src/
   
   # 运行pre-commit检查
   pre-commit run --all-files
   ```

6. **提交**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

7. **推送**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **创建Pull Request**
   - 在GitHub上创建Pull Request
   - 填写详细的描述
   - 链接相关的Issue
   - 等待代码审查

## 开发环境设置

### 系统要求

- Python 3.9+
- Node.js 16+ (用于前端开发)
- Git
- 支持的操作系统：Windows, macOS, Linux

### 详细设置步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/cyneck/ai-browser-agent.git
   cd ai-browser-agent
   ```

2. **Python环境**
   ```bash
   # 使用Poetry（推荐）
   poetry install --with dev
   poetry shell
   
   # 或使用pip
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # 或 .venv\Scripts\activate  # Windows
   pip install -e ".[dev]"
   ```

3. **浏览器设置**
   ```bash
   playwright install
   ```

4. **环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入必要的API密钥
   ```

5. **验证安装**
   ```bash
   # 运行测试
   pytest tests/unit/
   
   # 启动开发服务器
   python -m src.main --dev
   ```

### IDE配置

#### VS Code

推荐的扩展：
- Python
- Pylance
- Black Formatter
- isort
- GitLens
- Thunder Client (API测试)

配置文件 (`.vscode/settings.json`)：
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

#### PyCharm

1. 打开项目
2. 配置Python解释器为虚拟环境
3. 启用代码格式化工具
4. 配置测试运行器

## 提交指南

### 提交消息规范

我们使用[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### 类型说明

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式化（不影响代码运行的变动）
- `refactor`: 代码重构（既不是新增功能，也不是修复bug的代码变动）
- `perf`: 性能优化
- `test`: 增加测试
- `chore`: 构建过程或辅助工具的变动
- `ci`: 持续集成相关
- `build`: 构建系统或外部依赖的变动

#### 范围说明

- `perception`: 感知层相关
- `reasoning`: 推理层相关
- `action`: 执行层相关
- `api`: API接口相关
- `plugin`: 插件系统相关
- `cli`: 命令行界面相关
- `web`: Web界面相关
- `config`: 配置相关
- `deps`: 依赖更新

#### 示例

```bash
# 新功能
git commit -m "feat(perception): add dynamic content monitoring"

# Bug修复
git commit -m "fix(action): resolve element selection timeout issue"

# 文档更新
git commit -m "docs: update API documentation with new endpoints"

# 重构
git commit -m "refactor(reasoning): simplify instruction builder logic"

# 性能优化
git commit -m "perf(perception): optimize page analysis performance"

# 测试
git commit -m "test(action): add unit tests for action executor"
```

#### 详细提交消息

对于复杂的更改，提供详细的提交消息：

```
feat(plugin): add website-specific optimization plugins

Add support for website-specific optimization through plugin system:
- Implement plugin interface for custom page analysis
- Add Baidu search optimization plugin
- Add Google search optimization plugin
- Include plugin management API endpoints

This allows for better handling of different website structures
and improves the accuracy of element selection.

Closes #123
Refs #124
```

### 分支命名规范

- `feature/feature-name`: 新功能分支
- `fix/bug-description`: Bug修复分支
- `docs/documentation-update`: 文档更新分支
- `refactor/component-name`: 重构分支
- `test/test-improvement`: 测试改进分支

### Pull Request指南

#### PR标题

使用与提交消息相同的格式：
```
feat(perception): add dynamic content monitoring
```

#### PR描述模板

```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 测试改进
- [ ] 性能优化

## 变更描述
简洁描述此PR的变更内容。

## 相关Issue
- Closes #123
- Refs #124

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成
- [ ] 代码覆盖率满足要求

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过了所有CI检查
- [ ] 进行了自我代码审查

## 截图（如适用）
添加截图来展示变更效果。

## 附加信息
任何其他相关信息。
```

## 代码审查流程

### 审查标准

1. **功能性**
   - 代码是否实现了预期功能
   - 是否处理了边界情况
   - 错误处理是否完善

2. **代码质量**
   - 代码是否清晰易读
   - 是否遵循项目规范
   - 是否有适当的注释

3. **测试覆盖**
   - 是否有足够的测试用例
   - 测试是否覆盖了主要功能
   - 是否包含边界情况测试

4. **性能**
   - 是否有性能问题
   - 是否有内存泄漏
   - 是否有不必要的计算

5. **安全性**
   - 是否存在安全漏洞
   - 输入验证是否充分
   - 是否正确处理敏感数据

6. **文档**
   - 是否更新了相关文档
   - API文档是否准确
   - 代码注释是否充分

### 审查流程

1. **自动检查**
   - CI/CD流水线自动运行
   - 代码格式检查
   - 测试执行
   - 安全扫描

2. **人工审查**
   - 至少一名维护者审查
   - 复杂变更需要多人审查
   - 审查者提供建设性反馈

3. **反馈处理**
   - 贡献者根据反馈修改代码
   - 审查者重新审查
   - 直到所有问题解决

4. **合并**
   - 所有检查通过
   - 获得必要的批准
   - 维护者合并PR

### 审查礼仪

#### 对于审查者

- 提供建设性和具体的反馈
- 解释为什么需要更改
- 承认好的代码和改进
- 及时响应审查请求
- 保持友好和专业的语调

#### 对于贡献者

- 对反馈保持开放态度
- 及时响应审查意见
- 提供必要的解释和澄清
- 感谢审查者的时间和努力
- 学习并应用反馈

## 发布流程

### 版本号规范

我们使用[语义化版本](https://semver.org/)：

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的API更改
- `MINOR`: 向后兼容的功能添加
- `PATCH`: 向后兼容的Bug修复

### 发布步骤

1. **准备发布**
   ```bash
   # 更新版本号
   poetry version patch  # 或 minor, major
   
   # 更新CHANGELOG.md
   # 提交版本更新
   git add .
   git commit -m "chore: bump version to x.y.z"
   ```

2. **创建发布标签**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **构建和发布**
   ```bash
   # 构建包
   poetry build
   
   # 发布到PyPI
   poetry publish
   ```

4. **GitHub发布**
   - 在GitHub上创建Release
   - 添加发布说明
   - 上传构建产物

### 发布说明模板

```markdown
## 🚀 新功能
- feat(perception): 添加动态内容监控功能
- feat(plugin): 新增网站特定优化插件系统

## 🐛 Bug修复
- fix(action): 修复元素选择超时问题
- fix(api): 修复会话管理内存泄漏

## 📚 文档
- docs: 更新API文档
- docs: 添加插件开发指南

## 🔧 其他改进
- perf: 优化页面分析性能
- refactor: 简化指令构建逻辑

## 💔 破坏性变更
- 移除了已弃用的API端点 `/old-api`

## 📦 依赖更新
- 升级Playwright到v1.40.0
- 更新FastAPI到v0.104.0

**完整变更日志**: https://github.com/cyneck/ai-browser-agent/compare/v0.9.0...v1.0.0
```

## 社区支持

### 获取帮助

1. **文档**：首先查看[项目文档](https://ai-browser-agent.readthedocs.io)
2. **FAQ**：查看[常见问题](https://github.com/cyneck/ai-browser-agent/wiki/FAQ)
3. **Issues**：搜索[现有问题](https://github.com/cyneck/ai-browser-agent/issues)
4. **讨论**：参与[GitHub讨论](https://github.com/cyneck/ai-browser-agent/discussions)

### 社区渠道

- **GitHub**: https://github.com/cyneck/ai-browser-agent
- **Discord**: https://discord.gg/ai-browser-agent
- **邮件**: support@ai-browser-agent.com

### 贡献者认可

我们感谢所有贡献者的努力！贡献者将被列在：

- [贡献者页面](https://github.com/cyneck/ai-browser-agent/graphs/contributors)
- 项目README.md
- 发布说明中

### 成为维护者

活跃的贡献者可能被邀请成为项目维护者。维护者职责包括：

- 审查Pull Request
- 管理Issues和讨论
- 参与项目决策
- 指导新贡献者
- 维护项目质量

## 许可证

通过贡献代码，您同意您的贡献将在[MIT许可证](LICENSE)下授权。

## 联系方式

如有任何问题或建议，请联系：

- **项目负责人**: Eric - cyneck@qq.com
- **技术支持**: support@ai-browser-agent.com

---

感谢您的贡献！🎉