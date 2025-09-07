#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
指令数据模型

定义系统中使用的指令数据实体，包括基本指令、多步骤指令等。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class ActionType(Enum):
    """动作类型枚举"""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    TYPE = "type"
    KEY = "key"
    SELECT = "select"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"
    EXTRACT_RESULTS = "extract_results"
    SCROLL = "scroll"
    BACK = "back"
    FORWARD = "forward"
    REFRESH = "refresh"
    CLOSE = "close"
    ERROR = "error"
    WAIT_FOR_LOGIN = "wait_for_login"
    SMART_FILL = "smart_fill"
    SMART_SUBMIT = "smart_submit"
    SAVE_AS_PDF = "save_as_pdf"
    SAVE_AS_MHTML = "save_as_mhtml"


@dataclass
class BaseAction:
    """基础动作数据实体"""
    action: ActionType
    description: str = ""
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: Optional[int] = None


@dataclass
class NavigateAction(BaseAction):
    """导航动作"""
    action: ActionType = ActionType.NAVIGATE
    url: str = ""


@dataclass
class ClickAction(BaseAction):
    """点击动作"""
    action: ActionType = ActionType.CLICK


@dataclass
class FillAction(BaseAction):
    """填充动作"""
    action: ActionType = ActionType.FILL
    text: str = ""


@dataclass
class WaitAction(BaseAction):
    """等待动作"""
    action: ActionType = ActionType.WAIT
    wait_type: str = "timeout"  # timeout, selector, load
    selector: Optional[str] = None
    timeout_ms: Optional[int] = None


@dataclass
class ExtractAction(BaseAction):
    """提取动作"""
    action: ActionType = ActionType.EXTRACT
    extraction_type: str = "auto"  # auto, search_results, full_content, structured


@dataclass
class Instruction:
    """基础指令数据实体"""
    action: ActionType
    description: str = ""
    success: bool = True
    error: Optional[str] = None


@dataclass
class SingleStepInstruction(Instruction):
    """单步指令数据实体"""
    action: ActionType = ActionType.NAVIGATE
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: Optional[int] = None


@dataclass
class MultiStepInstruction(Instruction):
    """多步指令数据实体"""
    steps: List[BaseAction] = field(default_factory=list)
    current_step: int = 0


@dataclass
class InstructionContext:
    """指令上下文数据实体"""
    user_text: str
    page_data: Dict[str, Any] = field(default_factory=dict)
    session_state: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)