# AI浏览器代理部署和运维指南

## 概述

本文档提供AI浏览器代理项目的完整部署和运维指南，涵盖开发环境、测试环境、生产环境的部署方案，以及监控、维护和故障排除等运维内容。

## 目录

- [部署架构](#部署架构)
- [环境要求](#环境要求)
- [部署方式](#部署方式)
- [配置管理](#配置管理)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [性能调优](#性能调优)
- [安全配置](#安全配置)
- [故障排除](#故障排除)
- [运维最佳实践](#运维最佳实践)

## 部署架构

### 系统架构图

```mermaid
graph TB
    subgraph "负载均衡层"
        LB[负载均衡器]
    end
    
    subgraph "应用层"
        APP1[AI浏览器代理实例1]
        APP2[AI浏览器代理实例2]
        APP3[AI浏览器代理实例N]
    end
    
    subgraph "数据层"
        REDIS[Redis缓存]
        DB[PostgreSQL数据库]
        FILES[文件存储]
    end
    
    subgraph "监控层"
        PROM[Prometheus]
        GRAF[Grafana]
        LOGS[日志聚合]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    APP1 --> REDIS
    APP1 --> DB
    APP1 --> FILES
    
    APP2 --> REDIS
    APP2 --> DB
    APP2 --> FILES
    
    APP3 --> REDIS
    APP3 --> DB
    APP3 --> FILES
    
    PROM --> APP1
    PROM --> APP2
    PROM --> APP3
    
    GRAF --> PROM
    LOGS --> APP1
    LOGS --> APP2
    LOGS --> APP3
```

### 部署模式

#### 1. 单机部署
适用于开发和小规模测试环境：
```
┌─────────────────────────────┐
│     单机服务器               │
│  ┌─────────────────────────┐ │
│  │  AI浏览器代理应用        │ │
│  │  ├─ Web服务             │ │
│  │  ├─ API服务             │ │
│  │  └─ 浏览器实例          │ │
│  └─────────────────────────┘ │
│  ┌─────────────────────────┐ │
│  │  本地存储               │ │
│  │  ├─ SQLite数据库        │ │
│  │  ├─ 文件存储            │ │
│  │  └─ 日志文件            │ │
│  └─────────────────────────┘ │
└─────────────────────────────┘
```

#### 2. 集群部署
适用于生产环境：
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   应用服务器1    │    │   应用服务器2    │    │   应用服务器N    │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │AI浏览器代理 │ │    │ │AI浏览器代理 │ │    │ │AI浏览器代理 │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │                共享服务层                        │
         │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
         │ │Redis集群    │ │PostgreSQL   │ │文件存储     │ │
         │ └─────────────┘ └─────────────┘ └─────────────┘ │
         └─────────────────────────────────────────────────┘
```

## 环境要求

### 硬件要求

#### 最小配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB可用空间
- **网络**: 100Mbps带宽

#### 推荐配置
- **CPU**: 4核心以上
- **内存**: 8GB RAM以上
- **存储**: 100GB SSD
- **网络**: 1Gbps带宽

#### 生产环境配置
- **CPU**: 8核心以上
- **内存**: 16GB RAM以上
- **存储**: 500GB SSD + 网络存储
- **网络**: 10Gbps带宽

### 软件要求

#### 操作系统
- **Linux**: Ubuntu 20.04+, CentOS 8+, RHEL 8+
- **Windows**: Windows Server 2019+
- **macOS**: macOS 11+

#### 运行时环境
- **Python**: 3.9+
- **Node.js**: 16+ (可选，用于前端)
- **Docker**: 20.10+ (容器部署)
- **Kubernetes**: 1.20+ (K8s部署)

#### 依赖服务
- **数据库**: PostgreSQL 12+ 或 SQLite 3.35+
- **缓存**: Redis 6.0+
- **消息队列**: RabbitMQ 3.8+ 或 Apache Kafka 2.8+ (可选)
- **监控**: Prometheus + Grafana (可选)

## 部署方式

### 1. 传统部署

#### 系统准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3-pip git curl

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python39 python39-pip git curl

# 创建用户
sudo useradd -m -s /bin/bash aiagent
sudo usermod -aG sudo aiagent
```

#### 应用部署

```bash
# 切换到应用用户
sudo su - aiagent

# 克隆代码
git clone https://github.com/cyneck/ai-browser-agent.git
cd ai-browser-agent

# 创建虚拟环境
python3.9 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .
playwright install

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 初始化数据库
python -m src.common.database init

# 启动服务
python -m src.main --web --port 8000
```

#### 系统服务配置

```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/ai-browser-agent.service > /dev/null <<EOF
[Unit]
Description=AI Browser Agent
After=network.target

[Service]
Type=simple
User=aiagent
Group=aiagent
WorkingDirectory=/home/aiagent/ai-browser-agent
Environment=PATH=/home/aiagent/ai-browser-agent/.venv/bin
ExecStart=/home/aiagent/ai-browser-agent/.venv/bin/python -m src.main --web --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable ai-browser-agent
sudo systemctl start ai-browser-agent

# 检查状态
sudo systemctl status ai-browser-agent
```

### 2. Docker部署

#### Dockerfile

```dockerfile
# 多阶段构建
FROM python:3.9-slim as builder

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装Poetry并安装依赖
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# 生产镜像
FROM python:3.9-slim

# 安装浏览器依赖
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd -m -u 1000 aiagent

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python环境
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 安装Playwright浏览器
RUN playwright install chromium

# 设置权限
RUN chown -R aiagent:aiagent /app

# 切换到应用用户
USER aiagent

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "src.main", "--web", "--port", "8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  ai-browser-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/aiagent
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./browser_data:/app/browser_data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=aiagent
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ai-browser-agent
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 部署命令

```bash
# 构建和启动
docker-compose up -d

# 查看日志
docker-compose logs -f ai-browser-agent

# 扩展服务
docker-compose up -d --scale ai-browser-agent=3

# 更新服务
docker-compose pull
docker-compose up -d
```

### 3. Kubernetes部署

#### 命名空间

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-browser-agent
```

#### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-browser-agent-config
  namespace: ai-browser-agent
data:
  DATABASE_URL: "postgresql://user:password@postgres:5432/aiagent"
  REDIS_URL: "redis://redis:6379/0"
  LOG_LEVEL: "INFO"
  BROWSER_TYPE: "chromium"
  HEADLESS: "true"
```

#### Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-browser-agent-secret
  namespace: ai-browser-agent
type: Opaque
data:
  GEMINI_API_KEY: <base64-encoded-key>
  OPENAI_API_KEY: <base64-encoded-key>
```

#### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-browser-agent
  namespace: ai-browser-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-browser-agent
  template:
    metadata:
      labels:
        app: ai-browser-agent
    spec:
      containers:
      - name: ai-browser-agent
        image: ai-browser-agent:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-browser-agent-config
        - secretRef:
            name: ai-browser-agent-secret
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: browser-data
          mountPath: /app/browser_data
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: browser-data
        emptyDir: {}
      - name: logs
        emptyDir: {}
```

#### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-browser-agent-service
  namespace: ai-browser-agent
spec:
  selector:
    app: ai-browser-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-browser-agent-ingress
  namespace: ai-browser-agent
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: ai-browser-agent-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-browser-agent-service
            port:
              number: 80
```

#### 部署命令

```bash
# 应用配置
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# 查看状态
kubectl get pods -n ai-browser-agent
kubectl get services -n ai-browser-agent
kubectl get ingress -n ai-browser-agent

# 查看日志
kubectl logs -f deployment/ai-browser-agent -n ai-browser-agent

# 扩展副本
kubectl scale deployment ai-browser-agent --replicas=5 -n ai-browser-agent
```

## 配置管理

### 环境变量配置

```bash
# 核心配置
export DATABASE_URL="postgresql://user:password@localhost:5432/aiagent"
export REDIS_URL="redis://localhost:6379/0"
export GEMINI_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"

# 应用配置
export DEBUG_MODE="false"
export LOG_LEVEL="INFO"
export MAX_WORKERS="4"
export REQUEST_TIMEOUT="30"

# 浏览器配置
export BROWSER_TYPE="chromium"
export HEADLESS="true"
export USER_DATA_DIR="/app/browser_data"
export MAX_BROWSER_INSTANCES="10"

# 安全配置
export SECRET_KEY="your-secret-key"
export ALLOWED_HOSTS="localhost,yourdomain.com"
export CORS_ORIGINS="https://yourdomain.com"

# 性能配置
export CACHE_TTL="3600"
export MAX_CONCURRENT_SESSIONS="50"
export CLEANUP_INTERVAL="300"
```

### 配置文件

```yaml
# config/production.yaml
database:
  url: ${DATABASE_URL}
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30

redis:
  url: ${REDIS_URL}
  max_connections: 100
  socket_timeout: 5

browser:
  type: ${BROWSER_TYPE:chromium}
  headless: ${HEADLESS:true}
  user_data_dir: ${USER_DATA_DIR:/app/browser_data}
  max_instances: ${MAX_BROWSER_INSTANCES:10}
  launch_args:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
    - "--disable-gpu"

api:
  host: "0.0.0.0"
  port: 8000
  workers: ${MAX_WORKERS:4}
  timeout: ${REQUEST_TIMEOUT:30}
  max_request_size: 10485760  # 10MB

security:
  secret_key: ${SECRET_KEY}
  allowed_hosts: ${ALLOWED_HOSTS}
  cors_origins: ${CORS_ORIGINS}
  rate_limit: "60/minute"

logging:
  level: ${LOG_LEVEL:INFO}
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/app/logs/app.log"
  max_size: "100MB"
  backup_count: 5

monitoring:
  metrics_enabled: true
  health_check_interval: 30
  performance_tracking: true
```

### 配置验证

```python
# config/validator.py
from pydantic import BaseSettings, validator
from typing import List, Optional

class Settings(BaseSettings):
    # 数据库配置
    database_url: str
    
    # Redis配置
    redis_url: str
    
    # API密钥
    gemini_api_key: str
    openai_api_key: Optional[str] = None
    
    # 应用配置
    debug_mode: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    
    # 浏览器配置
    browser_type: str = "chromium"
    headless: bool = True
    max_browser_instances: int = 10
    
    # 安全配置
    secret_key: str
    allowed_hosts: List[str] = ["localhost"]
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v.upper()
    
    @validator('browser_type')
    def validate_browser_type(cls, v):
        valid_types = ['chromium', 'firefox', 'webkit']
        if v not in valid_types:
            raise ValueError(f'Invalid browser type: {v}')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 监控和日志

### 应用监控

#### Prometheus指标

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 请求计数器
REQUEST_COUNT = Counter(
    'ai_browser_agent_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

# 响应时间直方图
REQUEST_DURATION = Histogram(
    'ai_browser_agent_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# 活跃会话数
ACTIVE_SESSIONS = Gauge(
    'ai_browser_agent_active_sessions',
    'Number of active sessions'
)

# 浏览器实例数
BROWSER_INSTANCES = Gauge(
    'ai_browser_agent_browser_instances',
    'Number of browser instances'
)

# 错误计数器
ERROR_COUNT = Counter(
    'ai_browser_agent_errors_total',
    'Total number of errors',
    ['error_type']
)

def start_metrics_server(port=9090):
    """启动指标服务器"""
    start_http_server(port)
```

#### 健康检查

```python
# monitoring/health.py
import asyncio
import time
from typing import Dict, Any

class HealthChecker:
    def __init__(self):
        self.checks = {}
        self.last_check_time = 0
        self.check_interval = 30  # 30秒
    
    async def check_health(self) -> Dict[str, Any]:
        """执行健康检查"""
        current_time = time.time()
        
        if current_time - self.last_check_time < self.check_interval:
            return self.checks
        
        self.checks = {
            'status': 'healthy',
            'timestamp': current_time,
            'checks': {
                'database': await self._check_database(),
                'redis': await self._check_redis(),
                'browser': await self._check_browser(),
                'disk_space': await self._check_disk_space(),
                'memory': await self._check_memory()
            }
        }
        
        # 判断整体健康状态
        if any(check['status'] != 'healthy' for check in self.checks['checks'].values()):
            self.checks['status'] = 'unhealthy'
        
        self.last_check_time = current_time
        return self.checks
    
    async def _check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            # 执行简单查询
            # result = await database.execute("SELECT 1")
            return {'status': 'healthy', 'response_time': 0.01}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def _check_redis(self) -> Dict[str, Any]:
        """检查Redis连接"""
        try:
            # 执行ping命令
            # result = await redis.ping()
            return {'status': 'healthy', 'response_time': 0.005}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def _check_browser(self) -> Dict[str, Any]:
        """检查浏览器实例"""
        try:
            # 检查浏览器实例状态
            return {'status': 'healthy', 'instances': 2}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        import shutil
        try:
            total, used, free = shutil.disk_usage('/')
            usage_percent = (used / total) * 100
            
            if usage_percent > 90:
                return {'status': 'unhealthy', 'usage_percent': usage_percent}
            elif usage_percent > 80:
                return {'status': 'warning', 'usage_percent': usage_percent}
            else:
                return {'status': 'healthy', 'usage_percent': usage_percent}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def _check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        import psutil
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return {'status': 'unhealthy', 'usage_percent': memory.percent}
            elif memory.percent > 80:
                return {'status': 'warning', 'usage_percent': memory.percent}
            else:
                return {'status': 'healthy', 'usage_percent': memory.percent}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
```

### 日志管理

#### 日志配置

```python
# logging_config.py
import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_level="INFO", log_dir="/app/logs"):
    """设置日志配置"""
    
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（按大小轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'app.log'),
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志处理器
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'error.log'),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # 性能日志处理器
    perf_logger = logging.getLogger('performance')
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'performance.log'),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=3,
        encoding='utf-8'
    )
    perf_formatter = logging.Formatter(
        '%(asctime)s - %(message)s'
    )
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False
```

#### 结构化日志

```python
# structured_logging.py
import json
import logging
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_event(self, event_type: str, **kwargs):
        """记录结构化事件"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': kwargs
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration: float, **kwargs):
        """记录API请求"""
        self.log_event('api_request', 
                      method=method, 
                      path=path, 
                      status_code=status_code,
                      duration=duration,
                      **kwargs)
    
    def log_execution(self, instruction: str, success: bool, 
                     duration: float, **kwargs):
        """记录指令执行"""
        self.log_event('instruction_execution',
                      instruction=instruction,
                      success=success,
                      duration=duration,
                      **kwargs)
    
    def log_error(self, error_type: str, error_message: str, **kwargs):
        """记录错误"""
        self.log_event('error',
                      error_type=error_type,
                      error_message=error_message,
                      **kwargs)

# 使用示例
logger = StructuredLogger('ai_browser_agent')
logger.log_request('POST', '/api/execute', 200, 2.5, session_id='abc123')
```

### Grafana仪表板

```json
{
  "dashboard": {
    "title": "AI浏览器代理监控",
    "panels": [
      {
        "title": "请求速率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_browser_agent_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ai_browser_agent_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(ai_browser_agent_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "活跃会话",
        "type": "singlestat",
        "targets": [
          {
            "expr": "ai_browser_agent_active_sessions"
          }
        ]
      },
      {
        "title": "错误率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_browser_agent_errors_total[5m])",
            "legendFormat": "{{error_type}}"
          }
        ]
      }
    ]
  }
}
```

## 备份和恢复

### 数据备份策略

#### 数据库备份

```bash
#!/bin/bash
# backup_database.sh

# 配置
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="aiagent"
DB_USER="user"
BACKUP_DIR="/backup/database"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aiagent_$TIMESTAMP.sql"

# 执行备份
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 删除过期备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "数据库备份完成: $BACKUP_FILE.gz"
```

#### Redis备份

```bash
#!/bin/bash
# backup_redis.sh

REDIS_HOST="localhost"
REDIS_PORT="6379"
BACKUP_DIR="/backup/redis"
RETENTION_DAYS=7

mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# 执行BGSAVE命令
redis-cli -h $REDIS_HOST -p $REDIS_PORT BGSAVE

# 等待备份完成
while [ $(redis-cli -h $REDIS_HOST -p $REDIS_PORT LASTSAVE) -eq $(redis-cli -h $REDIS_HOST -p $REDIS_PORT LASTSAVE) ]; do
    sleep 1
done

# 复制RDB文件
cp /var/lib/redis/dump.rdb $BACKUP_FILE
gzip $BACKUP_FILE

# 删除过期备份
find $BACKUP_DIR -name "*.rdb.gz" -mtime +$RETENTION_DAYS -delete

echo "Redis备份完成: $BACKUP_FILE.gz"
```

#### 应用数据备份

```bash
#!/bin/bash
# backup_app_data.sh

APP_DIR="/app"
BACKUP_DIR="/backup/app_data"
RETENTION_DAYS=14

mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/app_data_$TIMESTAMP.tar.gz"

# 备份应用数据
tar -czf $BACKUP_FILE \
    --exclude="$APP_DIR/.venv" \
    --exclude="$APP_DIR/__pycache__" \
    --exclude="$APP_DIR/.git" \
    --exclude="$APP_DIR/logs/*.log" \
    $APP_DIR/browser_data \
    $APP_DIR/config \
    $APP_DIR/static

# 删除过期备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "应用数据备份完成: $BACKUP_FILE"
```

### 自动备份

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份数据库
0 2 * * * /backup/scripts/backup_database.sh

# 每6小时备份Redis
0 */6 * * * /backup/scripts/backup_redis.sh

# 每天凌晨3点备份应用数据
0 3 * * * /backup/scripts/backup_app_data.sh
```

### 恢复流程

#### 数据库恢复

```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="aiagent"
DB_USER="user"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <backup_file>"
    exit 1
fi

# 解压备份文件
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE > /tmp/restore.sql
    RESTORE_FILE="/tmp/restore.sql"
else
    RESTORE_FILE=$BACKUP_FILE
fi

# 停止应用服务
systemctl stop ai-browser-agent

# 删除现有数据库
dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME

# 创建新数据库
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME

# 恢复数据
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $RESTORE_FILE

# 启动应用服务
systemctl start ai-browser-agent

# 清理临时文件
rm -f /tmp/restore.sql

echo "数据库恢复完成"
```

## 性能调优

### 应用层优化

#### 连接池配置

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 连接池大小
    max_overflow=30,       # 最大溢出连接数
    pool_timeout=30,       # 获取连接超时时间
    pool_recycle=3600,     # 连接回收时间
    pool_pre_ping=True     # 连接前ping检查
)
```

#### 缓存优化

```python
# cache.py
import redis
from functools import wraps
import json
import hashlib

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def cache_result(self, ttl: int = 3600):
        """结果缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # 尝试从缓存获取
                cached_result = self.redis.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.redis.setex(cache_key, ttl, json.dumps(result))
                return result
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func_name: str, args, kwargs) -> str:
        """生成缓存键"""
        key_data = f"{func_name}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
```

#### 异步处理

```python
# async_processor.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any

class AsyncProcessor:
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_batch(self, items: List[Any], 
                          processor: Callable, 
                          batch_size: int = 10) -> List[Any]:
        """批量异步处理"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [
                asyncio.get_event_loop().run_in_executor(
                    self.executor, processor, item
                ) for item in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results
```

### 系统层优化

#### 内核参数调优

```bash
# /etc/sysctl.conf

# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 文件描述符限制
fs.file-max = 2097152

# 应用生效
sysctl -p
```

#### 文件描述符限制

```bash
# /etc/security/limits.conf
aiagent soft nofile 65535
aiagent hard nofile 65535
aiagent soft nproc 32768
aiagent hard nproc 32768
```

#### Nginx优化

```nginx
# nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 65535;
    use epoll;
    multi_accept on;
}

http {
    # 基础优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # 缓冲区优化
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # 压缩优化
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # 负载均衡
    upstream ai_browser_agent {
        least_conn;
        server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
        server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
        server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    server {
        listen 80;
        server_name api.yourdomain.com;
        
        location / {
            proxy_pass http://ai_browser_agent;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # 超时设置
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
```

## 安全配置

### SSL/TLS配置

```nginx
# SSL配置
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL证书
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 其他安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

### 防火墙配置

```bash
# UFW配置
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# 允许SSH
ufw allow 22/tcp

# 允许HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# 允许应用端口（仅内网）
ufw allow from 10.0.0.0/8 to any port 8000
ufw allow from 172.16.0.0/12 to any port 8000
ufw allow from 192.168.0.0/16 to any port 8000

# 启用防火墙
ufw --force enable
```

### 应用安全

```python
# security.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
from datetime import datetime, timedelta

security = HTTPBearer()

class SecurityManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """验证令牌"""
        try:
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=["HS256"])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return username
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
```

## 故障排除

### 常见问题诊断

#### 1. 应用启动失败

**症状**: 应用无法启动或启动后立即退出

**诊断步骤**:
```bash
# 检查日志
journalctl -u ai-browser-agent -f

# 检查配置文件
python -c "from src.common.config import Settings; print(Settings())"

# 检查依赖
pip check

# 检查端口占用
netstat -tlnp | grep 8000
```

**常见原因和解决方案**:
- 端口被占用: 更改端口或停止占用进程
- 配置错误: 检查环境变量和配置文件
- 依赖缺失: 重新安装依赖
- 权限问题: 检查文件和目录权限

#### 2. 数据库连接失败

**症状**: 数据库连接超时或拒绝连接

**诊断步骤**:
```bash
# 测试数据库连接
psql -h localhost -U user -d aiagent -c "SELECT 1;"

# 检查数据库状态
systemctl status postgresql

# 检查网络连接
telnet localhost 5432
```

**解决方案**:
- 检查数据库服务状态
- 验证连接参数
- 检查防火墙设置
- 检查数据库配置

#### 3. 浏览器实例问题

**症状**: 浏览器无法启动或操作失败

**诊断步骤**:
```bash
# 检查浏览器依赖
playwright install --dry-run

# 测试浏览器启动
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Browser started successfully')
    browser.close()
"

# 检查系统资源
free -h
df -h
```

**解决方案**:
- 安装缺失的系统依赖
- 增加系统内存
- 清理磁盘空间
- 调整浏览器启动参数

#### 4. 性能问题

**症状**: 响应时间慢或超时

**诊断步骤**:
```bash
# 检查系统负载
top
htop
iostat -x 1

# 检查网络延迟
ping google.com
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# 分析应用性能
python -m cProfile -o profile.stats -m src.main
```

**优化方案**:
- 增加服务器资源
- 优化数据库查询
- 启用缓存
- 调整并发参数

### 故障恢复流程

#### 自动恢复

```bash
#!/bin/bash
# auto_recovery.sh

SERVICE_NAME="ai-browser-agent"
MAX_RETRIES=3
RETRY_INTERVAL=30

check_service() {
    systemctl is-active --quiet $SERVICE_NAME
    return $?
}

restart_service() {
    echo "重启服务: $SERVICE_NAME"
    systemctl restart $SERVICE_NAME
    sleep 10
}

send_alert() {
    local message=$1
    # 发送告警通知
    curl -X POST "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" \
         -H 'Content-type: application/json' \
         --data "{\"text\":\"$message\"}"
}

# 主循环
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    if check_service; then
        echo "服务运行正常"
        exit 0
    else
        echo "服务异常，尝试重启 (${retry_count}/${MAX_RETRIES})"
        restart_service
        
        if check_service; then
            send_alert "服务 $SERVICE_NAME 已自动恢复"
            exit 0
        fi
        
        retry_count=$((retry_count + 1))
        sleep $RETRY_INTERVAL
    fi
done

send_alert "服务 $SERVICE_NAME 自动恢复失败，需要人工干预"
exit 1
```

#### 手动恢复

```bash
#!/bin/bash
# manual_recovery.sh

echo "开始故障恢复流程..."

# 1. 停止服务
echo "停止应用服务..."
systemctl stop ai-browser-agent

# 2. 备份当前状态
echo "备份当前状态..."
cp -r /app/browser_data /backup/recovery_$(date +%Y%m%d_%H%M%S)
cp /app/logs/app.log /backup/recovery_$(date +%Y%m%d_%H%M%S).log

# 3. 清理临时文件
echo "清理临时文件..."
rm -rf /app/browser_data/tmp/*
rm -rf /tmp/playwright-*

# 4. 检查磁盘空间
echo "检查磁盘空间..."
df -h

# 5. 重启依赖服务
echo "重启依赖服务..."
systemctl restart postgresql
systemctl restart redis

# 6. 启动应用服务
echo "启动应用服务..."
systemctl start ai-browser-agent

# 7. 验证服务状态
echo "验证服务状态..."
sleep 10
curl -f http://localhost:8000/health || echo "健康检查失败"

echo "故障恢复完成"
```

## 运维最佳实践

### 1. 监控策略

- **实时监控**: 使用Prometheus + Grafana监控关键指标
- **日志聚合**: 使用ELK Stack或类似工具聚合日志
- **告警设置**: 设置合理的告警阈值和通知渠道
- **性能基线**: 建立性能基线，及时发现异常

### 2. 部署策略

- **蓝绿部署**: 使用蓝绿部署减少停机时间
- **滚动更新**: 在Kubernetes中使用滚动更新
- **回滚计划**: 准备快速回滚方案
- **测试验证**: 部署前充分测试

### 3. 安全管理

- **定期更新**: 及时更新系统和依赖包
- **访问控制**: 实施最小权限原则
- **安全扫描**: 定期进行安全漏洞扫描
- **备份加密**: 对备份数据进行加密

### 4. 容量规划

- **负载预测**: 根据业务增长预测负载
- **弹性扩展**: 实现自动扩缩容
- **资源监控**: 监控资源使用趋势
- **成本优化**: 平衡性能和成本

### 5. 文档维护

- **运维手册**: 维护详细的运维手册
- **故障记录**: 记录故障和解决方案
- **变更日志**: 记录所有变更操作
- **知识分享**: 定期进行知识分享

---

*本文档将根据项目发展持续更新，如有问题请联系运维团队。*