#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
状态管理器

负责管理程序会话状态的键值存储，并支持持久化到文件。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.common.logger import get_logger


class StateManager:
    """简单的内存态管理与持久化实现"""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self._logger = get_logger()
        self._state: Dict[str, Any] = dict(initial_state or {})

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def delete_state(self, key: str) -> None:
        if key in self._state:
            del self._state[key]

    def clear_state(self) -> None:
        self._state.clear()

    def save_state(self, file_path: str) -> None:
        try:
            path = Path(file_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
            self._logger.info(f"会话状态已保存到 {file_path}")
        except Exception as exc:
            self._logger.error(f"保存会话状态失败: {exc}")
            raise

    def load_state(self, file_path: str) -> None:
        try:
            path = Path(file_path)
            if not path.exists():
                self._logger.warning(f"状态文件不存在，跳过加载: {file_path}")
                return
            with path.open("r", encoding="utf-8") as f:
                self._state = json.load(f)
            self._logger.info(f"会话状态已从 {file_path} 加载")
        except Exception as exc:
            self._logger.error(f"加载会话状态失败: {exc}")
            raise

    @property
    def data(self) -> Dict[str, Any]:
        return self._state


