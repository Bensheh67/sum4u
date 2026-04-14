#!/bin/bash

# 音频/视频总结工具 - Web UI 快速启动脚本
# 使用方法：./start_webui.sh

set -e

echo "🚀 启动音频/视频总结工具 Web UI"
echo "=================================="

# 获取脚本所在目录作为项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 未找到虚拟环境 (.venv)"
    echo "💡 请先运行以下命令创建虚拟环境并安装依赖:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖是否已安装
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

# 创建必要的输出目录
echo "📁 检查输出目录..."
mkdir -p downloads summaries transcriptions uploads

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "📝 检测到首次运行，正在创建配置文件..."
    python -c "
import json
config = {
    'api_keys': {
        'deepseek': '',
        'openai': '',
        'tikhub': ''
    }
}
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ 配置文件已创建：config.json')
print('💡 请编辑 config.json 添加您的 API 密钥')
"
fi

# 启动 FastAPI 服务器
echo ""
echo "🌐 启动 Web 服务器..."
echo "=================================="
echo "访问地址：http://localhost:8001"
echo "按 Ctrl+C 停止服务器"
echo "=================================="
echo ""

python -c "import uvicorn; from src.webui import app; uvicorn.run(app, host='0.0.0.0', port=8001)"
