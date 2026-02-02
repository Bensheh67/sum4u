# 音频/视频AI总结技能

## 技能概述
一个强大的音频/视频内容分析技能，能够自动处理视频和本地音频文件、转录音频内容并生成结构化总结。

## 核心能力
- **多平台视频下载**: 支持YouTube、Bilibili等平台视频下载
- **本地音频处理**: 支持多种音频格式（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等）
- **智能音频提取**: 自动提取视频音频并转换为MP3格式
- **高质量转录**: 使用OpenAI Whisper进行本地音频转录，支持99种语言自动检测
- **AI智能总结**: 使用多种AI模型生成结构化总结
- **灵活提示词**: 支持预设模板和自定义提示词
- **Web界面支持**: 提供直观的Web界面进行操作
- **批量处理**: 支持批量处理多个音频文件

## 使用场景
- 学生整理课堂录像或讲座内容
- 研究人员快速获取视频内容要点
- 内容创作者分析竞品视频
- 企业培训内容整理
- 会议记录转录和总结

## 技能接口

### 主要功能
1. `process_video(url, options)` - 处理视频URL
2. `process_audio(file_path, options)` - 处理本地音频文件
3. `batch_process(directory, options)` - 批量处理音频文件
4. `start_web_interface()` - 启动Web界面

### 选项参数
- `model`: Whisper模型大小（tiny, base, small, medium, large）
- `prompt_template`: 预设提示词模板
- `custom_prompt`: 自定义提示词
- `language`: 指定音频语言

## 预设模板
- `default课堂笔记`: 通用课堂笔记格式
- `youtube_英文笔记`: 英文视频双语笔记格式
- `youtube_结构化提取`: 结构化提取要点
- `youtube_精炼提取`: 提取核心要点和精华
- `youtube_专业课笔记`: 专业课程笔记格式
- `爆款短视频文案`: 短视频内容文案风格
- `youtube_视频总结`: 综合性视频总结模板

## 系统要求
- Python 3.8+
- FFmpeg
- 足够的磁盘空间和内存

## 安装方式
通过pip安装或从GitHub克隆项目

## 输出格式
- 转录文本（.txt）
- 结构化总结（.md）
- 批量处理报告（.json/.txt）