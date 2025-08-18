#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全校验器

负责对进入执行层的指令进行结构与安全校验，并对字符串做必要的转义与长度限制。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from src.common.config import get_config


class SafetyValidator:
    MAX_SELECTOR_LEN = 512
    MAX_VALUE_LEN = 2048

    def __init__(self, allowed_actions: List[str]):
        self.allowed_actions = set(allowed_actions or [])

    def validate_and_sanitize(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if not isinstance(instruction, dict):
            raise ValueError("指令必须为字典类型")

        # 支持多步或单步
        if "steps" in instruction:
            if not isinstance(instruction["steps"], list) or not instruction["steps"]:
                raise ValueError("多步指令的 steps 必须为非空列表")
            sanitized_steps = []
            for i, step in enumerate(instruction["steps"]):
                try:
                    sanitized_steps.append(self._validate_single(step))
                except ValueError as exc:
                    errors.append(f"第{i+1}步: {exc}")
            if errors:
                raise ValueError("; ".join(errors))
            new_instr = dict(instruction)
            new_instr["steps"] = sanitized_steps
            return new_instr
        else:
            return self._validate_single(instruction)

    def _validate_single(self, step: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(step, dict):
            raise ValueError("单步指令必须为字典类型")

        action = step.get("action")
        if action not in self.allowed_actions:
            raise ValueError(f"不支持的操作类型: {action}")

        # 必填字段
        if action in {"click", "type", "select"}:
            if "selector" not in step:
                raise ValueError(f"操作 {action} 缺少 selector")
        if action in {"navigate"}:
            if "value" not in step:
                raise ValueError("navigate 缺少 value(URL)")

        # URL 域名白名单
        if action == "navigate":
            self._validate_url(step.get("value"))

        # 文本长度限制与转义
        sanitized = dict(step)
        if "selector" in sanitized and isinstance(sanitized["selector"], str):
            sanitized["selector"] = self._escape_string(sanitized["selector"], self.MAX_SELECTOR_LEN)
        if "value" in sanitized and isinstance(sanitized["value"], str):
            sanitized["value"] = self._escape_string(sanitized["value"], self.MAX_VALUE_LEN)
        if "description" in sanitized and isinstance(sanitized["description"], str):
            sanitized["description"] = self._escape_string(sanitized["description"], 512)

        return sanitized

    def _escape_string(self, s: str, max_len: int) -> str:
        s = s[:max_len]
        # 简单转义，避免注入破坏模板中的字符串封闭
        s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        # 可选：限制危险片段
        if "import" in s or "__" in s:
            # 仅作为防御，选择器与值里一般不应出现这些
            s = s.replace("import", "").replace("__", "_")
        return s

    def _validate_url(self, url: str) -> None:
        allowed_domains = get_config("ALLOWED_DOMAINS", "*")
        if allowed_domains == "*":
            return
        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            raise ValueError("无效URL")
        parts = domain.split(".")
        main = ".".join(parts[-2:]) if len(parts) > 2 else domain
        if main not in allowed_domains:
            raise ValueError(f"域名不在白名单: {main}")


