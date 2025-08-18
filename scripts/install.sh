#!/bin/bash

# AI浏览器代理安装脚本

set -e

ECHO_PREFIX="[AI浏览器代理安装] "

echo "${ECHO_PREFIX}开始安装..."

# 检查Python版本
echo "${ECHO_PREFIX}检查Python版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "${ECHO_PREFIX}错误: 需要Python 3.8或更高版本，当前版本为 $PYTHON_VERSION"
    exit 1
fi

echo "${ECHO_PREFIX}Python版本检查通过: $PYTHON_VERSION"

# 创建虚拟环境
echo "${ECHO_PREFIX}创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境
echo "${ECHO_PREFIX}激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "${ECHO_PREFIX}安装依赖..."
pip install --upgrade pip
pip install -e .

# 安装Playwright浏览器
echo "${ECHO_PREFIX}安装Playwright浏览器..."
python -m playwright install

# 创建.env文件
if [ ! -f ".env" ]; then
    echo "${ECHO_PREFIX}创建.env文件..."
    cp .env.example .env
    echo "${ECHO_PREFIX}请编辑.env文件配置您的环境变量"
fi

echo "${ECHO_PREFIX}安装完成！"
echo "${ECHO_PREFIX}使用以下命令启动:"
echo "${ECHO_PREFIX}  命令行模式: python scripts/start.py --mode cli"
echo "${ECHO_PREFIX}  Web模式: python scripts/start.py --mode web"
echo "${ECHO_PREFIX}使用 --help 查看更多选项"