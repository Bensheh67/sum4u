# 视频总结工具使用示例

本文件提供了一些使用视频总结工具的示例，帮助您快速上手。

## 1. 基本用法

### 处理视频URL
```bash
# 使用默认模板处理YouTube视频
python src/main.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

# 使用指定模板处理B站视频
python src/main.py --url "https://www.bilibili.com/video/BV1xxx" --prompt_template "youtube_专业课笔记"

# 使用自定义提示词
python src/main.py --url "视频URL" --prompt "请总结视频的主要观点和实用建议"
```

### 处理本地音频文件
```bash
# 处理本地音频文件
python src/main.py --audio-file "/path/to/audio.mp3"

# 指定语言和模板
python src/main.py --audio-file "/path/to/audio.mp3" --language "zh" --prompt_template "default课堂笔记"
```

### 批量处理
```bash
# 批量处理上传目录中的所有音频文件
python src/main.py --batch --upload-dir "uploads"
```

## 2. 高级用法

### 使用不同的Whisper模型
```bash
# 使用medium模型（更准确但更慢）
python src/main.py --url "视频URL" --model "medium"

# 使用tiny模型（更快但准确性较低）
python src/main.py --audio-file "音频文件" --model "tiny"
```

### 自定义输出路径
```bash
# 指定自定义输出文件名
python src/main.py --url "视频URL" --output "my_custom_summary.md"
```

## 3. 启动脚本用法

### 快速处理视频
```bash
# 使用交互式启动脚本处理视频
./start.sh "视频URL"
```

### 快速处理音频
```bash
# 使用交互式启动脚本处理音频文件
./start_audio.sh "/path/to/audio.mp3"
```

### 批量处理
```bash
# 使用交互式批量处理脚本
./batch_process.sh
```

## 4. 可用的提示词模板

- `default课堂笔记`: 通用课堂笔记格式，适合大多数教学视频
- `youtube_英文笔记`: 专门用于英文视频的双语笔记格式
- `youtube_结构化提取`: 以结构化方式提取要点
- `youtube_精炼提取`: 提取核心要点和精华
- `youtube_专业课笔记`: 适用于教学视频的专业笔记格式
- `爆款短视频文案`: 适用于短视频内容的文案风格
- `youtube_视频总结`: 综合性视频总结模板

## 5. 常见问题

### Q: 处理长视频时出现内存不足错误怎么办？
A: 程序会自动将长音频分段处理，通常不会出现内存问题。如果仍有问题，请尝试使用更小的Whisper模型。

### Q: 如何提高转录准确性？
A: 使用较大的Whisper模型（如medium或large），但处理时间会相应增加。

### Q: 可以处理哪些音频格式？
A: 支持MP3、WAV、M4A、MP4、AAC、FLAC、WMA、AMR等常见音频格式。

## 6. 项目结构说明

```
video_summarizer_cli/
├── src/                  # 源代码目录
│   ├── main.py          # 主程序入口
│   ├── audio.py         # 视频音频下载和提取
│   ├── audio_handler.py # 本地音频文件处理
│   ├── transcribe.py    # 音频转录模块
│   ├── summarize.py     # AI总结模块
│   ├── prompts.py       # 提示词模板
│   └── utils.py         # 工具函数
├── test/                # 测试文件目录
├── downloads/           # 下载的音频文件
├── summaries/           # 生成的总结文件
├── transcriptions/      # 转录文本文件
├── reports/             # 批量处理报告
├── uploads/             # 批量处理上传目录
├── requirements.txt     # 依赖包列表
├── pyproject.toml       # 项目配置
├── README.md           # 项目说明
├── start.sh            # 视频处理启动脚本
├── start_audio.sh      # 音频处理启动脚本
└── batch_process.sh    # 批量处理启动脚本
```

希望这些示例能帮助您更好地使用视频总结工具！