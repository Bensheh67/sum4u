# 音频/视频总结工具 - API密钥配置指南

## 概述

本项目现已支持用户自定义API密钥，并且这些配置会被持久化保存，无需每次启动都重新配置。

## 新增功能

### 1. 配置管理系统
- 自动创建 `config.json` 配置文件
- 支持多种AI服务提供商（DeepSeek、OpenAI、Anthropic）
- 配置信息持久化保存

### 2. 交互式配置向导
- 运行 `python3 setup_api_keys.py` 启动配置向导
- 也可以使用 `python3 src/main.py --setup-api`

### 3. 启动脚本改进
- `start.sh` - 视频处理脚本
- `start_audio.sh` - 音频处理脚本
- `start_webui.sh` - Web界面启动脚本

所有启动脚本都会在启动时检查配置，并在首次运行或未配置API密钥时提示用户进行配置。

### 4. Web界面API配置
- Web界面中新增"API配置"标签页
- 可以直接在网页上设置和管理API密钥
- 保存的配置会持久化到 `config.json`

## 配置文件结构

```json
{
  "api_keys": {
    "deepseek": "your-api-key",
    "openai": "your-api-key",
    "anthropic": "your-api-key"
  },
  "default_model": "deepseek-chat",
  "default_language": "auto",
  "output_settings": {
    "transcription_folder": "transcriptions",
    "summary_folder": "summaries",
    "download_folder": "downloads"
  }
}
```

## 使用方法

### 命令行方式
```bash
# 设置API密钥
python3 setup_api_keys.py

# 使用配置好的密钥处理视频
./start.sh "https://www.youtube.com/watch?v=..."

# 处理本地音频
./start_audio.sh "/path/to/audio.mp3"

# 或直接使用Python
python3 src/main.py --url "视频链接" --prompt_template "youtube_视频总结"
```

### Web界面方式
```bash
./start_webui.sh
```
然后访问 http://localhost:8000，可以在"API配置"标签页中设置API密钥。

## 配置验证

系统会在以下情况检查配置：
- 启动脚本运行时
- Web界面启动时
- 使用API服务时

## 安全说明

- API密钥只在本地存储
- 配置文件默认被添加到 `.gitignore` 中
- 建议定期更换API密钥
- 不要在共享设备上使用生产环境的API密钥