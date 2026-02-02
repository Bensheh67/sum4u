# API密钥配置说明

本项目支持多种AI服务提供商，可以通过以下方式配置您的API密钥。

## 配置方式

### 1. 使用交互式配置向导（推荐）

运行以下命令启动交互式配置向导：

```bash
python3 setup_api_keys.py
```

或者在使用命令行工具时：

```bash
python3 src/main.py --setup-api
```

### 2. 手动编辑配置文件

在项目根目录创建或编辑 `config.json` 文件，内容如下：

```json
{
  "api_keys": {
    "deepseek": "your-deepseek-api-key",
    "openai": "your-openai-api-key",
    "anthropic": "your-anthropic-api-key"
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

## 启动脚本中的API配置

所有启动脚本都会在启动时检查API密钥配置：

- `./start.sh` - 处理视频URL
- `./start_audio.sh` - 处理本地音频文件
- `./start_webui.sh` - 启动Web界面

如果检测到未配置API密钥，将提示您进行配置。

## 支持的AI服务提供商

- **DeepSeek**: `deepseek-chat` 模型
- **OpenAI**: GPT系列模型
- **Anthropic**: Claude系列模型

## Web界面中配置API密钥

启动Web界面后 (`./start_webui.sh`)，您可以在界面上的"API配置"标签页中配置API密钥。

## 注意事项

- 请妥善保管您的API密钥，不要泄露给他人
- 配置文件 `config.json` 通常会被添加到 `.gitignore` 中，避免提交到版本控制系统
- 更改配置后，需要重启服务才能生效