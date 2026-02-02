#!/bin/bash

# 启动Web UI的脚本
# 用于Qwen技能系统
# 使用方法: bash ~/.qwen/skills/audio-video-summarizer/scripts/start_webui_modified.sh

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 启动音频/视频总结工具 Web UI"
echo "================================"

# 检查是否已安装uv
if ! command -v uv &> /dev/null; then
    echo "📦 未检测到 uv，正在安装..."
    pip install uv
fi

# 检查虚拟环境
VENV_PATH="$HOME/.qwen/skills/audio-video-summarizer/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    uv venv "$VENV_PATH"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source "$VENV_PATH/bin/activate"

# 检查并安装依赖
echo "📦 检查并安装依赖包..."
uv pip install -r "$SCRIPT_DIR/requirements.txt"

# 检查是否已安装yt-dlp
if ! python -c "import yt_dlp" &> /dev/null; then
    echo "📦 安装 yt-dlp..."
    pip install yt-dlp
fi

# 检查是否已安装ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  未检测到 ffmpeg，请手动安装:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
    echo "   Windows: choco install ffmpeg"
fi

# 创建必要的文件夹
echo "📁 创建输出文件夹..."
mkdir -p "$HOME/downloads" "$HOME/summaries" "$HOME/transcriptions" "$HOME/uploads"

# 启动FastAPI服务器
echo "🌐 启动Web服务器..."
echo "访问地址: http://localhost:8000"
python3 -m uvicorn "$SCRIPT_DIR/src.webui":app --host 0.0.0.0 --port 8000