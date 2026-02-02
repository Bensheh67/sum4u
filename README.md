# 音频/视频总结工具 (Audio/Video Summarizer)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/OpenAI-Whisper-green?logo=openai" alt="OpenAI Whisper">
  <img src="https://img.shields.io/badge/FastAPI-WebUI-orange?logo=fastapi" alt="FastAPI WebUI">
  <img src="https://img.shields.io/badge/MIT-License-yellow" alt="License">
</p>

一个强大的Python命令行工具及Web界面，用于自动处理视频和本地音频文件、转录音频内容并生成结构化总结。

## ✨ 特性

- **多平台支持**: 支持YouTube、Bilibili等平台视频下载
- **本地音频处理**: 支持多种音频格式（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等）
- **智能音频提取**: 自动提取视频音频并转换为MP3格式
- **高质量转录**: 使用OpenAI Whisper进行本地音频转录，支持99种语言自动检测
- **AI智能总结**: 使用多种AI模型生成结构化总结
- **灵活提示词**: 支持预设模板和自定义提示词
- **自动文件管理**: 智能命名和保存结果文件
- **中文友好**: 完全支持中文界面和内容处理
- **Web界面支持**: 提供直观的Web界面进行操作
- **批量处理**: 支持批量处理多个音频文件
- **实时进度监控**: 提供处理进度可视化

## 🚀 快速开始

### 系统要求

- Python 3.8+
- macOS/Linux/Windows
- 足够的磁盘空间用于音频文件存储
- FFmpeg（用于音频处理）

### 安装

1. **克隆项目**：
   ```bash
   git clone <项目地址>
   cd 音频视频总结工具
   ```

2. **使用uv管理依赖（推荐）**：
   ```bash
   # 安装 uv
   pip install uv

   # 创建虚拟环境并安装依赖
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # 或者在Windows上: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **安装额外工具**：
   ```bash
   # 安装 yt-dlp (用于视频下载)
   pip install yt-dlp

   # 安装 ffmpeg (用于音频处理)
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg

   # Windows (使用Chocolatey)
   choco install ffmpeg
   ```

## 💡 使用方法

### 1. 命令行使用

**处理视频**：
```bash
# 使用预设模板
python3 src/main.py --url "视频URL" --prompt_template "youtube_结构化提取"

# 使用自定义提示词
python3 src/main.py --url "视频URL" --prompt "请总结主要观点和关键数据"

# 处理本地音频文件
python3 src/main.py --audio-file "/path/to/audio.mp3" --prompt_template "default课堂笔记"
```

**批量处理**：
```bash
# 批量处理上传文件夹中的所有音频文件
python3 src/main.py --batch --upload-dir "uploads" --model "small" --prompt_template "default课堂笔记"
```

### 2. 快速启动脚本

**处理视频**：
```bash
./start.sh "视频URL"
```

**处理本地音频文件**：
```bash
./start_audio.sh "音频文件路径"
```

**批量处理**：
```bash
./batch_process.sh
```

### 3. Web界面使用（推荐）

启动Web界面，支持视频URL处理、本地音频上传、批量处理等功能：

```bash
./start_webui.sh
```

启动后访问 `http://localhost:8000` 即可使用Web界面。

Web界面功能包括：
- 视频URL处理
- 本地音频文件上传
- 批量处理
- 实时进度监控
- 结果下载
- 任务历史记录

## ⚙️ 配置选项

### Whisper模型选项

- `tiny`: 最快但准确性最低 (约32x实时速度)
- `base`: 快速且准确 (约16x实时速度)
- `small`: 平衡速度和准确性 (约6x实时速度) - **默认值**
- `medium`: 较慢但更准确 (约2x实时速度)
- `large`: 最准确但最慢 (接近实时速度)
- `large-v1`, `large-v2`, `large-v3`: 大模型的不同版本

### 预设提示词模板

- `default课堂笔记`: 通用课堂笔记格式，适合大多数教学视频
- `youtube_英文笔记`: 专门用于英文视频的双语笔记格式
- `youtube_结构化提取`: 以结构化方式提取要点
- `youtube_精炼提取`: 提取核心要点和精华
- `youtube_专业课笔记`: 适用于教学视频的专业笔记格式
- `爆款短视频文案`: 适用于短视频内容的文案风格
- `youtube_视频总结`: 综合性视频总结模板

## 📁 输出文件

处理结果保存在以下目录：

- `downloads/` - 下载的音频文件
- `summaries/` - 生成的总结文件 (Markdown格式)
- `transcriptions/` - 转录文本文件
- `reports/` - 批量处理报告
- `uploads/` - 批量处理的上传文件夹

## 🛠️ 开发

### 项目结构

```
音频视频总结工具/
├── src/
│   ├── main.py          # 主程序入口
│   ├── audio.py         # 音频下载和提取模块
│   ├── transcribe.py    # 音频转录模块
│   ├── summarize.py     # 文本摘要模块
│   ├── prompts.py       # 提示词模板
│   ├── audio_handler.py # 音频处理辅助函数
│   ├── batch_processor.py # 批量处理模块
│   ├── utils.py         # 工具函数模块
│   └── webui.py         # Web界面后端
├── static/              # 静态资源
├── templates/           # HTML模板
├── downloads/           # 下载的音频文件
├── summaries/           # 生成的总结文件
├── transcriptions/      # 转录文本文件
├── reports/             # 批量处理报告
├── uploads/             # 批量处理上传文件夹
├── start.sh             # 视频处理启动脚本
├── start_audio.sh       # 音频处理启动脚本
├── start_webui.sh       # Web界面启动脚本
├── batch_process.sh     # 批量处理启动脚本
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明文档
```

### 添加新提示词模板

在 `src/prompts.py` 中添加新的模板：

```python
new_template = """
# 你的模板说明
在这里定义你的提示词模板...
"""

prompt_templates = {
    # ... 现有模板 ...
    "你的模板名称": new_template,
}
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 优秀的语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能Web框架
- [moviepy](https://zulko.github.io/moviepy/) - 音视频处理库