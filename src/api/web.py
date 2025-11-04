#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web交互界面

提供基于Web的用户交互界面，使用FastAPI实现RESTful API和WebSocket通信。
现在基于增强的RESTful API实现。
"""

import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from src.common.logger import get_logger
from src.reasoning.agent import BrowserAgent
from src.api.rest_api import RESTfulAPI


# 定义API模型
class Instruction(BaseModel):
    """指令模型"""
    text: str
    session_id: Optional[str] = None


class ExecutionResult(BaseModel):
    """执行结果模型"""
    success: bool
    message: str
    error: Optional[str] = None
    screenshot: Optional[str] = None  # Base64编码的截图
    session_id: Optional[str] = None


class WebInterface:
    """Web交互界面类"""

    def __init__(self, enable_auth: bool = False):
        """初始化Web界面
        
        Args:
            enable_auth: 是否启用API认证
        """
        self.logger = get_logger()
        
        # 使用增强的RESTful API
        self.rest_api = RESTfulAPI(enable_auth=enable_auth)
        self.app = self.rest_api.app
        
        # WebSocket连接管理
        self.active_connections: Dict[str, WebSocket] = {}

        # 注册WebSocket路由
        self._setup_websocket_routes()

    def _setup_websocket_routes(self):
        """设置WebSocket路由"""
        
        # WebSocket API
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket端点"""
            await websocket.accept()
            self.active_connections[session_id] = websocket

            # 确保会话存在
            if session_id not in self.rest_api.agents:
                agent = BrowserAgent()
                await asyncio.to_thread(agent.initialize)
                self.rest_api.agents[session_id] = agent
                self.rest_api.session_states[session_id] = {}
                self.rest_api.session_info[session_id] = {
                    "created_at": asyncio.get_event_loop().time(),
                    "last_activity": asyncio.get_event_loop().time(),
                    "message_count": 0
                }

            try:
                while True:
                    # 接收指令
                    data = await websocket.receive_json()
                    instruction = data.get("instruction", "")

                    # 执行指令
                    try:
                        await websocket.send_json({"type": "status", "message": "执行中..."})
                        result = await asyncio.to_thread(
                            self.rest_api.agents[session_id].execute,
                            instruction,
                            self.rest_api.session_states[session_id]
                        )

                        # 更新会话状态
                        if "session_state" in result:
                            self.rest_api.session_states[session_id].update(result["session_state"])

                        # 更新会话信息
                        self.rest_api.session_info[session_id]["last_activity"] = asyncio.get_event_loop().time()
                        self.rest_api.session_info[session_id]["message_count"] += 1

                        # 发送结果
                        await websocket.send_json({
                            "type": "result",
                            "success": result.get("success", False),
                            "message": result.get("message", ""),
                            "error": result.get("error"),
                            "screenshot": result.get("screenshot")
                        })
                    except Exception as e:
                        self.logger.error(f"执行指令时发生错误: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e)
                        })
            except WebSocketDisconnect:
                self.logger.info(f"客户端断开连接: {session_id}")
                if session_id in self.active_connections:
                    del self.active_connections[session_id]
            except Exception as e:
                self.logger.error(f"WebSocket处理时发生错误: {str(e)}")
                if session_id in self.active_connections:
                    del self.active_connections[session_id]

    def start(self, host: str = "127.0.0.1", port: int = 8000):
        """启动Web服务器"""
        self.logger.info(f"启动Web界面，地址: {host}:{port}")
        self.rest_api.start(host, port)

    async def cleanup(self):
        """清理资源"""
        await self.rest_api.cleanup()
        self.active_connections.clear()