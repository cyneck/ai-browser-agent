# AI浏览器代理使用指南

## 概述

AI浏览器代理是一个智能的网页自动化工具，支持通过自然语言指令控制浏览器执行各种网页操作。本指南将帮助您快速上手并充分利用系统的各项功能。

## 目录

- [快速开始](#快速开始)
- [基础使用](#基础使用)
- [高级功能](#高级功能)
- [API使用](#api使用)
- [插件系统](#插件系统)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)
- [使用示例](#使用示例)

## 快速开始

### 安装和启动

1. **安装依赖**
   ```bash
   pip install ai-browser-agent
   playwright install
   ```

2. **配置环境**
   ```bash
   # 创建配置文件
   cp .env.example .env
   
   # 编辑配置文件，添加API密钥
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. **启动服务**
   ```bash
   # 命令行模式
   python -m src.main --cli
   
   # Web界面模式
   python -m src.main --web
   
   # API服务模式
   python -m src.main --api --port 8000
   ```

### 第一次使用

1. **命令行界面**
   ```bash
   $ python -m src.main --cli
   AI浏览器代理已启动，输入指令或 'help' 查看帮助
   > 打开百度
   [执行中...] 正在打开百度首页
   [完成] 已成功打开 https://www.baidu.com
   
   > 搜索天气
   [执行中...] 正在搜索"天气"
   [完成] 搜索完成，找到约100,000,000个结果
   ```

2. **Web界面**
   - 访问 http://localhost:8000
   - 在输入框中输入自然语言指令
   - 点击"执行"按钮
   - 查看执行结果和截图

## 基础使用

### 支持的指令类型

#### 1. 导航操作
```
# 打开网站
打开百度
访问 https://www.google.com
导航到京东首页

# 页面操作
刷新页面
返回上一页
前进到下一页
关闭当前标签页
```

#### 2. 搜索操作
```
# 搜索内容
搜索天气预报
在百度搜索"人工智能"
查找最新新闻

# 特定网站搜索
在京东搜索iPhone
在淘宝查找运动鞋
```

#### 3. 表单操作
```
# 填写表单
输入用户名"admin"
在密码框输入密码
选择"北京"作为城市
勾选同意条款复选框

# 提交表单
点击登录按钮
提交表单
```

#### 4. 信息提取
```
# 获取页面信息
获取页面标题
提取所有链接
获取商品价格信息
提取新闻标题列表

# 截图保存
截取当前页面
保存页面为PDF
```

### 指令语法规则

#### 自然语言指令
系统支持中文自然语言指令，无需严格的语法格式：

```
✅ 正确示例：
- "帮我打开百度"
- "搜索一下天气"
- "点击登录按钮"
- "填写用户名为admin"

✅ 也支持：
- "打开百度"
- "搜索天气"
- "点击登录"
- "输入用户名admin"
```

#### 参数传递
某些指令支持参数传递：

```
# 带引号的参数
搜索"人工智能发展趋势"
输入用户名"test@example.com"

# 不带引号的参数
搜索 iPhone 15
输入密码 123456
```

### 会话管理

#### 会话概念
- 每个浏览器实例对应一个会话
- 会话保持浏览器状态（cookies、localStorage等）
- 支持多轮对话和上下文理解

#### 会话操作
```python
# Python API示例
from ai_browser_agent import BrowserAgent

# 创建代理实例
agent = BrowserAgent()

# 开始会话
session_id = agent.create_session()

# 执行指令（保持会话状态）
agent.execute("打开京东", session_id=session_id)
agent.execute("搜索手机", session_id=session_id)  # 在同一页面搜索
agent.execute("点击第一个商品", session_id=session_id)

# 结束会话
agent.close_session(session_id)
```

## 高级功能

### 1. 多步操作

#### 顺序执行
```
# 单条指令包含多个步骤
打开京东，搜索iPhone，点击第一个商品

# 分步执行
> 打开京东
> 搜索iPhone
> 点击第一个商品
> 查看商品详情
```

#### 条件执行
```
# 条件判断
如果页面包含"登录"按钮，则点击登录

# 循环操作
滚动页面直到找到"加载更多"按钮
```

### 2. 智能等待

系统自动处理页面加载和动态内容：

```python
# 自动等待页面加载
agent.execute("打开淘宝")  # 自动等待页面完全加载

# 等待特定元素出现
agent.execute("等待搜索结果加载完成")

# 智能重试
agent.execute("点击可能延迟出现的按钮")  # 自动重试直到元素可点击
```

### 3. 错误处理和恢复

#### 自动错误恢复
```
# 元素定位失败时自动尝试备选方案
点击登录按钮  # 如果ID选择器失败，自动尝试文本选择器

# 页面加载超时时自动重试
打开网站 https://slow-website.com  # 自动处理超时重试
```

#### 错误信息反馈
```
> 点击不存在的按钮
[错误] 未找到指定的按钮元素
建议：请检查按钮是否存在或尝试更具体的描述

> 在错误的页面执行操作
[错误] 当前页面不支持此操作
建议：请先导航到正确的页面
```

### 4. 人类行为模拟

#### 自然操作模拟
```python
# 启用人类行为模拟
agent = BrowserAgent(human_behavior=True)

# 模拟真实用户行为：
# - 随机的操作间隔
# - 自然的鼠标移动轨迹
# - 人类化的打字速度
# - 页面滚动行为
```

#### 反检测机制
```python
# 配置反检测参数
agent = BrowserAgent(
    human_behavior=True,
    behavior_mode="stealth",  # 隐蔽模式
    random_delays=True,       # 随机延迟
    mouse_simulation=True     # 鼠标轨迹模拟
)
```

## API使用

### REST API

#### 基础API调用

```python
import requests

# API基础URL
BASE_URL = "http://localhost:8000"

# 执行指令
response = requests.post(f"{BASE_URL}/api/execute", json={
    "text": "打开百度并搜索天气",
    "screenshot": True,
    "timeout": 30
})

result = response.json()
print(f"执行结果: {result['message']}")
if result.get('screenshot'):
    # 处理base64编码的截图
    import base64
    screenshot_data = base64.b64decode(result['screenshot'])
    with open('screenshot.png', 'wb') as f:
        f.write(screenshot_data)
```

#### 会话管理API

```python
# 创建会话
response = requests.post(f"{BASE_URL}/api/sessions")
session_id = response.json()['session_id']

# 在会话中执行指令
requests.post(f"{BASE_URL}/api/execute", json={
    "text": "打开京东",
    "session_id": session_id
})

requests.post(f"{BASE_URL}/api/execute", json={
    "text": "搜索手机",
    "session_id": session_id
})

# 获取会话状态
response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
session_info = response.json()

# 删除会话
requests.delete(f"{BASE_URL}/api/sessions/{session_id}")
```

#### 批量执行API

```python
# 批量执行多条指令
instructions = [
    {"text": "打开百度", "session_id": session_id},
    {"text": "搜索人工智能", "session_id": session_id},
    {"text": "点击第一个结果", "session_id": session_id}
]

response = requests.post(f"{BASE_URL}/api/execute/batch", json=instructions)
results = response.json()

for i, result in enumerate(results['results']):
    print(f"指令 {i+1}: {result['message']}")
```

### WebSocket API

#### 实时通信

```javascript
// 建立WebSocket连接
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

// 监听消息
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'status':
            console.log('状态更新:', data.message);
            break;
        case 'result':
            console.log('执行结果:', data.message);
            if (data.screenshot) {
                displayScreenshot(data.screenshot);
            }
            break;
        case 'error':
            console.error('执行错误:', data.message);
            break;
    }
};

// 发送指令
function sendInstruction(instruction) {
    ws.send(JSON.stringify({
        instruction: instruction
    }));
}

// 使用示例
sendInstruction("打开百度");
sendInstruction("搜索天气");
```

#### Python WebSocket客户端

```python
import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8000/ws/session123"
    
    async with websockets.connect(uri) as websocket:
        # 发送指令
        await websocket.send(json.dumps({
            "instruction": "打开百度"
        }))
        
        # 接收响应
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'result':
                    print(f"执行完成: {data['message']}")
                    break
                elif data['type'] == 'status':
                    print(f"状态: {data['message']}")
                elif data['type'] == 'error':
                    print(f"错误: {data['message']}")
                    break
                    
            except websockets.exceptions.ConnectionClosed:
                break

# 运行客户端
asyncio.run(websocket_client())
```

## 插件系统

### 使用现有插件

#### 查看可用插件

```python
# 通过API查看插件
response = requests.get("http://localhost:8000/api/plugins")
plugins = response.json()['plugins']

for plugin in plugins:
    print(f"插件: {plugin['name']}")
    print(f"描述: {plugin['description']}")
    print(f"支持网站: {plugin['supported_sites']}")
    print(f"状态: {'启用' if plugin['enabled'] else '禁用'}")
```

#### 启用/禁用插件

```python
# 启用插件
requests.put("http://localhost:8000/api/plugins/enhanced_baidu_plugin/toggle")

# 禁用插件
requests.put("http://localhost:8000/api/plugins/enhanced_google_plugin/toggle")
```

### 插件配置

#### 查看插件配置

```python
# 获取插件配置
response = requests.get("http://localhost:8000/api/plugins/enhanced_baidu_plugin/config")
config = response.json()['config']

print(f"搜索延迟: {config['search_delay']}秒")
print(f"最大结果数: {config['max_results']}")
```

#### 修改插件配置

```python
# 更新插件配置
new_config = {
    "search_delay": 2.0,
    "max_results": 20
}

requests.put(
    "http://localhost:8000/api/plugins/enhanced_baidu_plugin/config",
    json=new_config
)
```

### 网站特定优化

#### 百度搜索优化
```
# 使用百度插件优化的搜索
> 打开百度
[插件] 使用百度搜索优化插件
[完成] 已打开百度首页

> 搜索人工智能
[插件] 应用百度搜索策略
[完成] 搜索完成，提取到20个优化结果
```

#### 小红书优化
```
# 小红书内容提取
> 打开小红书
> 搜索美食推荐
[插件] 使用小红书内容提取优化
[完成] 已提取笔记标题、作者、点赞数等结构化数据
```

## 最佳实践

### 1. 指令编写技巧

#### 清晰具体的描述
```
✅ 好的指令：
- "点击页面右上角的登录按钮"
- "在搜索框输入'iPhone 15 Pro'"
- "选择价格从低到高排序"

❌ 模糊的指令：
- "点击那个按钮"
- "输入一些东西"
- "选择一个选项"
```

#### 分步执行复杂任务
```
# 复杂任务分解
任务：在京东购买iPhone

步骤1: 打开京东首页
步骤2: 搜索"iPhone 15"
步骤3: 选择合适的商品
步骤4: 加入购物车
步骤5: 查看购物车
```

#### 使用上下文信息
```
# 利用会话上下文
> 打开淘宝
> 搜索运动鞋  # 在淘宝页面搜索
> 筛选耐克品牌  # 在搜索结果页面筛选
> 选择第一个商品  # 在筛选结果中选择
```

### 2. 错误处理策略

#### 预期错误处理
```python
try:
    result = agent.execute("点击可能不存在的按钮")
    if not result.success:
        # 处理执行失败
        print(f"执行失败: {result.error}")
        # 尝试备选方案
        result = agent.execute("尝试其他方式完成操作")
except Exception as e:
    print(f"系统错误: {e}")
```

#### 重试机制
```python
import time

def execute_with_retry(agent, instruction, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = agent.execute(instruction)
            if result.success:
                return result
            else:
                print(f"尝试 {attempt + 1} 失败: {result.error}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
        except Exception as e:
            print(f"尝试 {attempt + 1} 异常: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    raise Exception(f"执行失败，已重试 {max_retries} 次")
```

### 3. 性能优化

#### 合理使用截图
```python
# 只在需要时启用截图
result = agent.execute("打开百度", screenshot=False)  # 不需要截图
result = agent.execute("搜索结果", screenshot=True)   # 需要查看结果
```

#### 会话复用
```python
# 复用会话避免重复初始化
session_id = agent.create_session()

# 在同一会话中执行多个相关操作
agent.execute("打开购物网站", session_id=session_id)
agent.execute("登录账户", session_id=session_id)
agent.execute("浏览商品", session_id=session_id)
agent.execute("加入购物车", session_id=session_id)

# 完成后关闭会话
agent.close_session(session_id)
```

#### 批量操作
```python
# 使用批量API提高效率
instructions = [
    "打开网站",
    "填写表单字段1",
    "填写表单字段2",
    "提交表单"
]

results = agent.execute_batch(instructions, session_id=session_id)
```

### 4. 安全考虑

#### 敏感信息处理
```python
# 避免在日志中记录敏感信息
agent.execute("输入密码", log_sensitive=False)

# 使用环境变量存储敏感数据
import os
password = os.getenv('USER_PASSWORD')
agent.execute(f"输入密码{password}")
```

#### 访问控制
```python
# 启用认证
agent = BrowserAgent(auth_required=True)

# 使用API密钥
headers = {"Authorization": "Bearer your-api-key"}
response = requests.post(url, headers=headers, json=data)
```

## 常见问题

### Q1: 为什么指令执行失败？

**可能原因：**
1. 网页元素未加载完成
2. 元素选择器失效
3. 网络连接问题
4. 页面结构变化

**解决方案：**
```python
# 增加等待时间
agent.execute("等待页面加载完成")
agent.execute("点击按钮")

# 使用更具体的描述
agent.execute("点击页面右上角的蓝色登录按钮")

# 检查页面状态
result = agent.execute("获取页面标题")
print(f"当前页面: {result.message}")
```

### Q2: 如何处理动态内容？

**解决方案：**
```python
# 等待动态内容加载
agent.execute("等待搜索结果出现")

# 滚动加载更多内容
agent.execute("滚动到页面底部")
agent.execute("点击加载更多按钮")

# 监控页面变化
agent.execute("等待页面内容更新完成")
```

### Q3: 如何提高执行成功率？

**最佳实践：**
1. 使用清晰具体的指令描述
2. 分步执行复杂操作
3. 适当添加等待时间
4. 使用插件优化特定网站
5. 启用人类行为模拟

### Q4: 如何调试执行问题？

**调试方法：**
```python
# 启用详细日志
agent = BrowserAgent(debug_mode=True)

# 获取页面截图
result = agent.execute("截取当前页面", screenshot=True)

# 查看页面源码
result = agent.execute("获取页面HTML内容")

# 检查元素信息
result = agent.execute("分析页面可交互元素")
```

## 使用示例

### 示例1: 电商购物流程

```python
from ai_browser_agent import BrowserAgent

# 创建代理实例
agent = BrowserAgent(human_behavior=True)

# 创建会话
session_id = agent.create_session()

try:
    # 1. 打开购物网站
    result = agent.execute("打开京东首页", session_id=session_id)
    print(f"步骤1: {result.message}")
    
    # 2. 搜索商品
    result = agent.execute("搜索iPhone 15", session_id=session_id)
    print(f"步骤2: {result.message}")
    
    # 3. 筛选结果
    result = agent.execute("选择128GB存储容量", session_id=session_id)
    print(f"步骤3: {result.message}")
    
    # 4. 查看商品详情
    result = agent.execute("点击第一个商品", session_id=session_id)
    print(f"步骤4: {result.message}")
    
    # 5. 获取商品信息
    result = agent.execute("提取商品价格和评价信息", session_id=session_id)
    print(f"商品信息: {result.message}")
    
    # 6. 截图保存
    result = agent.execute("截取商品详情页面", 
                          session_id=session_id, 
                          screenshot=True)
    
    if result.screenshot:
        import base64
        with open('product_page.png', 'wb') as f:
            f.write(base64.b64decode(result.screenshot))
        print("已保存商品页面截图")

finally:
    # 关闭会话
    agent.close_session(session_id)
```

### 示例2: 信息收集和分析

```python
import json
from ai_browser_agent import BrowserAgent

def collect_news_data():
    agent = BrowserAgent()
    session_id = agent.create_session()
    
    news_data = []
    
    try:
        # 打开新闻网站
        agent.execute("打开新浪新闻", session_id=session_id)
        
        # 获取头条新闻
        result = agent.execute("提取头条新闻标题和链接", session_id=session_id)
        
        # 解析结果（假设返回结构化数据）
        if result.success and result.data:
            news_data.extend(result.data)
        
        # 切换到科技频道
        agent.execute("点击科技频道", session_id=session_id)
        
        # 获取科技新闻
        result = agent.execute("提取科技新闻列表", session_id=session_id)
        
        if result.success and result.data:
            news_data.extend(result.data)
        
        # 保存数据
        with open('news_data.json', 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功收集 {len(news_data)} 条新闻")
        
    finally:
        agent.close_session(session_id)
    
    return news_data

# 执行数据收集
news_data = collect_news_data()
```

### 示例3: 表单自动填写

```python
def auto_fill_form(form_data):
    agent = BrowserAgent(human_behavior=True)
    session_id = agent.create_session()
    
    try:
        # 打开表单页面
        agent.execute("打开注册页面", session_id=session_id)
        
        # 填写个人信息
        agent.execute(f"输入姓名'{form_data['name']}'", session_id=session_id)
        agent.execute(f"输入邮箱'{form_data['email']}'", session_id=session_id)
        agent.execute(f"输入电话'{form_data['phone']}'", session_id=session_id)
        
        # 选择下拉选项
        agent.execute(f"选择城市'{form_data['city']}'", session_id=session_id)
        agent.execute(f"选择职业'{form_data['occupation']}'", session_id=session_id)
        
        # 勾选复选框
        if form_data.get('agree_terms'):
            agent.execute("勾选同意服务条款", session_id=session_id)
        
        if form_data.get('subscribe_newsletter'):
            agent.execute("勾选订阅新闻邮件", session_id=session_id)
        
        # 提交表单
        result = agent.execute("点击提交按钮", session_id=session_id)
        
        if result.success:
            print("表单提交成功")
            # 获取确认信息
            confirmation = agent.execute("获取确认信息", session_id=session_id)
            return confirmation.message
        else:
            print(f"表单提交失败: {result.error}")
            return None
            
    finally:
        agent.close_session(session_id)

# 使用示例
form_data = {
    'name': '张三',
    'email': 'zhangsan@example.com',
    'phone': '13800138000',
    'city': '北京',
    'occupation': '软件工程师',
    'agree_terms': True,
    'subscribe_newsletter': False
}

result = auto_fill_form(form_data)
print(f"提交结果: {result}")
```

### 示例4: 批量数据处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def batch_process_urls(urls):
    """批量处理多个URL"""
    
    def process_single_url(url):
        agent = BrowserAgent()
        session_id = agent.create_session()
        
        try:
            # 访问URL
            result = agent.execute(f"打开 {url}", session_id=session_id)
            if not result.success:
                return {'url': url, 'error': result.error}
            
            # 提取页面信息
            title_result = agent.execute("获取页面标题", session_id=session_id)
            content_result = agent.execute("提取主要内容", session_id=session_id)
            
            return {
                'url': url,
                'title': title_result.message if title_result.success else None,
                'content': content_result.message if content_result.success else None,
                'success': True
            }
            
        except Exception as e:
            return {'url': url, 'error': str(e)}
        
        finally:
            agent.close_session(session_id)
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_single_url, url)
            for url in urls
        ]
        
        results = await asyncio.gather(*tasks)
    
    return results

# 使用示例
urls = [
    'https://www.example1.com',
    'https://www.example2.com',
    'https://www.example3.com'
]

# 运行批量处理
results = asyncio.run(batch_process_urls(urls))

# 处理结果
for result in results:
    if result.get('success'):
        print(f"✅ {result['url']}: {result['title']}")
    else:
        print(f"❌ {result['url']}: {result['error']}")
```

---

*本使用指南将持续更新，如有问题或建议，请访问项目GitHub页面或联系技术支持。*