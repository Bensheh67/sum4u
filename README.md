# 音频/视频总结工具 (Audio/Video Summarizer CLI)

一个强大的Python命令行工具，用于自动处理视频和本地音频文件、转录音频内容并生成结构化总结。

## 🚀 功能特性

- **多平台支持**: 支持YouTube和Bilibili视频下载
- **本地音频文件处理**: 支持上传本地音频文件（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等格式，包括iPhone和Android语音备忘录）
- **智能音频提取**: 自动提取视频音频并转换为MP3格式
- **高质量转录**: 使用OpenAI Whisper进行本地音频转录，支持99种语言自动检测
- **AI智能总结**: 使用多种AI模型生成结构化总结
- **灵活提示词**: 支持预设模板和自定义提示词
- **自动文件管理**: 智能命名和保存结果文件
- **中文友好**: 完全支持中文界面和内容处理

## 📋 系统要求

- Python 3.8+
- macOS/Linux/Windows
- 稳定的网络连接
- 足够的磁盘空间用于音频文件存储

## 🛠️ 安装步骤

### 1. 克隆项目
```bash
git clone <项目地址>
cd video_summarizer_cli
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 安装额外工具
```bash
# 安装 yt-dlp (用于视频下载)
pip install yt-dlp

# 安装 ffmpeg (用于音频处理)
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (下载并添加到PATH)
# 从 https://ffmpeg.org/download.html 下载
```

### 5. Whisper模型下载
首次运行时，Whisper模型会自动从OpenAI下载到本地缓存（通常在 `~/.cache/whisper/` 目录）：
- `tiny` 模型：约75MB
- `base` 模型：约142MB
- `small` 模型：约466MB（默认）
- `medium` 模型：约1.5GB
- `large` 模型：约2.9GB

如果网络较慢，可以预先下载模型：
```bash
python3 -c "import whisper; whisper.load_model('small')"
```

## 🔑 API密钥配置

本工具已内置API密钥，无需用户手动配置。

## 📖 使用方法

### 1. 使用快速启动脚本 (推荐)

为了简化操作，项目提供了启动脚本，可以交互式地选择总结模板或自定义提示词。

**处理视频:**
```bash
./start.sh "视频URL"
```

**处理本地音频文件:**
```bash
./start_audio.sh "音频文件路径"
```

脚本会自动激活虚拟环境、运行主程序，并引导您选择一个预设的总结模板或输入自定义提示词。

### 2. 使用Web UI (新功能)

项目现在支持Web界面，可以更方便地使用所有功能。

**启动Web UI:**
```bash
./start_webui.sh
```

启动后，访问 `http://localhost:8000` 即可使用Web界面，支持以下功能：
- **视频URL处理**: 输入YouTube或Bilibili视频链接进行处理
- **本地音频上传**: 上传本地音频文件进行处理
- **批量处理**: 批量处理上传文件夹中的所有音频文件
- **实时进度监控**: 查看任务处理进度
- **结果下载**: 直接下载处理结果

### 3. 直接运行主程序

您也可以直接运行 `src/main.py` 并通过参数指定总结模板或自定义提示词。

**处理视频:**
```bash
# 使用预设模板
python3 src/main.py --url "视频URL" --prompt_template "模板名称"

# 使用自定义提示词
python3 src/main.py --url "视频URL" --prompt "你的自定义提示词"

# 设置Whisper模型大小
python3 src/main.py --url "视频URL" --model "medium"
```

**处理本地音频文件:**
```bash
# 使用预设模板
python3 src/main.py --audio-file "/path/to/audio.mp3" --prompt_template "模板名称"

# 使用自定义提示词
python3 src/main.py --audio-file "/path/to/audio.mp3" --prompt "你的自定义提示词"

# 指定音频语言（可选，不指定则自动检测）
python3 src/main.py --audio-file "/path/to/audio.mp3" --prompt_template "模板名称" --language "zh"

# 设置Whisper模型大小
python3 src/main.py --audio-file "/path/to/audio.mp3" --model "medium"
```

**本地音频文件处理说明:**
- 支持的音频格式：MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR
- 音频文件将自动转换为MP3格式进行处理
- 可以指定音频语言以提高转录准确性
- 处理流程：音频验证 → 格式转换 → 转录 → AI总结

可用的Whisper模型大小：
- `tiny`: 最快但准确性最低 (约32x实时速度)
- `base`: 快速且准确 (约16x实时速度)
- `small`: 平衡速度和准确性 (约6x实时速度) - 默认值
- `medium`: 较慢但更准确 (约2x实时速度)
- `large`, `large-v1`, `large-v2`, `large-v3`: 最准确但最慢 (接近实时速度)

可用的模板名称包括：
- `default课堂笔记`: 通用课堂笔记格式，适合大多数教学视频
- `youtube_英文笔记`: 专门用于英文视频的双语笔记格式
- `youtube_结构化提取`: 以结构化方式提取要点
- `youtube_精炼提取`: 提取核心要点和精华
- `youtube_专业课笔记`: 适用于教学视频的专业笔记格式
- `爆款短视频文案`: 适用于短视频内容的文案风格
- `youtube_视频总结`: 综合性视频总结模板



## 📁 输出文件

### 文件结构
```
video_summarizer_cli/
├── downloads/           # 下载的音频文件
│   ├── youtube_output.mp3
│   └── bilibili_output.mp3
├── summaries/          # 生成的总结文件
│   ├── youtube_VIDEO_ID_TIMESTAMP_总结.md
│   └── bilibili_VIDEO_ID_TIMESTAMP_总结.md
└── transcriptions/     # 转录文本文件
    ├── youtube_VIDEO_ID_TIMESTAMP_转录.txt
    └── bilibili_VIDEO_ID_TIMESTAMP_转录.txt
```

### 文件命名规则
- **总结文件**: `平台_视频ID_时间戳_总结.md`
- **转录文件**: `平台_视频ID_时间戳_转录.txt`
- **音频文件**: `平台_output.mp3`

## 🔧 项目结构

```
video_summarizer_cli/
├── src/                  # 主要源代码
│   ├── main.py           # 主程序入口
│   ├── audio.py          # 视频音频下载和提取模块
│   ├── audio_handler.py  # 本地音频文件处理模块
│   ├── transcribe.py     # 音频转录模块
│   ├── summarize.py      # AI总结模块
│   ├── prompts.py        # 预设提示词模板
│   ├── batch_processor.py # 批量处理模块
│   └── utils.py          # 工具函数模块
├── summaries/            # 输出总结文件
├── downloads/            # 下载的音频文件
├── transcriptions/       # 转录文本文件
├── requirements.txt      # 依赖包列表
├── pyproject.toml        # 项目配置文件
├── uv.lock               # uv依赖锁定文件
├── README.md             # 项目说明文档
├── start.sh              # 视频处理快速启动脚本
├── start_audio.sh        # 音频处理快速启动脚本
└── batch_process.sh      # 批量处理启动脚本
```

**核心模块说明:**
- `audio.py`: 负责从YouTube、Bilibili等平台下载视频并提取音频
- `audio_handler.py`: 处理本地音频文件上传，支持多种格式并转换为统一的MP3格式
- `transcribe.py`: 使用Whisper模型将音频转换为文本
- `summarize.py`: 调用AI模型对转录文本进行结构化总结
- `prompts.py`: 包含多种总结模板，适用于不同场景
- `batch_processor.py`: 支持批量处理多个音频文件

## 🆕 使用uv管理与项目结构

本项目已采用 [uv](https://github.com/astral-sh/uv) 进行依赖和虚拟环境管理，推荐使用 uv 替代 pip。

### 目录结构
```
video_summarizer_cli/
├── src/                  # 主要源代码
│   ├── main.py
│   ├── audio.py
│   ├── transcribe.py
│   ├── summarize.py
│   ├── prompts.py         # 新增：存储所有提示词模板
│   ├── utils.py
├── summaries/            # 输出总结文件
├── downloads/            # 下载的音频文件
├── transcriptions/       # 转录文本文件
├── requirements.txt      # 依赖包列表
├── README.md             # 项目说明文档
└── ...
```

### uv 常用命令
```bash
# 安装 uv
pip install uv

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate    # Windows

# 安装新依赖
uv pip install 包名

# 运行主程序
python src/main.py --url "视频URL"
```

## ⚙️ 配置选项

### 转录选项
- **模型大小**: 默认使用Whisper small模型，平衡速度和准确性
- **语言检测**: 自动检测音频语言，支持99种语言
- **输出格式**: 转录结果保存为UTF-8编码的文本文件

### 总结选项
- **结构化输出**: 包含关键概念、主要观点、实用建议等部分
- **多语言支持**: 根据转录内容自动选择总结语言
- **Markdown格式**: 便于阅读和分享

## 🐛 常见问题

### Q: 下载失败怎么办？
A: 
- 检查网络连接
- 确认视频URL有效
- 某些视频可能需要登录，尝试使用浏览器cookies

### Q: 转录速度慢？
A: 
- Whisper small模型需要一定处理时间
- 长视频处理时间更长，请耐心等待
- 确保有足够的CPU资源

### Q: API调用失败？
A: 
- 检查API密钥是否正确
- 确认API账户有足够余额
- 检查网络连接是否正常

### Q: 音频文件损坏？
A:
- 确保ffmpeg正确安装
- 检查磁盘空间是否充足
- 重新下载视频

### Q: 本地音频文件处理失败？
A:
- 确认音频格式支持（MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR）
- 检查文件路径是否正确
- 确保文件没有损坏或加密保护
- 确认文件大小，过大的文件可能需要更多处理时间

### Q: 上传的音频文件如何处理？
A:
- 程序会自动验证音频格式
- 将音频文件复制到downloads目录
- 自动转换为MP3格式（如需要）
- 然后进行转录和总结处理

## 📝 使用建议

1. **选择合适的API**: DeepSeek API通常更稳定且价格更优惠
2. **批量处理**: 可以编写脚本批量处理多个视频或音频文件
3. **定期清理**: 定期清理downloads文件夹中的音频文件，特别是处理大文件后
4. **备份重要总结**: 重要的总结文件建议备份到其他位置
5. **音频文件处理**:
   - 本地音频文件支持MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR等格式
   - 大文件（>100MB）会自动分段处理，可能需要较长时间
   - 建议使用高质量音频以获得更好的转录效果
6. **Whisper模型选择**:
   - `tiny`或`base`: 适合快速处理和测试
   - `small`: 平衡速度和准确性，推荐日常使用
   - `medium`或`large`: 适合对准确性要求高的场景

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 优秀的语音识别模型
- [DeepSeek](https://platform.deepseek.com/) - 提供AI总结服务
- [OpenAI](https://openai.com/) - 提供GPT API服务

---

**注意**: 请遵守相关平台的使用条款和版权法律，仅用于个人学习和研究目的。