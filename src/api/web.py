#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web交互界面

提供基于Web的用户交互界面，使用FastAPI实现RESTful API和WebSocket通信。
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

    def __init__(self):
        """初始化Web界面"""
        self.logger = get_logger()
        self.app = FastAPI(title="AI浏览器代理", description="基于自然语言的网页自动化代理")
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, BrowserAgent] = {}
        self.session_states: Dict[str, Dict[str, Any]] = {}

        # 设置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 注册路由
        self._setup_routes()

    def _setup_routes(self):
        """设置API路由"""
        # RESTful API
        @self.app.post("/api/execute", response_model=ExecutionResult)
        async def execute_instruction(instruction: Instruction):
            """执行指令"""
            session_id = instruction.session_id or "default"

            # 确保会话存在
            if session_id not in self.agents:
                agent = BrowserAgent()
                await asyncio.to_thread(agent.initialize)
                self.agents[session_id] = agent
                self.session_states[session_id] = {}

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

                return ExecutionResult(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    error=result.get("error"),
                    screenshot=result.get("screenshot"),
                    session_id=session_id
                )
            except Exception as e:
                self.logger.error(f"执行指令时发生错误: {str(e)}")
                return ExecutionResult(
                    success=False,
                    message="执行失败",
                    error=str(e),
                    session_id=session_id
                )

        @self.app.delete("/api/sessions/{session_id}")
        async def close_session(session_id: str):
            """关闭会话"""
            if session_id in self.agents:
                await asyncio.to_thread(self.agents[session_id].cleanup)
                del self.agents[session_id]
                del self.session_states[session_id]
                return {"success": True, "message": f"会话 {session_id} 已关闭"}
            else:
                raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")

        # WebSocket API
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket端点"""
            await websocket.accept()
            self.active_connections[session_id] = websocket

            # 确保会话存在
            if session_id not in self.agents:
                agent = BrowserAgent()
                await asyncio.to_thread(agent.initialize)
                self.agents[session_id] = agent
                self.session_states[session_id] = {}

            try:
                while True:
                    # 接收指令
                    data = await websocket.receive_json()
                    instruction = data.get("instruction", "")

                    # 执行指令
                    try:
                        await websocket.send_json({"type": "status", "message": "执行中..."})
                        result = await asyncio.to_thread(
                            self.agents[session_id].execute,
                            instruction,
                            self.session_states[session_id]
                        )

                        # 更新会话状态
                        if "session_state" in result:
                            self.session_states[session_id].update(result["session_state"])

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

        # 静态文件
        try:
            project_root = Path(__file__).resolve().parents[2]
            static_dir = project_root / "static"
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            self.app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="root")
        except Exception as e:
            self.logger.warning(f"挂载静态文件目录失败: {str(e)}")

    def start(self, host: str = "127.0.0.1", port: int = 8000):
        """启动Web服务器"""
        self.logger.info(f"启动Web界面，地址: {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

    async def cleanup(self):
        """清理资源"""
        for session_id, agent in self.agents.items():
            await asyncio.to_thread(agent.cleanup)
        self.agents.clear()
        self.session_states.clear()