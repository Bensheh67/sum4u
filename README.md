# 音频/视频总结工具 (Audio/Video Summarizer)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/OpenAI-Whisper-green?logo=openai" alt="OpenAI Whisper">
  <img src="https://img.shields.io/badge/FastAPI-WebUI-orange?logo=fastapi" alt="FastAPI WebUI">
  <img src="https://img.shields.io/badge/MIT-License-yellow" alt="License">
</p>
1. 一个强大的Python命令行工具及Web界面，用于自动处理视频和本地音频文件、转录音频内容并生成结构化总结。
2. /skill 符合claude skill规范，可以直接使用
<img width="1028" height="870" alt="截屏首页" src="https://github.com/Bensheh67/sum4u/blob/main/%E6%88%AA%E5%B1%8F2026-05-23%2022.56.25.png" />
## ✨ 特性

- **多平台支持**: 支持YouTube、Bilibili、抖音、TikTok等平台视频下载
- **本地音频处理**: 支持多种音频格式（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等）
- **智能音频提取**: 自动提取视频音频并转换为MP3格式
- **高质量转录**: 使用OpenAI Whisper进行本地音频转录，支持99种语言自动检测
- **AI智能总结**: 使用多种AI模型生成结构化总结
- **视频截图功能**: AI智能分析视频内容，自动选择关键帧插入总结（可选）
- **灵活提示词**: 支持预设模板和自定义提示词
- **自动文件管理**: 智能命名和保存结果文件
- **中文友好**: 完全支持中文界面和内容处理
- **Web界面支持**: 提供直观的Web界面进行操作
- **批量处理**: 支持批量处理多个音频文件
- **实时进度监控**: 提供处理进度可视化
- **抖音/TikTok分享链接支持**: 直接粘贴抖音分享链接（如"6.39 03/26 14:06 [抖音] https://..."）即可处理
- **TikHub API集成**: 使用专业的抖音/TikTok数据API，支持无水印视频下载

## 🆕 最新更新 (2026-05-23)

- **视频类型自动分类器**: 新增智能分类器，根据视频标题/描述自动判断类型（学习/教程/评测/访谈），选择最优总结模板
- **模板增强**: 重写所有提示词模板，10个优化模板覆盖更多场景，结构更清晰、条理性更强
- **下载稳定性修复**: 解决YouTube视频下载挂起问题，添加300秒超时保护

## 📝 What's Changed

> 2026 年 5 月

### Features
- **MiniMax API 集成**: AI 摘要新增 MiniMax 作为备用提供商，支持 DeepSeek / MiniMax 切换
- **Obsidian 一键导入**: WebUI 增加「导入 Obsidian」按钮，将总结以原生格式写入 vault，支持 YAML frontmatter 元数据
- **取消任务功能**: URL 处理页面增加取消任务按钮，支持中断正在执行的任务
- **实时进度百分比**: 进度条实时显示当前处理阶段的百分比数值

### Fixes
- **修复 API Key 保存**: save_api_config/get_api_config 漏掉 minimax provider 导致 Key 无法保存
- **修复 task_history 未定义**: 变量初始化位置错误导致 NameError
- **修复 Obsidian 路径验证**: save_obsidian_config 增加路径有效性检查
- **CI 测试收集失败**: .gitignore 规则误排除了 tests/test_*.py 文件

### Chores
- **CI workflow 优化**: 合并依赖安装、使用 pip cache、清理冗余步骤
- **设计系统应用**: 字体 16px、Header 按钮 44px、移动端 toggle 重叠修复

## 🚀 快速开始

### 系统要求

- **Python方式**:
  - Python 3.8+
  - macOS/Linux/Windows
  - 足够的磁盘空间用于音频文件存储
  - FFmpeg（用于音频处理）
  - TikHub API密钥（用于处理抖音/TikTok视频）

### 安装方式

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

# 生成带视频截图的总结（AI自动选择关键帧）
python3 src/main.py --url "视频URL" --with-screenshots
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

```bash
# 启动 Web UI
./start_webui.sh

# 或直接运行
python -m src.webui
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
- 视频截图功能（可选，开启后AI自动选择关键帧）

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

### 带截图的输出结构
当使用 `--with-screenshots` 选项时，输出为文件夹格式：
```
summaries/
└── {视频名}_{日期时间}_总结/
    ├── summary.md              # 包含截图引用的总结
    └── screenshots/
        ├── frame_001_013000.jpg  # 时间戳: 00:13:00
        ├── frame_002_025400.jpg
        └── ...
```

## 🛠️ 开发

### 项目结构

```
音频视频总结工具/
├── src/                    # 源代码目录
│   ├── main.py            # 主程序入口
│   ├── audio.py           # 音频下载和提取模块
│   ├── video.py           # 视频帧提取模块（截图功能）
│   ├── keyframe_selector.py # AI关键帧选择模块
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
├── start.sh               # 视频处理启动脚本
├── start_audio.sh         # 音频处理启动脚本
├── start_webui.sh         # Web界面启动脚本
├── batch_process.sh       # 批量处理启动脚本
├── requirements.txt       # 依赖包列表
└── README.md              # 项目说明文档
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
