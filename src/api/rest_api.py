#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RESTful API接口

提供完整的REST API接口，包括认证、会话管理、指令执行等功能。
支持API文档生成和访问控制。
"""

import asyncio
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
import jwt

from src.common.logger import get_logger
from src.reasoning.agent import BrowserAgent


# JWT配置
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 安全认证
security = HTTPBearer()

# API模型定义
class Token(BaseModel):
    """访问令牌模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class InstructionRequest(BaseModel):
    """指令请求模型"""
    text: str = Field(..., min_length=1, max_length=1000, description="自然语言指令")
    session_id: Optional[str] = Field(None, max_length=100, description="会话ID")
    timeout: Optional[int] = Field(30, ge=1, le=300, description="超时时间(秒)")
    screenshot: Optional[bool] = Field(False, description="是否返回截图")


class ExecutionResponse(BaseModel):
    """执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    message: str = Field(..., description="执行结果消息")
    error: Optional[str] = Field(None, description="错误信息")
    screenshot: Optional[str] = Field(None, description="Base64编码的截图")
    session_id: str = Field(..., description="会话ID")
    execution_time: float = Field(..., description="执行时间(秒)")
    timestamp: str = Field(..., description="执行时间戳")


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话ID")
    created_at: str = Field(..., description="创建时间")
    last_activity: str = Field(..., description="最后活动时间")
    message_count: int = Field(..., description="消息数量")
    status: str = Field(..., description="会话状态")


class APIStatus(BaseModel):
    """API状态模型"""
    status: str = Field(..., description="API状态")
    version: str = Field(..., description="API版本")
    uptime: float = Field(..., description="运行时间(秒)")
    active_sessions: int = Field(..., description="活跃会话数")
    total_requests: int = Field(..., description="总请求数")


class RESTfulAPI:
    """RESTful API类"""

    def __init__(self, enable_auth: bool = False, rate_limit: int = 60):
        """初始化API
        
        Args:
            enable_auth: 是否启用认证
            rate_limit: 每分钟请求限制数量
        """
        self.logger = get_logger()
        self.enable_auth = enable_auth
        self.rate_limit = rate_limit
        self.app = FastAPI(
            title="AI浏览器代理 API",
            description="基于自然语言的网页自动化代理 RESTful API",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # 状态统计
        self.start_time = datetime.now()
        self.total_requests = 0
        
        # 会话管理
        self.agents: Dict[str, BrowserAgent] = {}
        self.session_states: Dict[str, Dict[str, Any]] = {}
        self.session_info: Dict[str, Dict[str, Any]] = {}
        
        # 速率限制
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        
        # 用户认证 (简单的内存存储，生产环境应使用数据库)
        self.users = {
            "admin": self._hash_password("admin123"),
            "user": self._hash_password("user123")
        }
        
        # 设置中间件
        self._setup_middleware()
        
        # 注册路由
        self._setup_routes()

    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return self._hash_password(password) == hashed

    def _create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def _verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """验证访问令牌"""
        if not self.enable_auth:
            return "anonymous"
            
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的认证凭据",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return username
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 在依赖中添加一个默认值None，这样当没有提供认证头时也不会报错
    def _verify_token_optional(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """验证访问令牌（可选）"""
        if not self.enable_auth:
            return "anonymous"
        
        # 如果没有提供认证信息，且启用了认证，则抛出异常
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的认证凭据",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return username
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _check_rate_limit(self, client_ip: str) -> bool:
        """检查速率限制"""
        now = time.time()
        minute_ago = now - 60
        
        # 清理过期的请求记录
        while self.request_counts[client_ip] and self.request_counts[client_ip][0] < minute_ago:
            self.request_counts[client_ip].popleft()
        
        # 检查是否超过限制
        if len(self.request_counts[client_ip]) >= self.rate_limit:
            return False
        
        # 记录当前请求
        self.request_counts[client_ip].append(now)
        return True

    def _setup_middleware(self):
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 请求统计和速率限制中间件
        @self.app.middleware("http")
        async def stats_and_rate_limit_middleware(request: Request, call_next):
            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            
            # 检查速率限制（跳过健康检查和文档页面）
            if not request.url.path.startswith(("/health", "/docs", "/redoc", "/openapi.json")):
                if not self._check_rate_limit(client_ip):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": f"请求过于频繁，每分钟最多 {self.rate_limit} 次请求"}
                    )
            
            # 统计请求
            self.total_requests += 1
            
            # 记录请求日志
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            self.logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s - "
                f"Client: {client_ip}"
            )
            
            return response

    def _setup_routes(self):
        """设置API路由"""
        
        # 定义依赖函数，根据是否启用认证来决定使用哪种验证方式
        def get_current_user_dependency():
            if self.enable_auth:
                return self._verify_token
            else:
                # 当认证禁用时，返回一个始终返回"anonymous"的函数
                async def anonymous_user():
                    return "anonymous"
                return anonymous_user
        
        current_user_dependency = get_current_user_dependency()
        
        # 认证相关路由
        @self.app.post("/api/auth/login", response_model=Token, tags=["认证"])
        async def login(login_data: LoginRequest):
            """用户登录"""
            if not self.enable_auth:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="认证功能未启用"
                )
                
            username = login_data.username
            password = login_data.password
            
            if username not in self.users or not self._verify_password(password, self.users[username]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token = self._create_access_token(data={"sub": username})
            return Token(access_token=access_token)

        # API状态路由
        @self.app.get("/api/status", response_model=APIStatus, tags=["系统"])
        async def get_api_status(current_user: str = Depends(current_user_dependency)):
            """获取API状态"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            return APIStatus(
                status="running",
                version="1.0.0",
                uptime=uptime,
                active_sessions=len(self.agents),
                total_requests=self.total_requests
            )

        # 会话管理路由
        @self.app.get("/api/sessions", response_model=List[SessionInfo], tags=["会话管理"])
        async def list_sessions(current_user: str = Depends(current_user_dependency)):
            """获取所有会话列表"""
            sessions = []
            for session_id, info in self.session_info.items():
                sessions.append(SessionInfo(
                    session_id=session_id,
                    created_at=info["created_at"],
                    last_activity=info["last_activity"],
                    message_count=info["message_count"],
                    status="active" if session_id in self.agents else "inactive"
                ))
            return sessions

        @self.app.post("/api/sessions", tags=["会话管理"])
        async def create_session(current_user: str = Depends(current_user_dependency)):
            """创建新会话"""
            session_id = secrets.token_urlsafe(16)
            
            # 初始化代理
            agent = BrowserAgent()
            await asyncio.to_thread(agent.initialize)
            
            self.agents[session_id] = agent
            self.session_states[session_id] = {}
            self.session_info[session_id] = {
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "message_count": 0
            }
            
            return {"session_id": session_id, "message": "会话创建成功"}

        @self.app.get("/api/sessions/{session_id}", response_model=SessionInfo, tags=["会话管理"])
        async def get_session(session_id: str, current_user: str = Depends(current_user_dependency)):
            """获取会话信息"""
            if session_id not in self.session_info:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            info = self.session_info[session_id]
            return SessionInfo(
                session_id=session_id,
                created_at=info["created_at"],
                last_activity=info["last_activity"],
                message_count=info["message_count"],
                status="active" if session_id in self.agents else "inactive"
            )

        @self.app.delete("/api/sessions/{session_id}", tags=["会话管理"])
        async def delete_session(session_id: str, current_user: str = Depends(current_user_dependency)):
            """删除会话"""
            if session_id in self.agents:
                await asyncio.to_thread(self.agents[session_id].cleanup)
                del self.agents[session_id]
                del self.session_states[session_id]
                del self.session_info[session_id]
                return {"message": f"会话 {session_id} 已删除"}
            else:
                raise HTTPException(status_code=404, detail="会话不存在")

        # 指令执行路由
        @self.app.post("/api/execute", response_model=ExecutionResponse, tags=["指令执行"])
        async def execute_instruction(
            instruction: InstructionRequest,
            current_user: str = Depends(current_user_dependency)
        ):
            """执行自然语言指令"""
            session_id = instruction.session_id or "default"
            start_time = datetime.now()

            # 确保会话存在
            if session_id not in self.agents:
                agent = BrowserAgent()
                await asyncio.to_thread(agent.initialize)
                self.agents[session_id] = agent
                self.session_states[session_id] = {}
                self.session_info[session_id] = {
                    "created_at": datetime.now().isoformat(),
                    "last_activity": datetime.now().isoformat(),
                    "message_count": 0
                }

            # 执行指令
            try:
                result = await asyncio.to_thread(
                    self.agents[session_id].execute,
                    instruction.text,
                    self.session_states[session_id]
                )

                # 更新会话状态
                if "session_state" in result:
                    self.session_states[session_id].update(result["session_state"])

                # 更新会话信息
                self.session_info[session_id]["last_activity"] = datetime.now().isoformat()
                self.session_info[session_id]["message_count"] += 1

                execution_time = (datetime.now() - start_time).total_seconds()

                return ExecutionResponse(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    error=result.get("error"),
                    screenshot=result.get("screenshot") if instruction.screenshot else None,
                    session_id=session_id,
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                self.logger.error(f"执行指令时发生错误: {str(e)}")
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return ExecutionResponse(
                    success=False,
                    message="执行失败",
                    error=str(e),
                    session_id=session_id,
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

        # 批量执行路由
        @self.app.post("/api/execute/batch", tags=["指令执行"])
        async def execute_batch_instructions(
            instructions: List[InstructionRequest],
            current_user: str = Depends(current_user_dependency)
        ):
            """批量执行指令"""
            if len(instructions) > 10:
                raise HTTPException(status_code=400, detail="批量执行最多支持10条指令")
            
            results = []
            for instruction in instructions:
                try:
                    result = await execute_instruction(instruction, current_user)
                    results.append(result)
                except Exception as e:
                    results.append(ExecutionResponse(
                        success=False,
                        message="执行失败",
                        error=str(e),
                        session_id=instruction.session_id or "default",
                        execution_time=0,
                        timestamp=datetime.now().isoformat()
                    ))
            
            return {"results": results, "total": len(results)}

        # 监控和日志路由
        @self.app.get("/api/logs", tags=["监控"])
        async def get_logs(
            lines: int = 100,
            level: str = "INFO",
            current_user: str = Depends(current_user_dependency)
        ):
            """获取系统日志"""
            try:
                from pathlib import Path
                log_file = Path("logs/agent.log")
                
                if not log_file.exists():
                    return {"logs": [], "message": "日志文件不存在"}
                
                # 读取日志文件的最后N行
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                # 过滤日志级别
                filtered_logs = []
                for line in recent_lines:
                    if level.upper() in line or level == "ALL":
                        filtered_logs.append(line.strip())
                
                return {
                    "logs": filtered_logs,
                    "total_lines": len(filtered_logs),
                    "log_level": level,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"获取日志时发生错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

        @self.app.get("/api/metrics", tags=["监控"])
        async def get_metrics(current_user: str = Depends(current_user_dependency)):
            """获取系统指标"""
            import psutil
            import gc
            
            # 获取系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取Python进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # 垃圾回收统计
            gc_stats = gc.get_stats()
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_total": memory.total,
                    "memory_available": memory.available,
                    "memory_percent": memory.percent,
                    "disk_total": disk.total,
                    "disk_free": disk.free,
                    "disk_percent": disk.percent
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "create_time": process.create_time()
                },
                "application": {
                    "active_sessions": len(self.agents),
                    "total_requests": self.total_requests,
                    "uptime": (datetime.now() - self.start_time).total_seconds(),
                    "gc_collections": sum(stat['collections'] for stat in gc_stats)
                },
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/sessions/{session_id}/screenshot", tags=["会话管理"])
        async def take_screenshot(
            session_id: str,
            current_user: str = Depends(current_user_dependency)
        ):
            """获取会话的当前页面截图"""
            if session_id not in self.agents:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            try:
                # 执行截图指令
                result = await asyncio.to_thread(
                    self.agents[session_id].execute,
                    "截图",
                    self.session_states[session_id]
                )
                
                return {
                    "success": result.get("success", False),
                    "screenshot": result.get("screenshot"),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"截图时发生错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"截图失败: {str(e)}")

        @self.app.get("/api/sessions/{session_id}/state", tags=["会话管理"])
        async def get_session_state(
            session_id: str,
            current_user: str = Depends(current_user_dependency)
        ):
            """获取会话状态"""
            if session_id not in self.session_states:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            return {
                "session_id": session_id,
                "state": self.session_states[session_id],
                "timestamp": datetime.now().isoformat()
            }

        @self.app.put("/api/sessions/{session_id}/state", tags=["会话管理"])
        async def update_session_state(
            session_id: str,
            state_data: dict,
            current_user: str = Depends(current_user_dependency)
        ):
            """更新会话状态"""
            if session_id not in self.session_states:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            # 更新状态
            self.session_states[session_id].update(state_data)
            
            # 更新活动时间
            if session_id in self.session_info:
                self.session_info[session_id]["last_activity"] = datetime.now().isoformat()
            
            return {
                "message": "会话状态已更新",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

        # 健康检查路由
        @self.app.get("/health", tags=["系统"])
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        # 静态文件服务
        try:
            project_root = Path(__file__).resolve().parents[2]
            static_dir = project_root / "static"
            if static_dir.exists():
                self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
                
                @self.app.get("/", response_class=HTMLResponse)
                async def serve_index():
                    """服务主页"""
                    index_file = static_dir / "index.html"
                    if index_file.exists():
                        return HTMLResponse(content=index_file.read_text(encoding='utf-8'))
                    return HTMLResponse("<h1>AI浏览器代理 API</h1><p>访问 <a href='/docs'>/docs</a> 查看API文档</p>")
        except Exception as e:
            self.logger.warning(f"挂载静态文件目录失败: {str(e)}")

    def start(self, host: str = "127.0.0.1", port: int = 8000):
        """启动API服务器"""
        self.logger.info(f"启动RESTful API服务器，地址: {host}:{port}")
        if self.enable_auth:
            self.logger.info("认证功能已启用")
        else:
            self.logger.info("认证功能已禁用")
        
        uvicorn.run(self.app, host=host, port=port)

    async def cleanup(self):
        """清理资源"""
        for session_id, agent in self.agents.items():
            await asyncio.to_thread(agent.cleanup)
        self.agents.clear()
        self.session_states.clear()
        self.session_info.clear()