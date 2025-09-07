# 测试策略

## 概述

本项目采用分层测试策略，包括单元测试和集成测试，以确保代码质量和系统稳定性。

## 单元测试

单元测试位于 [tests/unit](file:///D:/code/ai-browser-agent/tests/unit) 目录中，主要用于测试单个组件的功能。

### 特点
- 使用 mock 对象隔离依赖
- 执行速度快
- 环境要求低
- 覆盖所有公共方法

### 编写规范
1. 所有新增功能方法都需要编写对应的单元测试用例
2. 使用 mock 对象模拟依赖组件的行为
3. 验证方法调用次数和参数
4. 即使无法完全测试实际功能，也需要验证方法可以被正确调用且不会引发异常
5. 测试用例需要覆盖所有公共方法
6. 测试用例设计应遵循现有测试模式

## 集成测试

集成测试位于 [tests/integration](file:///D:/code/ai-browser-agent/tests/integration) 目录中，用于验证多个组件间的协同工作能力。

### 特点
- 使用真实组件和外部服务
- 执行速度相对较慢
- 需要完整运行环境
- 验证端到端功能

### 编写规范
1. 仅对无法通过单元测试验证的关键集成点编写集成测试
2. 优先测试与外部服务（如浏览器）的集成
3. 确保测试环境的稳定性和可重复性
4. 正确管理测试资源（启动/关闭浏览器、清理临时文件等）

## 运行测试

```bash
# 运行所有单元测试
pytest -m unit

# 运行所有集成测试
pytest -m integration

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_action_executor.py
pytest tests/integration/test_page_analyzer_integration.py
```