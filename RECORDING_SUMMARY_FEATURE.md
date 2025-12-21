# 录音文件课堂总结功能

本项目提供了一个强大的功能，可以将本地录音文件转换为课堂内容摘要，帮助用户快速获取课程要点。

## 功能特性

- **多格式音频支持**：支持常见的音频格式（MP3、WAV等）
- **智能转录**：将音频内容转换为文字
- **内容摘要**：使用AI模型生成简洁准确的课堂摘要
- **格式转换**：内置音频格式转换功能
- **易于集成**：简单的API接口，方便集成到现有系统

## 系统要求

- Python 3.8+
- 有效的OpenAI API密钥
- ffmpeg（用于音频处理）

## 安装依赖

```bash
# 使用uv安装依赖（推荐）
uv sync

# 或者使用pip安装
pip install -r requirements.txt
```

## 快速开始

### 1. 配置API密钥

在使用功能之前，需要配置OpenAI API密钥：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

或者在代码中设置：

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

### 2. 处理录音文件

```python
from src.audio_handler import convert_audio_format, validate_audio_file
from src.transcriber import transcribe_audio
from src.summarizer import generate_summary

# 示例：处理录音文件并生成摘要
def process_recording(file_path):
    # 1. 验证音频文件
    if not validate_audio_file(file_path):
        raise ValueError("无效的音频文件")
    
    # 2. 转换音频格式（如果需要）
    converted_path = convert_audio_format(file_path, target_format=".mp3")
    
    # 3. 转录音频
    transcript = transcribe_audio(converted_path)
    
    # 4. 生成摘要
    summary = generate_summary(transcript)
    
    return summary
```

## 高级配置

### 音频处理选项

- **输出格式**：支持MP3和WAV格式
- **质量设置**：可调整音频质量和文件大小平衡
- **错误处理**：自动重试机制和详细的错误报告

### 摘要生成选项

- **摘要长度**：可控制摘要的详细程度
- **主题提取**：从音频内容中提取关键主题
- **时间戳**：可选择在摘要中包含时间信息

## 使用示例

### 命令行使用

```bash
# 直接处理录音文件
python -m src.main --audio-file path/to/recording.mp3

# 批量处理
./batch_process.sh recordings/
```

### 编程接口使用

```python
from src.recording_processor import RecordingProcessor

processor = RecordingProcessor(api_key="your-api-key")
summary = processor.process_recording("recording.mp3")

print(summary)
```

## 错误处理

常见错误及解决方案：

- **"未找到moviepy"**：运行 `pip install moviepy` 安装依赖
- **API密钥错误**：检查OpenAI API密钥是否有效
- **音频格式不支持**：确认输入文件是支持的音频格式
- **文件权限错误**：检查对输入和输出目录的访问权限

## 性能优化

- **大文件处理**：对于长时间录音，建议分段处理
- **并发处理**：支持多个文件的并发处理
- **缓存机制**：避免重复处理相同的音频文件

## 故障排除

### 音频转换问题

如果遇到音频格式转换问题：

1. 确认已安装moviepy依赖
2. 检查ffmpeg是否正确安装
3. 查看是否有足够的磁盘空间

### API限制问题

如果遇到API限制：

1. 检查API配额使用情况
2. 考虑降低请求频率
3. 检查API密钥的有效性

## 技术细节

### 架构概述

- **音频处理层**：负责音频格式转换和预处理
- **转录层**：使用OpenAI Whisper API进行语音转文字
- **摘要生成层**：基于GPT模型生成内容摘要
- **结果输出层**：格式化并保存最终摘要

### 数据流

```
录音文件 → 音频验证 → 格式转换 → 语音转文字 → 内容摘要 → 输出结果
```

## 维护和支持

- **定期更新**：保持依赖库的最新版本
- **监控性能**：跟踪处理时间和准确性
- **错误日志**：详细记录处理过程中的错误信息

## 许可证

请参见项目根目录下的LICENSE文件。