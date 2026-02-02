#!/bin/bash

# 启动Web UI的脚本
# 使用方法: ./start_webui.sh

echo "🚀 启动音频/视频总结工具 Web UI"
echo "================================"

# 检查配置文件是否存在
if [ ! -f "config.json" ]; then
    echo "📝 检测到首次运行，正在创建默认配置文件..."
    python3 -c "from src.config import initialize_config; initialize_config()"
    echo "💡 请运行以下命令设置您的API密钥:"
    echo "   python3 setup_api_keys.py"
    read -p "是否现在运行配置向导？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 setup_api_keys.py
    fi
else
    # 检查API密钥是否已配置
    deepseek_key=$(python3 -c "import json; c=json.load(open('config.json')); print(c['api_keys']['deepseek'] != '')" 2>/dev/null)
    if [ "$deepseek_key" = "False" ]; then
        echo "⚠️  检测到API密钥未配置"
        echo "💡 提示：您可以运行 python3 setup_api_keys.py 来配置API密钥"
        read -p "是否现在运行配置向导？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 setup_api_keys.py
        fi
    fi
fi

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