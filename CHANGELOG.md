# 变更日志 (Changelog)

所有值得注意的变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 标准，并使用 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [v1.1.0] - 2026-02-10

### 新增功能
- **抖音/TikTok分享链接支持**: 添加了对抖音分享链接（如"6.39 03/26 14:06 [抖音] https://..."）的处理功能
- **TikHub API集成**: 集成TikHub API用于处理抖音和TikTok视频，支持无水印下载
- **URL清理功能**: 实现智能URL清理，从分享文本中提取纯净的视频链接
- **平台检测增强**: 扩展平台检测功能，支持抖音和TikTok平台识别
- **WebUI更新**: 更新Web界面，支持分享链接输入和TikHub API配置
- **批量处理支持**: 添加批量处理抖音/TikTok视频的功能

### 变更
- **API端点更新**: 使用TikHub API端点 `/api/v1/douyin/app/v3/fetch_one_video_by_share_url`
- **输入验证**: 将WebUI输入类型从 `type="url"` 改为 `type="text"`，支持分享链接格式
- **模块重构**: 创建独立的 `douyin_handler.py` 模块处理抖音/TikTok功能
- **配置更新**: 添加TikHub API密钥配置选项

### 修复
- **分享链接处理**: 修复无法处理抖音分享链接的问题
- **URL验证**: 修复前端URL验证阻止分享链接输入的问题
- **API调用**: 修复API端点拼写和参数传递问题

## [v1.0.0] - 2026-02-06

### 新增功能
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
- **Docker支持**: 一键部署，无需复杂环境配置

[Unreleased]: https://github.com/your-repo/compare/v1.1.0...HEAD
[v1.1.0]: https://github.com/your-repo/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/your-repo/releases/tag/v1.0.0