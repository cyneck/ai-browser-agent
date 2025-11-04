#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI浏览器代理 API 使用示例

演示如何使用RESTful API进行各种操作。
"""

import requests
import json
import time
import asyncio
import websockets
from typing import Optional


class BrowserAgentAPIClient:
    """AI浏览器代理API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        """初始化客户端
        
        Args:
            base_url: API基础URL
            token: 访问令牌（如果启用了认证）
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
    
    def login(self, username: str, password: str) -> str:
        """登录获取访问令牌
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            访问令牌
        """
        response = self.session.post(f"{self.base_url}/api/auth/login", json={
            "username": username,
            "password": password
        })
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })
        
        return self.token
    
    def get_status(self) -> dict:
        """获取API状态"""
        response = self.session.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()
    
    def create_session(self) -> str:
        """创建新会话
        
        Returns:
            会话ID
        """
        response = self.session.post(f"{self.base_url}/api/sessions")
        response.raise_for_status()
        return response.json()["session_id"]
    
    def list_sessions(self) -> list:
        """获取所有会话列表"""
        response = self.session.get(f"{self.base_url}/api/sessions")
        response.raise_for_status()
        return response.json()
    
    def get_session(self, session_id: str) -> dict:
        """获取会话信息"""
        response = self.session.get(f"{self.base_url}/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def delete_session(self, session_id: str) -> dict:
        """删除会话"""
        response = self.session.delete(f"{self.base_url}/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def execute_instruction(self, text: str, session_id: Optional[str] = None, 
                          screenshot: bool = False, timeout: int = 30) -> dict:
        """执行单条指令
        
        Args:
            text: 自然语言指令
            session_id: 会话ID
            screenshot: 是否返回截图
            timeout: 超时时间
            
        Returns:
            执行结果
        """
        data = {
            "text": text,
            "screenshot": screenshot,
            "timeout": timeout
        }
        
        if session_id:
            data["session_id"] = session_id
        
        response = self.session.post(f"{self.base_url}/api/execute", json=data)
        response.raise_for_status()
        return response.json()
    
    def execute_batch(self, instructions: list) -> dict:
        """批量执行指令
        
        Args:
            instructions: 指令列表
            
        Returns:
            批量执行结果
        """
        response = self.session.post(f"{self.base_url}/api/execute/batch", json=instructions)
        response.raise_for_status()
        return response.json()


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 创建客户端
    client = BrowserAgentAPIClient()
    
    # 获取API状态
    status = client.get_status()
    print(f"API状态: {status['status']}")
    print(f"活跃会话数: {status['active_sessions']}")
    
    # 创建会话
    session_id = client.create_session()
    print(f"创建会话: {session_id}")
    
    # 执行指令
    result = client.execute_instruction("打开百度", session_id=session_id)
    print(f"执行结果: {result['success']}")
    print(f"消息: {result['message']}")
    print(f"执行时间: {result['execution_time']:.2f}秒")
    
    # 获取会话信息
    session_info = client.get_session(session_id)
    print(f"会话消息数: {session_info['message_count']}")
    
    # 删除会话
    client.delete_session(session_id)
    print("会话已删除")


def example_with_authentication():
    """带认证的使用示例"""
    print("\n=== 带认证的使用示例 ===")
    
    # 创建客户端
    client = BrowserAgentAPIClient()
    
    try:
        # 登录
        token = client.login("admin", "admin123")
        print(f"登录成功，令牌: {token[:20]}...")
        
        # 执行操作
        result = client.execute_instruction("获取页面信息")
        print(f"执行结果: {result['success']}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 501:
            print("认证功能未启用，请使用 --auth 参数启动服务")
        else:
            print(f"认证失败: {e}")


def example_batch_execution():
    """批量执行示例"""
    print("\n=== 批量执行示例 ===")
    
    client = BrowserAgentAPIClient()
    
    # 创建会话
    session_id = client.create_session()
    
    # 准备批量指令
    instructions = [
        {"text": "打开百度", "session_id": session_id},
        {"text": "搜索Python", "session_id": session_id},
        {"text": "点击第一个搜索结果", "session_id": session_id}
    ]
    
    # 批量执行
    results = client.execute_batch(instructions)
    print(f"批量执行完成，总数: {results['total']}")
    
    for i, result in enumerate(results['results'], 1):
        print(f"指令{i}: {'成功' if result['success'] else '失败'} - {result['message']}")
    
    # 清理
    client.delete_session(session_id)


def example_screenshot_capture():
    """截图捕获示例"""
    print("\n=== 截图捕获示例 ===")
    
    client = BrowserAgentAPIClient()
    
    # 执行指令并获取截图
    result = client.execute_instruction("打开百度", screenshot=True)
    
    if result['success'] and result['screenshot']:
        # 保存截图
        import base64
        screenshot_data = base64.b64decode(result['screenshot'])
        
        with open('screenshot.png', 'wb') as f:
            f.write(screenshot_data)
        
        print("截图已保存为 screenshot.png")
        print(f"截图大小: {len(screenshot_data)} 字节")
    else:
        print("未获取到截图")


async def example_websocket_usage():
    """WebSocket使用示例"""
    print("\n=== WebSocket使用示例 ===")
    
    session_id = "websocket_test"
    uri = f"ws://localhost:8000/ws/{session_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket连接已建立")
            
            # 发送指令
            await websocket.send(json.dumps({
                "instruction": "打开百度"
            }))
            
            # 接收响应
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                print(f"收到消息: {data['type']}")
                
                if data['type'] == 'result':
                    print(f"执行结果: {'成功' if data['success'] else '失败'}")
                    print(f"消息: {data['message']}")
                    break
                elif data['type'] == 'error':
                    print(f"执行错误: {data['message']}")
                    break
                elif data['type'] == 'status':
                    print(f"状态: {data['message']}")
    
    except Exception as e:
        print(f"WebSocket连接失败: {e}")
        print("请确保服务正在运行")


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    client = BrowserAgentAPIClient()
    
    try:
        # 尝试获取不存在的会话
        client.get_session("nonexistent_session")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误 {e.response.status_code}: {e.response.json()['detail']}")
    
    try:
        # 尝试执行无效指令
        result = client.execute_instruction("")
    except requests.exceptions.HTTPError as e:
        print(f"请求错误: {e.response.json()['detail']}")
    
    # 执行可能失败的指令
    result = client.execute_instruction("点击不存在的元素")
    if not result['success']:
        print(f"指令执行失败: {result['error']}")


def example_session_management():
    """会话管理示例"""
    print("\n=== 会话管理示例 ===")
    
    client = BrowserAgentAPIClient()
    
    # 创建多个会话
    sessions = []
    for i in range(3):
        session_id = client.create_session()
        sessions.append(session_id)
        print(f"创建会话 {i+1}: {session_id}")
    
    # 在不同会话中执行指令
    for i, session_id in enumerate(sessions):
        result = client.execute_instruction(f"打开百度搜索{i+1}", session_id=session_id)
        print(f"会话{i+1}执行结果: {result['success']}")
    
    # 列出所有会话
    all_sessions = client.list_sessions()
    print(f"\n当前活跃会话数: {len(all_sessions)}")
    
    for session in all_sessions:
        print(f"会话 {session['session_id']}: {session['message_count']} 条消息")
    
    # 清理所有会话
    for session_id in sessions:
        client.delete_session(session_id)
        print(f"删除会话: {session_id}")


def example_monitoring_and_metrics():
    """监控和指标示例"""
    print("\n=== 监控和指标示例 ===")
    
    client = BrowserAgentAPIClient()
    
    try:
        # 获取系统指标
        metrics = client.session.get(f"{client.base_url}/api/metrics").json()
        print("系统指标:")
        print(f"  CPU使用率: {metrics['system']['cpu_percent']:.1f}%")
        print(f"  内存使用率: {metrics['system']['memory_percent']:.1f}%")
        print(f"  活跃会话数: {metrics['application']['active_sessions']}")
        print(f"  总请求数: {metrics['application']['total_requests']}")
        print(f"  运行时间: {metrics['application']['uptime']:.1f}秒")
        
        # 获取日志
        logs = client.session.get(f"{client.base_url}/api/logs?lines=5&level=INFO").json()
        print(f"\n最近的日志 ({len(logs['logs'])} 条):")
        for log in logs['logs'][-3:]:  # 显示最后3条
            print(f"  {log}")
            
    except requests.exceptions.HTTPError as e:
        print(f"获取监控数据失败: {e}")


def example_advanced_session_management():
    """高级会话管理示例"""
    print("\n=== 高级会话管理示例 ===")
    
    client = BrowserAgentAPIClient()
    
    # 创建会话
    session_id = client.create_session()
    print(f"创建会话: {session_id}")
    
    try:
        # 执行一些操作来改变会话状态
        client.execute_instruction("打开百度", session_id=session_id)
        
        # 获取会话状态
        state_response = client.session.get(f"{client.base_url}/api/sessions/{session_id}/state")
        if state_response.status_code == 200:
            state = state_response.json()
            print(f"当前会话状态: {state['state']}")
        
        # 手动更新会话状态
        new_state = {
            "user_preference": "简洁模式",
            "last_search": "Python教程",
            "step_count": 1
        }
        update_response = client.session.put(
            f"{client.base_url}/api/sessions/{session_id}/state",
            json=new_state
        )
        if update_response.status_code == 200:
            print("会话状态已更新")
        
        # 获取会话截图
        screenshot_response = client.session.post(f"{client.base_url}/api/sessions/{session_id}/screenshot")
        if screenshot_response.status_code == 200:
            screenshot_data = screenshot_response.json()
            if screenshot_data['success'] and screenshot_data['screenshot']:
                print("截图获取成功")
                # 可以保存截图
                import base64
                screenshot_bytes = base64.b64decode(screenshot_data['screenshot'])
                with open(f'session_{session_id}_screenshot.png', 'wb') as f:
                    f.write(screenshot_bytes)
                print(f"截图已保存为 session_{session_id}_screenshot.png")
            else:
                print("截图获取失败")
        
    finally:
        # 清理会话
        client.delete_session(session_id)


def example_rate_limiting():
    """速率限制示例"""
    print("\n=== 速率限制示例 ===")
    
    client = BrowserAgentAPIClient()
    
    print("快速发送多个请求测试速率限制...")
    success_count = 0
    rate_limited_count = 0
    
    for i in range(10):
        try:
            response = client.session.get(f"{client.base_url}/api/status")
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"请求 {i+1} 被速率限制")
        except Exception as e:
            print(f"请求 {i+1} 失败: {e}")
    
    print(f"成功请求: {success_count}, 被限制请求: {rate_limited_count}")


def example_concurrent_sessions():
    """并发会话示例"""
    print("\n=== 并发会话示例 ===")
    
    import concurrent.futures
    import threading
    
    def worker_session(worker_id):
        """工作线程函数"""
        client = BrowserAgentAPIClient()
        session_id = client.create_session()
        
        try:
            # 执行一些操作
            result = client.execute_instruction(f"工作线程{worker_id}的任务", session_id=session_id)
            return {
                "worker_id": worker_id,
                "session_id": session_id,
                "success": result['success'],
                "message": result['message']
            }
        finally:
            client.delete_session(session_id)
    
    # 创建多个并发会话
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker_session, i) for i in range(3)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    print("并发会话执行结果:")
    for result in results:
        print(f"  工作线程{result['worker_id']}: {'成功' if result['success'] else '失败'}")


def example_api_integration():
    """API集成示例"""
    print("\n=== API集成示例 ===")
    
    client = BrowserAgentAPIClient()
    
    # 模拟一个完整的自动化流程
    session_id = client.create_session()
    
    try:
        workflow_steps = [
            "打开百度首页",
            "搜索'Python编程'",
            "点击第一个搜索结果",
            "获取页面标题"
        ]
        
        print("执行自动化工作流程:")
        for i, step in enumerate(workflow_steps, 1):
            print(f"  步骤{i}: {step}")
            result = client.execute_instruction(step, session_id=session_id)
            
            if result['success']:
                print(f"    ✓ 成功: {result['message']}")
            else:
                print(f"    ✗ 失败: {result.get('error', '未知错误')}")
                break
            
            # 获取当前会话状态
            session_info = client.get_session(session_id)
            print(f"    会话消息数: {session_info['message_count']}")
        
        print("\n工作流程完成")
        
    finally:
        client.delete_session(session_id)


def main():
    """主函数"""
    print("AI浏览器代理 API 使用示例")
    print("请确保服务正在运行: python src/main.py --web")
    print("=" * 50)
    
    try:
        # 基础使用
        example_basic_usage()
        
        # 带认证的使用
        example_with_authentication()
        
        # 批量执行
        example_batch_execution()
        
        # 截图捕获
        example_screenshot_capture()
        
        # 会话管理
        example_session_management()
        
        # 高级会话管理
        example_advanced_session_management()
        
        # 监控和指标
        example_monitoring_and_metrics()
        
        # 速率限制
        example_rate_limiting()
        
        # 并发会话
        example_concurrent_sessions()
        
        # API集成
        example_api_integration()
        
        # 错误处理
        example_error_handling()
        
        # WebSocket使用
        print("\n启动WebSocket示例...")
        asyncio.run(example_websocket_usage())
        
    except requests.exceptions.ConnectionError:
        print("连接失败！请确保AI浏览器代理服务正在运行。")
        print("启动命令: python src/main.py --web")
    except KeyboardInterrupt:
        print("\n示例已中断")
    except Exception as e:
        print(f"示例执行出错: {e}")


if __name__ == "__main__":
    main()