#!/bin/bash

# 启动Web UI的脚本
# 使用方法: ./start_webui.sh

echo "🚀 启动音频/视频总结工具 Web UI"
echo "================================"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    uv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 检查并安装依赖
echo "📦 检查并安装依赖包..."
uv pip install -r requirements.txt

# 创建必要的文件夹
echo "📁 创建输出文件夹..."
mkdir -p downloads summaries transcriptions uploads

# 启动FastAPI服务器
echo "🌐 启动Web服务器..."
echo "访问地址: http://localhost:8000"
uvicorn src.webui:app --host 0.0.0.0 --port 8000 --reload