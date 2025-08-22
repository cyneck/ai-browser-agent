# 如何对 ARIA Snapshot Usage 进行技术调试

本文档说明如何使用真实网站（如 www.jd.com）对 ARIA Snapshot 功能进行技术调试，而不是使用 mock 测试。

## 快速开始

### 1. 简单调试脚本 (推荐用于快速调试)

```bash
# 调试京东的搜索元素
python examples/simple_aria_debug.py search

# 调试京东的按钮元素  
python examples/simple_aria_debug.py buttons

# 获取京东的完整 ARIA 快照
python examples/simple_aria_debug.py full

# 调试任意网站
python examples/simple_aria_debug.py site https://www.baidu.com
```

### 2. 完整调试工具 (功能更全面)

```bash
# 交互式调试会话
python scripts/debug_aria_snapshot.py

# 直接命令行调试
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function interactive  
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role button
```

## 调试特定功能函数

### 1. 基础 ARIA 快照获取

```python
from examples.aria_snapshot_usage import ARIASnapshotExamples

examples = ARIASnapshotExamples()
examples.setup()

try:
    # 获取基础 ARIA 快照
    snapshot = examples.basic_aria_snapshot("https://www.jd.com")
    print(f"页面角色: {snapshot['role']}")
    print(f"页面名称: {snapshot['name']}")
    print(f"子元素数量: {len(snapshot['children'])}")
finally:
    examples.cleanup()
```

**命令行快速调试:**
```bash
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic --headless
```

### 2. 查找交互元素

```python
# 查找所有交互元素
interactive_elements = examples.find_interactive_elements("https://www.jd.com")

# 按角色分类
by_role = {}
for elem in interactive_elements:
    role = elem['role']
    if role not in by_role:
        by_role[role] = []
    by_role[role].append(elem)

print("交互元素统计:")
for role, elements in by_role.items():
    print(f"  {role}: {len(elements)} 个")
```

**命令行快速调试:**
```bash
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function interactive --headless
```

### 3. 按角色查找元素

```python
# 查找所有按钮
buttons = examples.find_elements_by_role("https://www.jd.com", "button")
print(f"找到 {len(buttons)} 个按钮:")
for button in buttons:
    print(f"  - {button['name']}")

# 查找所有文本输入框
textboxes = examples.find_elements_by_role("https://www.jd.com", "textbox") 
searchboxes = examples.find_elements_by_role("https://www.jd.com", "searchbox")
```

**命令行快速调试:**
```bash
# 查找按钮
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role button --headless

# 查找文本框
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role textbox --headless

# 查找链接
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role link --headless
```

### 4. 表单结构分析

```python
# 分析表单结构
form_analysis = examples.analyze_form_structure("https://www.jd.com")

forms = form_analysis['forms']
print(f"找到 {len(forms)} 个表单:")
for i, form in enumerate(forms):
    print(f"表单 {i+1}: {form['name']}")
    print(f"  字段: {len(form['fields'])} 个")
    print(f"  按钮: {len(form['buttons'])} 个")
```

**命令行快速调试:**
```bash
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function forms --headless
```

### 5. 选择器生成

```python
# 为特定元素生成选择器
selector = examples.create_selector_from_aria("https://www.jd.com", "搜索")
print(f"生成的选择器: {selector}")

# 为按钮生成选择器
selector = examples.create_selector_from_aria("https://www.jd.com", "登录")
print(f"登录按钮选择器: {selector}")
```

**命令行快速调试:**
```bash
# 为搜索框生成选择器
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function selector --element "搜索" --headless

# 为登录按钮生成选择器  
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function selector --element "登录" --headless
```

## 不同网站的调试示例

### 京东 (JD.com)
```bash
# 基础信息
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function info --headless

# 搜索功能
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role searchbox --headless
```

### 百度
```bash
# 调试百度搜索
python examples/simple_aria_debug.py site https://www.baidu.com

# 查找百度的搜索框
python scripts/debug_aria_snapshot.py --url https://www.baidu.com --function role --role textbox --headless
```

### 淘宝
```bash
# 调试淘宝
python scripts/debug_aria_snapshot.py --url https://www.taobao.com --function interactive --headless
```

## 调试模式选择

### 1. 可视化调试 (显示浏览器窗口)
```bash
# 不使用 --headless 参数，可以看到浏览器操作过程
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic

# 慢速模式，便于观察
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic --slow 1000
```

### 2. 无头模式 (后台运行)
```bash
# 使用 --headless 参数，后台运行更快
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic --headless
```

### 3. 交互式调试
```bash
# 启动交互式调试会话
python scripts/debug_aria_snapshot.py
```

## 常见调试场景

### 场景 1: 查找网站的搜索功能
```bash
# 步骤 1: 获取页面基本信息
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function info --headless

# 步骤 2: 查找搜索相关元素
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role searchbox --headless
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role textbox --headless

# 步骤 3: 生成选择器
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function selector --element "搜索" --headless
```

### 场景 2: 分析登录表单
```bash
# 查找表单结构
python scripts/debug_aria_snapshot.py --url https://passport.jd.com --function forms --headless

# 查找登录相关按钮
python scripts/debug_aria_snapshot.py --url https://passport.jd.com --function role --role button --headless

# 查找输入框
python scripts/debug_aria_snapshot.py --url https://passport.jd.com --function role --role textbox --headless
```

### 场景 3: 调试复杂页面的交互元素
```bash
# 获取所有交互元素的概览
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function interactive --headless

# 按类型分别查看
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role link --headless
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function role --role button --headless
```

## 保存调试结果

### 保存 ARIA 快照到文件
```bash
# 交互式保存
python scripts/debug_aria_snapshot.py
# 选择选项 8 保存快照

# 或使用简单脚本保存
python examples/simple_aria_debug.py full  # 会自动保存 JSON 文件
```

### 自定义保存逻辑
```python
import json
import time

# 获取快照并保存
snapshot = examples.basic_aria_snapshot("https://www.jd.com")
filename = f"jd_debug_{int(time.time())}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(snapshot, f, indent=2, ensure_ascii=False)
print(f"快照已保存到: {filename}")
```

## 性能调试

### 测量 ARIA 快照获取时间
```python
import time

start_time = time.time()
snapshot = examples.basic_aria_snapshot("https://www.jd.com")  
duration = time.time() - start_time

print(f"ARIA 快照获取耗时: {duration:.2f} 秒")
print(f"快照大小: {len(str(snapshot))} 字符")
```

### 比较不同网站的性能
```bash
# 测试不同网站
python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic --headless
python scripts/debug_aria_snapshot.py --url https://www.baidu.com --function basic --headless  
python scripts/debug_aria_snapshot.py --url https://www.taobao.com --function basic --headless
```

## 故障排除

### 常见问题及解决方案

1. **网站加载缓慢**
   ```bash
   # 增加等待时间
   python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic --slow 2000
   ```

2. **找不到预期元素**
   ```bash
   # 先查看页面基本信息
   python scripts/debug_aria_snapshot.py --url https://www.jd.com --function info
   
   # 再查看所有交互元素
   python scripts/debug_aria_snapshot.py --url https://www.jd.com --function interactive
   ```

3. **ARIA 快照为空**
   ```bash
   # 检查页面是否正确加载
   python scripts/debug_aria_snapshot.py --url https://www.jd.com --function info
   ```

4. **调试特定问题**
   ```bash
   # 使用可视化模式观察浏览器行为
   python scripts/debug_aria_snapshot.py --url https://www.jd.com --function basic
   ```

## 最佳实践

1. **从简单开始**: 先使用 `simple_aria_debug.py` 快速了解网站结构
2. **渐进调试**: 先获取基本信息，再深入特定功能
3. **保存结果**: 将重要的调试结果保存为 JSON 文件便于后续分析  
4. **可视化调试**: 遇到问题时使用非无头模式观察浏览器行为
5. **性能监控**: 对复杂网站监控 ARIA 快照获取性能

通过这些方法，你可以有效地对任何网站的 ARIA 快照功能进行技术调试和分析。