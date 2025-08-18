# AI 浏览器代理接口设计

本文档详细描述了AI浏览器代理系统中各模块之间的接口设计，包括数据结构、方法签名和交互流程。

## 1. 感知层接口 (Perception Layer Interfaces)

### 1.1 WebPageParser 接口

```python
class WebPageParser:
    async def parse(self, page) -> Dict[str, Any]:
        """
        解析网页内容，提取结构化数据
        
        参数:
            page: Playwright页面对象
            
        返回:
            包含网页结构化数据的字典
        """
        pass
    
    async def extract_dom_structure(self, page) -> Dict[str, Any]:
        """
        提取DOM结构
        
        参数:
            page: Playwright页面对象
            
        返回:
            DOM结构的字典表示
        """
        pass
    
    async def extract_accessibility_tree(self, page) -> Dict[str, Any]:
        """
        提取辅助功能树
        
        参数:
            page: Playwright页面对象
            
        返回:
            辅助功能树的字典表示
        """
        pass
```

### 1.2 IntentExtractor 接口

```python
class IntentExtractor:
    def extract_intents(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从页面数据中提取可能的用户意图
        
        参数:
            page_data: 页面结构化数据
            
        返回:
            页面意图图谱
        """
        pass
    
    def identify_interactive_elements(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        识别页面中的交互元素
        
        参数:
            page_data: 页面结构化数据
            
        返回:
            交互元素列表
        """
        pass
    
    def identify_forms(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        识别页面中的表单
        
        参数:
            page_data: 页面结构化数据
            
        返回:
            表单列表
        """
        pass
    
    def identify_navigation(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        识别页面中的导航元素
        
        参数:
            page_data: 页面结构化数据
            
        返回:
            导航元素字典
        """
        pass
```

### 1.3 PageMonitor 接口

```python
class PageMonitor:
    async def start_monitoring(self, page) -> None:
        """
        开始监控页面变化
        
        参数:
            page: Playwright页面对象
        """
        pass
    
    async def stop_monitoring(self) -> None:
        """
        停止监控页面变化
        """
        pass
    
    def add_change_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        添加页面变化监听器
        
        参数:
            callback: 当页面变化时调用的回调函数
        """
        pass
    
    def remove_change_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        移除页面变化监听器
        
        参数:
            callback: 要移除的回调函数
        """
        pass
```

## 2. 推理层接口 (Reasoning Layer Interfaces)

### 2.1 DialogueManager 接口

```python
class DialogueManager:
    def add_user_message(self, message: str) -> None:
        """
        添加用户消息到对话历史
        
        参数:
            message: 用户消息
        """
        pass
    
    def add_system_message(self, message: str) -> None:
        """
        添加系统消息到对话历史
        
        参数:
            message: 系统消息
        """
        pass
    
    def get_dialogue_history(self, max_turns: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        参数:
            max_turns: 最大对话轮数，None表示获取全部
            
        返回:
            对话历史列表
        """
        pass
    
    def clear_history(self) -> None:
        """
        清除对话历史
        """
        pass
    
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入，提取意图
        
        参数:
            user_input: 用户输入的自然语言指令
            
        返回:
            用户意图
        """
        pass
```

### 2.2 TaskPlanner 接口

```python
class TaskPlanner:
    async def plan_tasks(self, user_intent: Dict[str, Any], page_intent_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据用户意图和页面意图图谱规划任务
        
        参数:
            user_intent: 用户意图
            page_intent_graph: 页面意图图谱
            
        返回:
            任务执行计划
        """
        pass
    
    def decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将复杂任务分解为简单子任务
        
        参数:
            task: 复杂任务
            
        返回:
            子任务列表
        """
        pass
    
    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对任务进行优先级排序
        
        参数:
            tasks: 任务列表
            
        返回:
            排序后的任务列表
        """
        pass
```

### 2.3 InstructionGenerator 接口

```python
class InstructionGenerator:
    async def generate_instructions(self, task_plan: Dict[str, Any], page_intent_graph: Dict[str, Any], dialogue_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成执行指令
        
        参数:
            task_plan: 任务执行计划
            page_intent_graph: 页面意图图谱
            dialogue_history: 对话历史
            
        返回:
            指令列表
        """
        pass
    
    async def generate_single_instruction(self, task: Dict[str, Any], page_intent_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成单个指令
        
        参数:
            task: 任务
            page_intent_graph: 页面意图图谱
            
        返回:
            指令
        """
        pass
    
    def validate_instruction(self, instruction: Dict[str, Any]) -> bool:
        """
        验证指令是否符合规范
        
        参数:
            instruction: 指令
            
        返回:
            是否有效
        """
        pass
```

## 3. 执行层接口 (Action Layer Interfaces)

### 3.1 ActionExecutor 接口

```python
class ActionExecutor:
    async def execute(self, instruction: Dict[str, Any], page, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指令
        
        参数:
            instruction: 指令
            page: Playwright页面对象
            session_state: 会话状态
            
        返回:
            执行结果
        """
        pass
    
    async def execute_batch(self, instructions: List[Dict[str, Any]], page, session_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        批量执行指令
        
        参数:
            instructions: 指令列表
            page: Playwright页面对象
            session_state: 会话状态
            
        返回:
            执行结果列表
        """
        pass
    
    def get_supported_actions(self) -> List[str]:
        """
        获取支持的动作类型
        
        返回:
            动作类型列表
        """
        pass
```

### 3.2 StateManager 接口

```python
class StateManager:
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        获取状态值
        
        参数:
            key: 状态键
            default: 默认值
            
        返回:
            状态值
        """
        pass
    
    def set_state(self, key: str, value: Any) -> None:
        """
        设置状态值
        
        参数:
            key: 状态键
            value: 状态值
        """
        pass
    
    def delete_state(self, key: str) -> None:
        """
        删除状态
        
        参数:
            key: 状态键
        """
        pass
    
    def clear_state(self) -> None:
        """
        清除所有状态
        """
        pass
    
    def save_state(self, file_path: str) -> None:
        """
        保存状态到文件
        
        参数:
            file_path: 文件路径
        """
        pass
    
    def load_state(self, file_path: str) -> None:
        """
        从文件加载状态
        
        参数:
            file_path: 文件路径
        """
        pass
```

### 3.3 ErrorHandler 接口

```python
class ErrorHandler:
    def handle_error(self, error: Exception, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理执行错误
        
        参数:
            error: 异常
            instruction: 导致错误的指令
            context: 执行上下文
            
        返回:
            错误处理结果
        """
        pass
    
    def diagnose_error(self, error: Exception, instruction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        诊断错误原因
        
        参数:
            error: 异常
            instruction: 导致错误的指令
            context: 执行上下文
            
        返回:
            错误诊断结果
        """
        pass
    
    def suggest_recovery(self, error_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        建议恢复策略
        
        参数:
            error_diagnosis: 错误诊断结果
            
        返回:
            恢复建议
        """
        pass
```

## 4. 跨层接口 (Cross-Layer Interfaces)

### 4.1 BrowserAgent 接口

```python
class BrowserAgent:
    async def initialize(self, headless: bool = False) -> None:
        """
        初始化浏览器代理
        
        参数:
            headless: 是否使用无头模式
        """
        pass
    
    async def close(self) -> None:
        """
        关闭浏览器代理
        """
        pass
    
    async def process_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        处理用户指令
        
        参数:
            instruction: 用户自然语言指令
            
        返回:
            处理结果
        """
        pass
    
    async def get_page_state(self) -> Dict[str, Any]:
        """
        获取当前页面状态
        
        返回:
            页面状态
        """
        pass
    
    async def take_screenshot(self) -> bytes:
        """
        截取当前页面截图
        
        返回:
            截图数据
        """
        pass
```

### 4.2 PluginManager 接口

```python
class PluginManager:
    def register_plugin(self, plugin) -> None:
        """
        注册插件
        
        参数:
            plugin: 插件实例
        """
        pass
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """
        注销插件
        
        参数:
            plugin_name: 插件名称
        """
        pass
    
    def get_plugin(self, plugin_name: str) -> Any:
        """
        获取插件实例
        
        参数:
            plugin_name: 插件名称
            
        返回:
            插件实例
        """
        pass
    
    def get_all_plugins(self) -> List[Any]:
        """
        获取所有插件
        
        返回:
            插件列表
        """
        pass
    
    def hook_before_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        动作执行前的钩子
        
        参数:
            action: 动作
            context: 上下文
            
        返回:
            可能被修改的动作
        """
        pass
    
    def hook_after_action(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        动作执行后的钩子
        
        参数:
            result: 执行结果
            context: 上下文
            
        返回:
            可能被修改的结果
        """
        pass
```

## 5. 数据模型 (Data Models)

### 5.1 页面意图图谱 (PageIntentGraph)

```python
class InteractiveElement(BaseModel):
    type: str
    text: Optional[str] = None
    intent: Optional[str] = None
    selector: Dict[str, str]
    state: str
    position: Optional[Dict[str, int]] = None

class FormField(BaseModel):
    name: str
    type: str
    required: bool = False
    selector: Dict[str, str]

class Form(BaseModel):
    intent: Optional[str] = None
    fields: List[FormField]
    submit: Dict[str, Dict[str, str]]

class NavigationLink(BaseModel):
    text: str
    url: str
    selector: Dict[str, str]

class ContentSection(BaseModel):
    type: str
    text_summary: str
    selector: Dict[str, str]

class PageIntentGraph(BaseModel):
    page_title: str
    page_url: str
    interactive_elements: List[InteractiveElement]
    forms: List[Form]
    navigation: Dict[str, List[NavigationLink]]
    content_sections: List[ContentSection]
```

### 5.2 指令 (Instruction)

```python
class Selector(BaseModel):
    type: str  # css, xpath, text, etc.
    value: str

class InstructionOptions(BaseModel):
    timeout: Optional[int] = 5000
    force: Optional[bool] = False
    # 其他选项...

class Instruction(BaseModel):
    action: str
    selector: Optional[Selector] = None
    value: Optional[Any] = None
    options: Optional[InstructionOptions] = None
    description: str
```

### 5.3 执行结果 (ExecutionResult)

```python
class ExecutionResult(BaseModel):
    status: str  # success, error
    message: str
    data: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None  # base64编码的截图
```

## 6. API接口 (API Interfaces)

### 6.1 REST API

```
POST /api/v1/instruction
请求体:
{
    "instruction": "登录京东账号",
    "session_id": "abc123"
}

响应:
{
    "status": "success",
    "result": {
        "message": "操作成功完成",
        "screenshot": "base64编码的截图"
    }
}
```

```
GET /api/v1/session/{session_id}/state
响应:
{
    "status": "success",
    "state": {
        "current_url": "https://www.jd.com",
        "page_title": "京东",
        "logged_in": true
    }
}
```

```
POST /api/v1/session/{session_id}/screenshot
响应:
{
    "status": "success",
    "screenshot": "base64编码的截图"
}
```

### 6.2 WebSocket API

```
WS /api/v1/session/{session_id}/stream

客户端发送:
{
    "type": "instruction",
    "data": {
        "instruction": "搜索iPhone"
    }
}

服务器响应:
{
    "type": "status_update",
    "data": {
        "status": "processing",
        "message": "正在执行搜索操作"
    }
}

{
    "type": "result",
    "data": {
        "status": "success",
        "message": "搜索完成",
        "screenshot": "base64编码的截图"
    }
}
```

## 7. 事件系统 (Event System)

### 7.1 事件类型

```python
class EventType(Enum):
    PAGE_LOADED = "page_loaded"
    PAGE_CHANGED = "page_changed"
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
    ERROR_OCCURRED = "error_occurred"
    SESSION_CREATED = "session_created"
    SESSION_CLOSED = "session_closed"
```

### 7.2 事件接口

```python
class Event(BaseModel):
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]

class EventEmitter:
    def on(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        注册事件监听器
        
        参数:
            event_type: 事件类型
            callback: 回调函数
        """
        pass
    
    def off(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        移除事件监听器
        
        参数:
            event_type: 事件类型
            callback: 回调函数
        """
        pass
    
    def emit(self, event: Event) -> None:
        """
        触发事件
        
        参数:
            event: 事件对象
        """
        pass
```

## 8. 配置接口 (Configuration Interface)

```python
class Config:
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        参数:
            key: 配置键
            default: 默认值
            
        返回:
            配置值
        """
        pass
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        参数:
            key: 配置键
            value: 配置值
        """
        pass
    
    def load_from_file(self, file_path: str) -> None:
        """
        从文件加载配置
        
        参数:
            file_path: 文件路径
        """
        pass
    
    def save_to_file(self, file_path: str) -> None:
        """
        保存配置到文件
        
        参数:
            file_path: 文件路径
        """
        pass
```

## 9. 日志接口 (Logging Interface)

```python
class Logger:
    def debug(self, message: str, **kwargs) -> None:
        """
        记录调试日志
        
        参数:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    def info(self, message: str, **kwargs) -> None:
        """
        记录信息日志
        
        参数:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    def warning(self, message: str, **kwargs) -> None:
        """
        记录警告日志
        
        参数:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    def error(self, message: str, **kwargs) -> None:
        """
        记录错误日志
        
        参数:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    def critical(self, message: str, **kwargs) -> None:
        """
        记录严重错误日志
        
        参数:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
```

## 10. 总结

本文档详细描述了AI浏览器代理系统中各模块的接口设计，包括感知层、推理层、执行层的核心接口，以及跨层接口、数据模型、API接口、事件系统、配置接口和日志接口。这些接口定义了系统各组件之间的交互方式，为系统的实现提供了清晰的指导。