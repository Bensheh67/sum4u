# 音频/视频总结工具 (Audio/Video Summarizer)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/OpenAI-Whisper-green?logo=openai" alt="OpenAI Whisper">
  <img src="https://img.shields.io/badge/FastAPI-WebUI-orange?logo=fastapi" alt="FastAPI WebUI">
  <img src="https://img.shields.io/badge/Docker-Supported-blueviolet?logo=docker" alt="Docker Support">
  <img src="https://img.shields.io/badge/MIT-License-yellow" alt="License">
</p>
1. 一个强大的Python命令行工具及Web界面，用于自动处理视频和本地音频文件、转录音频内容并生成结构化总结。
2. /skill 符合claude skill规范，可以直接使用
<img width="1028" height="870" alt="截屏2026-02-06 13 49 01" src="https://github.com/user-attachments/assets/db0770a6-8dee-4c03-9319-553f69efd2e8" />
## ✨ 特性

- **多平台支持**: 支持YouTube、Bilibili、抖音、TikTok等平台视频下载
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
- **抖音/TikTok分享链接支持**: 直接粘贴抖音分享链接（如"6.39 03/26 14:06 [抖音] https://..."）即可处理
- **TikHub API集成**: 使用专业的抖音/TikTok数据API，支持无水印视频下载

## 🚀 快速开始

### 系统要求

- **Python方式**:
  - Python 3.8+
  - macOS/Linux/Windows
  - 足够的磁盘空间用于音频文件存储
  - FFmpeg（用于音频处理）
  - TikHub API密钥（用于处理抖音/TikTok视频）

- **Docker方式**:
  - Docker Engine 19.03+
  - 至少 4GB RAM（推荐 8GB+）
  - 至少 2GB 可用磁盘空间
  - TikHub API密钥（用于处理抖音/TikTok视频）

### 安装方式

#### 方式一：Docker部署（推荐新手）

Docker方式无需安装Python环境和各种依赖，一键即可运行完整工具。

1. **安装Docker**：
   - Windows/Mac: 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Linux: 安装 Docker Engine

2. **克隆项目**：
   ```bash
   git clone <项目地址>
   cd 音频视频总结工具
   ```

3. **启动工具**：
   ```bash
   # 给启动脚本添加执行权限
   chmod +x docker_setup_simple.sh
   
   # 启动工具（首次运行会自动构建镜像）
   ./docker_setup_simple.sh
   ```

4. **访问工具**：
   打开浏览器，访问 `http://localhost:8000`

5. **首次配置**：
   首次访问时，按照网页提示配置API密钥即可开始使用。

#### 方式二：传统Python方式

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

# 处理抖音分享链接
python3 src/main.py --url "6.39 03/26 14:06 [抖音] https://v.douyin.com/xxxxx/ 复制此链接..." --prompt_template "default课堂笔记"

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

### 3. Web界面使用

启动Web界面，支持视频URL处理、本地音频上传、批量处理等功能：

#### Docker方式（推荐新手）
```bash
# 启动工具（已在后台运行）
./docker_setup_simple.sh
```

#### 传统Python方式
```bash
./start_webui.sh
```

启动后访问 `http://localhost:8000` 即可使用Web界面。

Web界面功能包括：

- API配置（支持TikHub API密钥配置）
- 视频URL处理（支持抖音/TikTok分享链接）
- 本地音频文件上传
- 批量处理
- 实时进度监控
- 结果下载
- 任务历史记录

### 4. Docker高级操作

如果你对Docker比较熟悉，可以使用以下高级操作：

**查看容器日志**：
```bash
./docker_setup_simple.sh logs
```

**停止工具**：
```bash
./docker_setup_simple.sh stop
```

**重启工具**：
```bash
./docker_setup_simple.sh restart
```

**使用docker-compose直接操作**：
```bash
# 启动（使用简化配置）
docker-compose -f docker-compose-simple.yml up -d

# 停止
docker-compose -f docker-compose-simple.yml down

# 查看状态
docker-compose -f docker-compose-simple.yml ps
```

**手动构建镜像**：
```bash
# 使用简化版Dockerfile（构建更快）
docker build -f Dockerfile.beginner -t video-summarizer .
```

## 📁 Docker数据存储

使用Docker部署时，所有数据都保存在本地的 `data/` 目录中：

- `./data/downloads/` - 下载的视频/音频文件
- `./data/summaries/` - 生成的总结文件
- `./data/transcriptions/` - 转录文本文件
- `./data/uploads/` - 上传的文件
- `./config.json` - API密钥配置文件

这些数据卷确保即使容器重启或更新，你的处理结果也不会丢失。

## 🎬 抖音/TikTok功能使用

要使用抖音/TikTok视频处理功能：

1. **获取TikHub API密钥**：
   - 访问 https://user.tikhub.io/users/signin 注册账户
   - 在用户面板中获取您的API密钥

2. **配置API密钥**：
   - 在Web界面的"API配置"标签页中配置
   - 或在 `config.json` 文件中添加 `"tikhub": "your-tikhub-api-key"`

3. **使用功能**：
   - 支持直接粘贴抖音分享链接（如"6.39 03/26 14:06 [抖音] https://..."）
   - 支持标准抖音/TikTok URL
   - 在Docker和传统Python方式中均可用

## ⚙️ 配置选项

### API密钥配置

要使用本工具，您需要配置至少一个AI服务提供商的API密钥：

1. **交互式配置**（推荐）：
   ```bash
   python3 setup_api_keys.py
   ```

2. **手动配置**：
   编辑项目根目录的 `config.json` 文件，添加所需的API密钥。

### TikHub API密钥配置（用于抖音/TikTok功能）

要使用抖音/TikTok视频处理功能，您需要：

1. **获取TikHub API密钥**：
   - 访问 https://user.tikhub.io/users/signin 注册账户
   - 在用户面板中获取您的API密钥

2. **配置API密钥**：
   - 使用交互式配置向导：`python3 setup_api_keys.py`
   - 或手动编辑 `config.json` 文件，在 `api_keys` 部分添加 `"tikhub": "your-tikhub-api-key"`

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
- 可自行配置prompt

## 📁 输出文件

### 传统Python方式
处理结果保存在以下目录：

- `downloads/` - 下载的音频文件
- `summaries/` - 生成的总结文件 (Markdown格式)
- `transcriptions/` - 转录文本文件
- `reports/` - 批量处理报告
- `uploads/` - 批量处理的上传文件夹

### Docker方式
使用Docker部署时，所有数据都保存在本地的 `data/` 目录中：

- `./data/downloads/` - 下载的视频/音频文件
- `./data/summaries/` - 生成的总结文件
- `./data/transcriptions/` - 转录文本文件
- `./data/uploads/` - 上传的文件
- `./config.json` - API密钥配置文件

## 🛠️ 开发

### 项目结构

```
音频视频总结工具/
├── src/                    # 源代码目录
│   ├── main.py            # 主程序入口
│   ├── audio.py           # 音频下载和提取模块
│   ├── transcribe.py      # 音频转录模块
│   ├── summarize.py       # 文本摘要模块
│   ├── prompts.py         # 提示词模板
│   ├── audio_handler.py   # 音频处理辅助函数
│   ├── batch_processor.py # 批量处理模块
│   ├── utils.py           # 工具函数模块
│   ├── webui.py           # Web界面后端
│   └── douyin_handler.py  # 抖音/TikTok视频处理模块
├── static/                # 静态资源
├── templates/             # HTML模板
├── downloads/             # 下载的音频文件
├── summaries/             # 生成的总结文件
├── transcriptions/        # 转录文本文件
├── reports/               # 批量处理报告
├── uploads/               # 批量处理上传文件夹
├── data/                  # Docker数据卷目录
│   ├── downloads/         # Docker版下载的音频文件
│   ├── summaries/         # Docker版生成的总结文件
│   ├── transcriptions/    # Docker版转录文本文件
│   └── uploads/           # Docker版上传的文件
├── start.sh               # 视频处理启动脚本
├── start_audio.sh         # 音频处理启动脚本
├── start_webui.sh         # Web界面启动脚本
├── batch_process.sh       # 批量处理启动脚本
├── docker_setup_simple.sh # Docker简化部署脚本
├── Dockerfile             # 标准Docker配置文件
├── Dockerfile.beginner    # 新手友好Docker配置文件
├── Dockerfile.simple      # 简化版Docker配置文件
├── docker-compose.yml     # 标准Docker Compose配置
├── docker-compose-simple.yml # 简化版Docker Compose配置
├── requirements.txt       # 依赖包列表
└── README.md              # 项目说明文档
```

### Docker开发

项目提供了多种Docker配置以适应不同需求：

- `Dockerfile`: 标准配置，预加载Whisper模型
- `Dockerfile.simple`: 简化配置，不预加载模型，构建更快
- `Dockerfile.beginner`: 专为新手优化的配置
- `docker-compose.yml`: 标准Compose配置
- `docker-compose-simple.yml`: 简化版Compose配置，使用更直观的数据卷结构

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

## 🐳 Docker常见问题与解决方案

### 1. 启动问题

**Q: 运行 `./docker_setup_simple.sh` 时报权限错误**

A: 给脚本添加执行权限：
```bash
chmod +x docker_setup_simple.sh
```

**Q: 访问 http://localhost:8000 显示连接被拒绝**

A: 检查以下几点：
- 确认Docker服务正在运行
- 确认容器已成功启动：`docker ps`
- 查看容器日志：`./docker_setup_simple.sh logs`
- 确认端口8000未被其他程序占用

### 2. 性能问题

**Q: 处理音频文件时非常缓慢**

A: 
- 确认有足够的内存分配给Docker（至少4GB）
- 在Docker Desktop设置中增加内存分配
- 尝试使用较小的Whisper模型（如 tiny 或 base）

**Q: 出现内存不足错误**

A: 
- 在Docker Desktop设置中增加内存分配
- 关闭其他占用内存的应用程序
- 使用较小的Whisper模型

### 3. 数据存储问题

**Q: 重启容器后处理结果丢失**

A: 确认使用的是正确的Docker配置，数据应保存在 `./data/` 目录中，该目录被挂载为数据卷。

### 4. 构建问题

**Q: 构建Docker镜像时失败**

A: 
- 确认Docker守护进程正在运行
- 检查是否有足够的磁盘空间
- 尝试清理Docker构建缓存：`docker builder prune`

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 🛡️ 安全注意事项

在贡献代码时，请注意以下安全事项：

1. **绝不要提交包含真实API密钥的文件**
   - 检查 `.gitignore` 文件确保 `config.json` 和 `.env` 被忽略
   - 使用 `git status` 确认没有意外提交敏感文件
   - 在推送前使用 `git log -p --all | grep -i "sk-"` 检查是否意外提交了API密钥

2. **使用示例配置文件**
   - 修改配置时参考 `config_example.json` 而非 `config.json`
   - 在示例代码中使用占位符而非真实密钥

3. **安全最佳实践**
   - 定期轮换API密钥
   - 使用环境变量而非配置文件存储密钥（特别是在服务器环境中）

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 优秀的语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能Web框架
- [moviepy](https://zulko.github.io/moviepy/) - 音视频处理库
