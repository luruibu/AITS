#!/bin/bash

echo "🚀 启动 AI Image Tree System..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    echo "💡 请先安装 Python 3.8+"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "⚠️ 配置文件不存在，运行安装脚本..."
    python3 setup.py
    if [ $? -ne 0 ]; then
        echo "❌ 安装失败"
        exit 1
    fi
fi

# 启动应用
echo "✅ 启动应用..."
python3 app.py