#!/bin/bash

# 批量音频处理脚本
# 用于Qwen技能系统
# 用于处理上传文件夹中的所有音频文件

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 批量音频处理工具"
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
mkdir -p "$HOME/downloads" "$HOME/summaries" "$HOME/transcriptions" "$HOME/reports" "$HOME/uploads"

echo ""
echo "⚙️  批量处理设置"

# 询问用户上传目录（默认为uploads）
read -p "请输入上传目录路径 (直接回车使用默认uploads): " UPLOAD_DIR
if [ -z "$UPLOAD_DIR" ]; then
    UPLOAD_DIR="$HOME/uploads"
fi

# 检查上传目录是否存在
if [ ! -d "$UPLOAD_DIR" ]; then
    echo "❌ 上传目录不存在: $UPLOAD_DIR"
    echo "正在创建目录..."
    mkdir -p "$UPLOAD_DIR"
fi

# 询问用户是否需要设置Whisper模型大小
echo ""
echo "⚙️  Whisper模型设置"
echo "可用模型: tiny, base, small (默认), medium, large, large-v1, large-v2, large-v3"
read -p "请输入Whisper模型大小 (直接回车使用默认small): " MODEL_SIZE

# 如果用户没有输入，则使用默认值
if [ -z "$MODEL_SIZE" ]; then
    MODEL_SIZE="small"
fi

# 询问用户是否需要指定音频语言
echo ""
read -p "请输入音频语言代码 (如 zh, en，直接回车自动检测): " LANGUAGE

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
echo "📁 上传目录: $UPLOAD_DIR"
echo "⚙️  Whisper模型: $MODEL_SIZE"
if [ -n "$LANGUAGE" ]; then
    echo "🌐 音频语言: $LANGUAGE"
fi

# 显示上传目录中的音频文件
echo ""
echo "🎵 检查上传目录中的音频文件..."
AUDIO_FILES=$(find "$UPLOAD_DIR" -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.mp4" -o -iname "*.aac" -o -iname "*.flac" -o -iname "*.wma" -o -iname "*.amr" \) | wc -l)
echo "找到 $AUDIO_FILES 个音频文件"

if [ "$AUDIO_FILES" -eq 0 ]; then
    echo "⚠️  上传目录中没有找到音频文件"
    echo "请将音频文件放入 $UPLOAD_DIR 目录后重新运行脚本"
    exit 1
fi

echo ""
read -p "确认开始批量处理? (y/N): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "❌ 批量处理已取消"
    exit 0
fi

echo ""
echo "🚀 开始批量处理 (模型: $MODEL_SIZE)..."
echo "================================"
echo "💡 提示: 批量处理可能需要较长时间，请耐心等待..."
echo ""

if [ "$TEMPLATE_IDX" -eq 0 ]; then
    # 用户选择了自定义提示词
    read -p "请输入自定义提示词：" CUSTOM_PROMPT
    echo ""
    if [ -z "$CUSTOM_PROMPT" ]; then
        echo "⚠️  您没有输入自定义提示词，将使用默认模板"
        if [ -n "$LANGUAGE" ]; then
            python3 "$SCRIPT_DIR/src/main.py" --batch --upload-dir "$UPLOAD_DIR" --model "$MODEL_SIZE" --language "$LANGUAGE"
        else
            python3 "$SCRIPT_DIR/src/main.py" --batch --upload-dir "$UPLOAD_DIR" --model "$MODEL_SIZE"
        fi
    else
        echo "📝 使用自定义提示词: $CUSTOM_PROMPT"
        if [ -n "$LANGUAGE" ]; then
            python3 "$SCRIPT_DIR/src/main.py" --batch --upload-dir "$UPLOAD_DIR" --model "$MODEL_SIZE" --prompt "$CUSTOM_PROMPT" --language "$LANGUAGE"
        else
            python3 "$SCRIPT_DIR/src/main.py" --batch --upload-dir "$UPLOAD_DIR" --model "$MODEL_SIZE" --prompt "$CUSTOM_PROMPT"
        fi
    fi
else
    # 用户选择了预设模板
    TEMPLATE_INDEX=$((TEMPLATE_IDX-1))
    TEMPLATE_NAME="${TEMPLATES[$TEMPLATE_INDEX]}"
    echo "📝 使用模板: $TEMPLATE_NAME"
    if [ -n "$LANGUAGE" ]; then
        python3 "$SCRIPT_DIR/src/main.py" --batch --upload-dir "$UPLOAD_DIR" --model "$MODEL_SIZE" --prompt_template "$TEMPLATE_NAME" --language "$LANGUAGE"
    else
        python3 "$SCRIPT_DIR/src/main.py" --batch --upload-dir "$UPLOAD_DIR" --model "$MODEL_SIZE" --prompt_template "$TEMPLATE_NAME"
    fi
fi

echo ""
echo "================================"
echo "✅ 批量处理完成！"
echo "📁 请查看以下文件夹获取结果："
echo "   - ~/summaries/: 总结文件"
echo "   - ~/transcriptions/: 转录文件"
echo "   - ~/reports/: 批量处理报告"
echo ""
echo "💡 小贴士:"
echo "   - 检查 ~/reports/ 文件夹中的处理报告"
echo "   - 如果处理失败，检查错误信息并重试"
echo "   - 可随时向 ~/uploads/ 文件夹添加新文件并重新运行此脚本"