# 音频/视频总结工具 (Audio/Video Summarizer SHELL)

一个强大的Python命令行工具，用于自动处理视频和本地音频文件、转录音频内容并生成结构化总结。

## 🚀 功能特性

- **多平台支持**: 支持YouTube和Bilibili视频下载
- **本地音频文件处理**: 支持上传本地音频文件（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等格式）
- **智能音频提取**: 自动提取视频音频并转换为MP3格式
- **高质量转录**: 使用OpenAI Whisper进行本地音频转录，支持99种语言自动检测
- **AI智能总结**: 使用多种AI模型生成结构化总结
- **灵活提示词**: 支持预设模板和自定义提示词
- **自动文件管理**: 智能命名和保存结果文件
- **中文友好**: 完全支持中文界面和内容处理
- **Web界面支持**: 提供直观的Web界面进行操作
- **批量处理**: 支持批量处理多个音频文件

## 🛠️ 安装与配置

### 系统要求
- Python 3.8+
- macOS/Linux/Windows
- 足够的磁盘空间用于音频文件存储

### 安装步骤
1. 克隆项目：
   ```bash
   git clone <项目地址>
   cd video_summarizer_cli
   ```

2. 使用uv管理依赖（推荐）：
   ```bash
   # 安装 uv
   pip install uv
   
   # 创建虚拟环境并安装依赖
   uv venv
   uv pip install -r requirements.txt
   ```

3. 安装额外工具：
   ```bash
   # 安装 yt-dlp (用于视频下载)
   pip install yt-dlp
   
   # 安装 ffmpeg (用于音频处理)
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   ```

4. 首次运行时，Whisper模型会自动从OpenAI下载到本地缓存。

## 📖 使用方法

### 1. 使用快速启动脚本 (推荐)

**处理视频:**
```bash
./start.sh "视频URL"
```

**处理本地音频文件:**
```bash
./start_audio.sh "音频文件路径"
```

### 2. 使用Web UI (新功能)

启动Web界面，支持视频URL处理、本地音频上传、批量处理等功能：
```bash
./start_webui.sh
```

启动后访问 `http://localhost:8000` 即可使用Web界面。

### 3. 直接运行主程序

```bash
# 处理视频
python3 src/main.py --url "视频URL" --prompt_template "模板名称"

# 处理本地音频文件
python3 src/main.py --audio-file "/path/to/audio.mp3" --prompt_template "模板名称"
```

## 🔧 配置选项

- **Whisper模型**: tiny, base, small (默认), medium, large
- **语言检测**: 自动检测或手动指定
- **提示词模板**: 包含多种预设模板，支持自定义

## 📁 输出文件

处理结果保存在以下目录：
- `downloads/` - 下载的音频文件
- `summaries/` - 生成的总结文件
- `transcriptions/` - 转录文本文件
- `reports/` - 批量处理报告

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 优秀的语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能Web框架