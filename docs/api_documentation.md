# AI浏览器代理 API 完整文档

## 概述

AI浏览器代理提供完整的RESTful API接口和WebSocket实时通信，支持自然语言指令执行、会话管理、插件系统、认证等功能。本文档涵盖所有API端点、使用示例和最佳实践。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1.0.0
- **认证方式**: Bearer Token (可选)
- **数据格式**: JSON
- **支持协议**: HTTP/HTTPS, WebSocket
- **文档更新**: 2024-11-03

## 认证

### 启用认证

启动服务时使用 `--auth` 参数启用认证功能：

```bash
python src/main.py --web --auth
```

### 获取访问令牌

**POST** `/api/auth/login`

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 使用访问令牌

在请求头中包含访问令牌：

```
Authorization: Bearer <access_token>
```

## API 端点

### 系统状态

#### 获取API状态

**GET** `/api/status`

**响应**:
```json
{
  "status": "running",
  "version": "1.0.0",
  "uptime": 3600.5,
  "active_sessions": 2,
  "total_requests": 150
}
```

#### 健康检查

**GET** `/health`

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 会话管理

#### 获取所有会话

**GET** `/api/sessions`

**响应**:
```json
[
  {
    "session_id": "abc123",
    "created_at": "2024-01-01T10:00:00",
    "last_activity": "2024-01-01T12:00:00",
    "message_count": 5,
    "status": "active"
  }
]
```

#### 创建新会话

**POST** `/api/sessions`

**响应**:
```json
{
  "session_id": "def456",
  "message": "会话创建成功"
}
```

#### 获取会话信息

**GET** `/api/sessions/{session_id}`

**响应**:
```json
{
  "session_id": "abc123",
  "created_at": "2024-01-01T10:00:00",
  "last_activity": "2024-01-01T12:00:00",
  "message_count": 5,
  "status": "active"
}
```

#### 删除会话

**DELETE** `/api/sessions/{session_id}`

**响应**:
```json
{
  "message": "会话 abc123 已删除"
}
```

### 指令执行

#### 执行单条指令

**POST** `/api/execute`

**请求体**:
```json
{
  "text": "打开百度并搜索天气",
  "session_id": "abc123",
  "timeout": 30,
  "screenshot": true
}
```

**响应**:
```json
{
  "success": true,
  "message": "执行成功",
  "error": null,
  "screenshot": "base64_encoded_image",
  "session_id": "abc123",
  "execution_time": 2.5,
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 批量执行指令

**POST** `/api/execute/batch`

**请求体**:
```json
[
  {
    "text": "打开百度",
    "session_id": "abc123"
  },
  {
    "text": "搜索天气",
    "session_id": "abc123"
  }
]
```

**响应**:
```json
{
  "results": [
    {
      "success": true,
      "message": "执行成功",
      "session_id": "abc123",
      "execution_time": 1.2,
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "success": true,
      "message": "执行成功",
      "session_id": "abc123",
      "execution_time": 0.8,
      "timestamp": "2024-01-01T12:00:01"
    }
  ],
  "total": 2
}
```

## WebSocket API

### 连接

**WebSocket** `/ws/{session_id}`

### 发送消息

```json
{
  "instruction": "打开百度并搜索天气"
}
```

### 接收消息

**状态消息**:
```json
{
  "type": "status",
  "message": "执行中..."
}
```

**结果消息**:
```json
{
  "type": "result",
  "success": true,
  "message": "执行成功",
  "error": null,
  "screenshot": "base64_encoded_image"
}
```

**错误消息**:
```json
{
  "type": "error",
  "message": "执行失败的原因"
}
```

## 错误处理

### HTTP状态码

- `200` - 成功
- `400` - 请求错误
- `401` - 未授权
- `404` - 资源不存在
- `500` - 服务器内部错误

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 使用示例

### Python 示例

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000"

# 登录获取令牌（如果启用了认证）
def login():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]

# 执行指令
def execute_instruction(text, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    response = requests.post(f"{BASE_URL}/api/execute", 
        json={"text": text, "screenshot": True},
        headers=headers
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 如果启用了认证，先登录
    # token = login()
    
    # 执行指令
    result = execute_instruction("打开百度并搜索天气")
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### JavaScript 示例

```javascript
// 基础URL
const BASE_URL = "http://localhost:8000";

// 登录获取令牌
async function login() {
    const response = await fetch(`${BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: 'admin',
            password: 'admin123'
        })
    });
    const data = await response.json();
    return data.access_token;
}

// 执行指令
async function executeInstruction(text, token = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${BASE_URL}/api/execute`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            text: text,
            screenshot: true
        })
    });
    
    return await response.json();
}

// 使用示例
async function main() {
    try {
        // 如果启用了认证，先登录
        // const token = await login();
        
        // 执行指令
        const result = await executeInstruction("打开百度并搜索天气");
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
```

### cURL 示例

```bash
# 登录获取令牌（如果启用了认证）
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 执行指令
curl -X POST "http://localhost:8000/api/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"text": "打开百度并搜索天气", "screenshot": true}'

# 获取API状态
curl -X GET "http://localhost:8000/api/status"

# 获取所有会话
curl -X GET "http://localhost:8000/api/sessions" \
  -H "Authorization: Bearer <token>"
```

## 高级功能

### 监控和日志

#### 获取系统指标

**GET** `/api/metrics`

**响应**:
```json
{
  "system": {
    "cpu_percent": 25.5,
    "memory_total": 8000000000,
    "memory_available": 4000000000,
    "memory_percent": 50.0,
    "disk_total": 1000000000000,
    "disk_free": 500000000000,
    "disk_percent": 50.0
  },
  "process": {
    "memory_rss": 100000000,
    "memory_vms": 200000000,
    "cpu_percent": 15.0,
    "num_threads": 10,
    "create_time": 1640995200.0
  },
  "application": {
    "active_sessions": 3,
    "total_requests": 150,
    "uptime": 3600.5,
    "gc_collections": 25
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 获取系统日志

**GET** `/api/logs`

**查询参数**:
- `lines`: 返回的日志行数（默认100）
- `level`: 日志级别过滤（INFO, ERROR, DEBUG, ALL）

**响应**:
```json
{
  "logs": [
    "2024-01-01 10:00:00 INFO 应用启动",
    "2024-01-01 10:01:00 DEBUG 调试信息"
  ],
  "total_lines": 2,
  "log_level": "INFO",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 会话状态管理

#### 获取会话截图

**POST** `/api/sessions/{session_id}/screenshot`

**响应**:
```json
{
  "success": true,
  "screenshot": "base64_encoded_image",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 获取会话状态

**GET** `/api/sessions/{session_id}/state`

**响应**:
```json
{
  "session_id": "abc123",
  "state": {
    "current_url": "https://example.com",
    "page_title": "Example Page",
    "variables": {}
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 更新会话状态

**PUT** `/api/sessions/{session_id}/state`

**请求体**:
```json
{
  "current_url": "https://newsite.com",
  "custom_data": "value"
}
```

**响应**:
```json
{
  "message": "会话状态已更新",
  "session_id": "abc123",
  "timestamp": "2024-01-01T12:00:00"
}
```

## 安全特性

### 速率限制

API实现了基于IP的速率限制：
- 默认每分钟60个请求
- 超过限制返回429状态码
- 健康检查和文档页面不受限制

### 请求日志

所有API请求都会被记录，包括：
- 请求方法和路径
- 响应状态码
- 处理时间
- 客户端IP地址

### 输入验证

所有输入都经过严格验证：
- 指令文本长度限制
- 参数类型检查
- 恶意内容过滤

## 插件系统API

### 获取插件列表

**GET** `/api/plugins`

**响应**:
```json
{
  "plugins": [
    {
      "name": "enhanced_baidu_plugin",
      "version": "1.0.0",
      "description": "百度搜索优化插件",
      "enabled": true,
      "supported_sites": ["baidu.com"]
    }
  ],
  "total": 1
}
```

### 启用/禁用插件

**PUT** `/api/plugins/{plugin_name}/toggle`

**响应**:
```json
{
  "message": "插件状态已更新",
  "plugin_name": "enhanced_baidu_plugin",
  "enabled": true
}
```

### 获取插件配置

**GET** `/api/plugins/{plugin_name}/config`

**响应**:
```json
{
  "plugin_name": "enhanced_baidu_plugin",
  "config": {
    "search_delay": 1.5,
    "max_results": 10
  }
}
```

## 性能监控API

### 获取详细性能指标

**GET** `/api/performance`

**响应**:
```json
{
  "browser": {
    "active_contexts": 2,
    "total_pages": 5,
    "memory_usage_mb": 150.5
  },
  "execution": {
    "avg_response_time": 2.3,
    "success_rate": 0.95,
    "total_executions": 1000
  },
  "plugins": {
    "loaded_plugins": 5,
    "active_plugins": 3
  }
}
```

## 最佳实践

### 1. 会话管理最佳实践

- 为每个用户或任务创建独立会话
- 定期清理不活跃的会话
- 使用有意义的会话ID便于调试

### 2. 错误处理最佳实践

- 始终检查API响应的success字段
- 实现指数退避重试机制
- 记录详细的错误日志

### 3. 性能优化建议

- 合理使用截图功能（仅在必要时启用）
- 批量执行相关指令
- 监控会话数量和内存使用

### 4. 安全建议

- 在生产环境中启用认证
- 定期轮换API令牌
- 验证和清理用户输入

## SDK和客户端库

### Python SDK

```python
from ai_browser_agent import BrowserAgentClient

# 创建客户端
client = BrowserAgentClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"  # 可选
)

# 执行指令
result = client.execute("打开百度并搜索天气")
print(result.message)

# 会话管理
session = client.create_session()
session.execute("打开百度")
session.execute("搜索天气")
session.close()
```

### JavaScript SDK

```javascript
import { BrowserAgentClient } from 'ai-browser-agent-js';

const client = new BrowserAgentClient({
    baseUrl: 'http://localhost:8000',
    apiKey: 'your_api_key'  // 可选
});

// 执行指令
const result = await client.execute('打开百度并搜索天气');
console.log(result.message);

// WebSocket连接
const ws = client.createWebSocket('session_id');
ws.onMessage((data) => {
    console.log('收到消息:', data);
});
ws.send('打开百度');
```

## 限制和注意事项

1. **请求频率**: 默认每分钟60个请求（可配置）
2. **会话数量**: 建议同时活跃会话不超过50个
3. **指令长度**: 单条指令最长1000字符
4. **批量执行**: 最多支持10条指令
5. **超时时间**: 默认30秒，最长300秒
6. **截图大小**: 返回的截图为Base64编码，可能较大
7. **内存使用**: 长时间运行的会话会占用更多内存
8. **并发限制**: 建议并发请求不超过10个
9. **插件兼容性**: 某些插件可能与特定网站不兼容
10. **浏览器资源**: 长时间运行需要定期重启浏览器实例

## 故障排除

### 常见问题

1. **连接超时**
   - 检查服务是否正常运行
   - 验证网络连接
   - 增加超时时间

2. **认证失败**
   - 检查API密钥是否正确
   - 验证令牌是否过期
   - 确认认证头格式正确

3. **指令执行失败**
   - 检查网页是否正常加载
   - 验证选择器是否有效
   - 查看详细错误信息

### 调试技巧

1. 启用详细日志记录
2. 使用截图功能查看页面状态
3. 检查浏览器控制台错误
4. 使用调试模式运行

## 版本更新日志

### v1.0.0 (2024-11-03)
- 完整的RESTful API实现
- WebSocket实时通信支持
- 插件系统集成
- 性能监控功能
- 认证和安全机制
- 详细的错误处理

## 交互式API文档

启动服务后，可以访问以下地址查看交互式API文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **API测试页面**: `http://localhost:8000/test`

这些文档提供了完整的API接口说明和在线测试功能。