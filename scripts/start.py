#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动脚本

用于快速启动AI浏览器代理。
"""

import argparse
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import main


if __name__ == "__main__":
    main()