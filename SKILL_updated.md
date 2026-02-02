---
name: audio-video-summarizer
description: A powerful audio/video content analysis skill that automatically processes videos and local audio files, transcribes audio content, and generates structured summaries. Use when users need to extract insights from audio/video content, create lecture notes from educational videos, summarize meeting recordings, or convert multimedia content into text format.
---

# 音频/视频AI总结技能

## 概述

这是一个强大的音频/视频内容分析技能，能够自动处理视频和本地音频文件、转录音频内容并生成结构化总结。该技能支持多种输入格式、预设模板和Web界面操作，适用于学生、研究人员、内容创作者和企业用户。

## 核心功能

### 1. 视频处理
- 支持YouTube、Bilibili等平台视频下载
- 自动提取视频音频并转换为MP3格式
- 智能平台识别和路由

### 2. 音频处理
- 支持多种音频格式（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等）
- 本地音频文件上传处理
- 音频格式自动转换

### 3. 音频转录
- 使用OpenAI Whisper进行本地音频转录
- 支持99种语言自动检测
- 高质量转录输出

### 4. AI智能总结
- 使用多种AI模型生成结构化总结
- 支持预设模板和自定义提示词
- 输出Markdown格式的结构化摘要

### 5. 批量处理
- 支持批量处理多个音频文件
- 自动生成处理报告
- 实时进度监控

### 6. Web界面操作
- 提供直观的Web界面进行操作
- 支持视频URL处理、本地音频上传
- 任务历史记录和结果下载

## 使用场景

### 何时使用此技能：

1. **教育场景**：
   - 学生整理课堂录像或讲座内容
   - 创建课程笔记和学习资料
   - 分析教学视频内容

2. **研究场景**：
   - 研究人员快速获取视频内容要点
   - 分析学术讲座或会议录像
   - 提取关键信息进行文献综述

3. **商业场景**：
   - 企业培训内容整理
   - 会议记录转录和总结
   - 竞品视频分析

4. **内容创作**：
   - 内容创作者分析竞品视频
   - 生成视频内容的文案素材
   - 制作短视频的灵感提取

## 快速开始

### 命令行使用

```bash
# 处理视频URL
python3 ~/.qwen/skills/audio-video-summarizer/scripts/src/main.py --url "视频URL" --prompt_template "youtube_结构化提取"

# 处理本地音频文件
python3 ~/.qwen/skills/audio-video-summarizer/scripts/src/main.py --audio-file "/path/to/audio.mp3" --prompt_template "default课堂笔记"

# 批量处理
python3 ~/.qwen/skills/audio-video-summarizer/scripts/src/main.py --batch --upload-dir "uploads" --model "small" --prompt_template "default课堂笔记"
```

### 使用启动脚本

```bash
# 处理视频
bash ~/.qwen/skills/audio-video-summarizer/scripts/start.sh "视频URL"

# 处理本地音频
bash ~/.qwen/skills/audio-video-summarizer/scripts/start_audio.sh "音频文件路径"

# 批量处理
bash ~/.qwen/skills/audio-video-summarizer/scripts/batch_process.sh
```

### Web界面使用

```bash
bash ~/.qwen/skills/audio-video-summarizer/scripts/start_webui.sh
```

启动后访问 `http://localhost:8000` 即可使用Web界面。

### 实用函数

技能还提供了以下实用函数，可以直接调用：

- `process_video(url, model="small", prompt_template="default课堂笔记")` - 处理视频URL
- `process_audio(file_path, model="small", prompt_template="default课堂笔记")` - 处理本地音频文件
- `batch_process(upload_dir="uploads", model="small", prompt_template="default课堂笔记")` - 批量处理
- `start_web_ui(port=8000)` - 启动Web界面

## 配置选项

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

## 输出文件

处理结果保存在以下目录：

- `downloads/` - 下载的音频文件
- `summaries/` - 生成的总结文件 (Markdown格式)
- `transcriptions/` - 转录文本文件
- `reports/` - 批量处理报告
- `uploads/` - 批量处理的上传文件夹

## 系统要求

- Python 3.8+
- FFmpeg（用于音频处理）
- 足够的磁盘空间用于音频文件存储
- 足够的内存运行Whisper模型

## 安装依赖

```bash
# 使用uv管理依赖（推荐）
pip install uv
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -r ~/.qwen/skills/audio-video-summarizer/scripts/requirements.txt

# 安装额外工具
pip install yt-dlp

# 安装FFmpeg
# macOS: brew install ffmpeg
# Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg
```

## 故障排除

### 常见问题

1. **FFmpeg未安装**：确保已正确安装FFmpeg并添加到PATH
2. **Whisper模型下载缓慢**：首次运行时会自动下载模型，可能需要较长时间
3. **API密钥问题**：检查API密钥是否有效
4. **音频格式不支持**：确认输入文件是支持的音频格式
5. **内存不足**：使用较小的Whisper模型（如tiny或small）

### 性能优化

- 对于快速处理，使用`tiny`或`base`模型
- 对于高质量转录，使用`medium`或`large`模型
- 对于长音频文件，考虑分段处理
- 确保有足够的磁盘空间存储中间文件