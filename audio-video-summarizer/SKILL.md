---
name: audio-video-summarizer
description: A powerful audio/video content analysis tool that automatically processes videos and local audio files, transcribes audio content, and generates structured summaries. Use when users need to extract insights from audio/video content, create lecture notes from educational videos, summarize meeting recordings, or convert multimedia content into text format.
---

# 音频/视频 AI 总结技能

## 概述

这是一个强大的音频/视频内容分析技能，能够自动处理视频和本地音频文件、转录音频内容并生成结构化总结。该技能支持多种输入格式、预设模板和 Web 界面操作，适用于学生、研究人员、内容创作者和企业用户。

## 核心功能

### 1. 视频处理
- 支持 YouTube、Bilibili、抖音、TikTok 等平台视频下载
- 自动提取视频音频并转换为 MP3 格式
- 智能平台识别和路由
- 支持抖音/TikTok 分享链接直接处理

### 2. 音频处理
- 支持多种音频格式（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR 等）
- 本地音频文件上传处理
- 音频格式自动转换

### 3. 音频转录
- 使用 OpenAI Whisper 进行本地音频转录
- 支持 99 种语言自动检测
- 支持分段转录大文件

### 4. AI 智能总结
- 使用多种 AI 模型生成结构化总结（DeepSeek、OpenAI、Anthropic）
- 支持预设模板和自定义提示词
- **防幻觉设计**：禁止 AI 编造视频标题、链接等元信息
- **直接输出内容**：禁止 AI 输出框架等待填充

### 5. 批量处理
- 支持批量处理多个音频文件
- 自动生成处理报告
- 实时进度监控

### 6. Web 界面操作
- 提供直观的 Web 界面进行操作
- 支持视频 URL 处理、本地音频上传
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
# 处理视频 URL
python3 ~/.qwen/skills/audio-video-summarizer/scripts/src/main.py --url "视频 URL" --prompt_template "default 课堂笔记"

# 处理本地音频文件
python3 ~/.qwen/skills/audio-video-summarizer/scripts/src/main.py --audio-file "/path/to/audio.mp3" --prompt_template "default 课堂笔记"

# 批量处理
python3 ~/.qwen/skills/audio-video-summarizer/scripts/src/main.py --batch --upload-dir "~/uploads" --model "small" --prompt_template "default 课堂笔记"
```

### 使用启动脚本（推荐）

```bash
# 处理视频
bash ~/.qwen/skills/audio-video-summarizer/scripts/start.sh "视频 URL"

# 处理本地音频
bash ~/.qwen/skills/audio-video-summarizer/scripts/start_audio.sh "音频文件路径"

# 批量处理
bash ~/.qwen/skills/audio-video-summarizer/scripts/batch_process.sh
```

### Web 界面使用

```bash
bash ~/.qwen/skills/audio-video-summarizer/scripts/start_webui.sh
```

启动后访问 `http://localhost:8000` 即可使用 Web 界面。

### 实用函数

技能还提供了以下实用函数，可以直接调用：

- `process_video(url, model="small", prompt_template="default 课堂笔记")` - 处理视频 URL
- `process_audio(file_path, model="small", prompt_template="default 课堂笔记")` - 处理本地音频文件
- `batch_process(upload_dir="~/uploads", model="small", prompt_template="default 课堂笔记")` - 批量处理
- `start_web_ui(port=8000)` - 启动 Web 界面

## 配置选项

### Whisper 模型选项

- `tiny`: 最快但准确性最低 (约 32x 实时速度)
- `base`: 快速且准确 (约 16x 实时速度)
- `small`: 平衡速度和准确性 (约 6x 实时速度) - **默认值**
- `medium`: 较慢但更准确 (约 2x 实时速度)
- `large`: 最准确但最慢 (接近实时速度)
- `large-v1`, `large-v2`, `large-v3`: 大模型的不同版本

### 预设提示词模板

- `default 课堂笔记`: 通用课堂笔记格式，适合大多数教学视频
- `双语学习笔记`: 专门用于英文视频的双语笔记格式
- `结构化知识提取`: 以结构化方式提取要点
- `精炼摘要`: 提取核心要点和精华
- `专业课程笔记`: 适用于教学视频的专业笔记格式
- `短视频素材包`: 适用于短视频内容的文案风格
- `视频综合总结`: 综合性视频总结模板

## 输出文件

处理结果保存在以下目录：

- `~/downloads/` - 下载的音频文件
- `~/summaries/` - 生成的总结文件 (Markdown 格式)
- `~/transcriptions/` - 转录文本文件
- `~/reports/` - 批量处理报告
- `~/uploads/` - 批量处理的上传文件夹

## 系统要求

- Python 3.8+
- FFmpeg（用于音频处理）
- 足够的磁盘空间用于音频文件存储
- 足够的内存运行 Whisper 模型

## 自动安装依赖

技能脚本会自动安装和配置所需依赖：

1. 自动检查并安装 `uv`（如果未安装）
2. 自动创建虚拟环境
3. 自动安装 Python 依赖包
4. 自动安装 `yt-dlp`（如果需要）
5. 检查 `ffmpeg` 是否已安装

## Prompt 优化说明

本技能的 prompt 模板经过专门优化，具有以下特点：

### 1. 防幻觉指令
- 禁止 AI 编造视频标题、链接、时长等元信息
- 如果转录文本中没有提及，明确标注"未知"或"无法获取"
- 所有内容必须基于转录文本中的实际内容

### 2. 直接输出内容
- 禁止 AI 输出"Role"、"Skills"、"Workflow"等模板框架
- 禁止 AI 在开头或结尾添加解释说明
- 直接输出结构化 Markdown 内容

### 3. 示例演示
- 每个模板都提供正确和错误的输出示例
- 明确展示什么是期望的输出格式
- 帮助 AI 理解应该避免的行为

### 4. 模板边界清晰
- 每个模板有明确的使用场景
- 减少场景重叠
- 增强输出质量控制

## 故障排除

### 常见问题

1. **FFmpeg 未安装**：确保已正确安装 FFmpeg 并添加到 PATH
2. **Whisper 模型下载缓慢**：首次运行时会自动下载模型，可能需要较长时间
3. **API 密钥问题**：检查 API 密钥是否有效
4. **音频格式不支持**：确认输入文件是支持的音频格式
5. **内存不足**：使用较小的 Whisper 模型（如 tiny 或 small）
6. **总结内容与视频不符**：已优化 prompt 添加防幻觉指令，如仍有问题请检查转录文本质量

### 性能优化

- 对于快速处理，使用 `tiny` 或 `base` 模型
- 对于高质量转录，使用 `medium` 或 `large` 模型
- 对于长音频文件，考虑分段处理
- 确保有足够的磁盘空间存储中间文件

## 更新日志

### 2026-04-11
- 优化所有 prompt 模板，添加防 AI 幻觉指令
- 禁止 AI 输出框架等待填充，直接生成内容
- 同步根目录和 skill 目录的 prompts.py 文件
- 添加明确的正确/错误输出示例
