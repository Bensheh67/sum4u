#!/bin/bash

# 音频/视频总结工具快速启动脚本
# 用于Qwen技能系统
# 使用方法: bash ~/.qwen/skills/audio-video-summarizer/scripts/start_modified.sh "视频URL"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎥 音频/视频总结工具快速启动"
echo "================================"

# 检查参数
if [ $# -lt 1 ]; then
    echo "❌ 错误: 请提供视频URL"
    echo "使用方法: bash ~/.qwen/skills/audio-video-summarizer/scripts/start_modified.sh \"视频URL\""
    echo ""
    echo "示例:"
    echo "  bash ~/.qwen/skills/audio-video-summarizer/scripts/start_modified.sh \"https://www.youtube.com/watch?v=VIDEO_ID\""
    echo "  bash ~/.qwen/skills/audio-video-summarizer/scripts/start_modified.sh \"https://www.bilibili.com/video/BV1xxx\""
    exit 1
fi

URL=$1

# 询问用户是否需要设置Whisper模型大小
echo ""
echo "⚙️  Whisper模型设置"
echo "可用模型: tiny, base, small (默认), medium, large, large-v1, large-v2, large-v3"
read -p "请输入Whisper模型大小 (直接回车使用默认small): " MODEL_SIZE

# 如果用户没有输入，则使用默认值
if [ -z "$MODEL_SIZE" ]; then
    MODEL_SIZE="small"
fi

# 定义可用的模板列表
TEMPLATES=("default课堂笔记" "youtube_英文笔记" "youtube_结构化提取" "youtube_精炼提取" "youtube_专业课笔记" "爆款短视频文案" "youtube_视频总结")
echo ""
echo "📋 可选的摘要模板："
for i in "${!TEMPLATES[@]}"; do
    printf "  %d. %s\n" $((i+1)) "${TEMPLATES[$i]}"
done
echo "  0. 自定义提示词"
echo ""

# 获取用户选择的模板
while true; do
    read -p "请选择模板编号（输入 1-${#TEMPLATES[@]} 或 0 表示自定义）：" TEMPLATE_IDX

    # 检查输入是否为数字
    if ! [[ "$TEMPLATE_IDX" =~ ^[0-9]+$ ]]; then
        echo "❌ 输入无效，请输入数字"
        continue
    fi

    # 检查范围
    if [ "$TEMPLATE_IDX" -ge 0 ] && [ "$TEMPLATE_IDX" -le ${#TEMPLATES[@]} ]; then
        break
    else
        echo "❌ 输入超出范围，请输入 0 到 ${#TEMPLATES[@]} 之间的数字"
    fi
done

echo ""
echo "📹 视频URL: $URL"
echo "⚙️  Whisper模型: $MODEL_SIZE"

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

# 检查依赖
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
mkdir -p "$HOME/downloads" "$HOME/summaries" "$HOME/transcriptions"

# 根据用户选择执行相应的操作
echo "🚀 开始处理视频 (模型: $MODEL_SIZE)..."
echo "================================"
echo "💡 提示: 转录过程可能需要几分钟到几十分钟，请耐心等待..."
echo ""

if [ "$TEMPLATE_IDX" -eq 0 ]; then
    # 用户选择了自定义提示词
    read -p "请输入自定义提示词：" CUSTOM_PROMPT
    echo ""
    if [ -z "$CUSTOM_PROMPT" ]; then
        echo "⚠️  您没有输入自定义提示词，将使用默认模板"
        python3 "$SCRIPT_DIR/src/main.py" --url "$URL" --model "$MODEL_SIZE" --output "$HOME/summaries/$(date +%Y%m%d_%H%M%S)_summary.md"
    else
        echo "📝 使用自定义提示词: $CUSTOM_PROMPT"
        python3 "$SCRIPT_DIR/src/main.py" --url "$URL" --model "$MODEL_SIZE" --prompt "$CUSTOM_PROMPT" --output "$HOME/summaries/$(date +%Y%m%d_%H%M%S)_summary.md"
    fi
else
    # 用户选择了预设模板
    TEMPLATE_INDEX=$((TEMPLATE_IDX-1))
    TEMPLATE_NAME="${TEMPLATES[$TEMPLATE_INDEX]}"
    echo "📝 使用模板: $TEMPLATE_NAME"
    python3 "$SCRIPT_DIR/src/main.py" --url "$URL" --model "$MODEL_SIZE" --prompt_template "$TEMPLATE_NAME" --output "$HOME/summaries/$(date +%Y%m%d_%H%M%S)_summary.md"
fi

echo ""
echo "================================"
echo "✅ 处理完成！"
echo "📁 请查看 ~/summaries/ 文件夹中的结果文件"
echo ""
echo "💡 小贴士:"
echo "   - 如果对结果不满意，可以尝试不同的模板"
echo "   - 长视频可能需要更多处理时间"
echo "   - 可以随时重新运行此脚本处理其他视频"