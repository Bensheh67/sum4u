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
    "anthropic": "your-anthropic-api-key",
    "tikhub": "your-tikhub-api-key"  // 用于处理抖音/TikTok视频
  },
  "default_model": "deepseek-chat",
  "default_language": "auto",
  "output_settings": {
    "transcription_folder": "transcriptions",
    "summary_folder": "summaries",
    "download_folder": "downloads"
  },
  "external_apis": {
    "douyin_api_endpoint": "https://api.tikhub.io"  // TikHub API端点
  }
}
```

## 启动脚本中的API配置

所有启动脚本都会在启动时检查API密钥配置：

- `./start.sh` - 处理视频URL
- `./start_audio.sh` - 处理本地音频文件
- `./start_webui.sh` - 启动Web界面

如果检测到未配置API密钥，将提示您进行配置。

## 抖音/TikTok功能配置

要使用抖音/TikTok视频处理功能，您需要：

1. **获取TikHub API密钥**：
   - 访问 https://user.tikhub.io/users/signin 注册账户
   - 在用户面板中获取您的API密钥

2. **配置API密钥**：
   - 使用交互式配置向导：`python3 setup_api_keys.py`
   - 或手动编辑 `config.json` 文件，添加 `tikhub` 字段

3. **API端点配置**：
   - 默认API端点为 `https://api.tikhub.io`
   - 如需更改，可在 `config.json` 的 `external_apis` 部分修改 `douyin_api_endpoint`

4. **使用功能**：
   - 支持直接粘贴抖音分享链接（如"6.39 03/26 14:06 [抖音] https://..."）
   - 支持标准抖音/TikTok URL
   - 在Web界面中同样可用

## 支持的AI服务提供商

- **DeepSeek**: `deepseek-chat` 模型
- **OpenAI**: GPT系列模型
- **Anthropic**: Claude系列模型
- **TikHub**: 用于处理抖音/TikTok视频的API密钥 (获取地址: https://user.tikhub.io/users/signin)

## Web界面中配置API密钥

启动Web界面后 (`./start_webui.sh`)，您可以在界面上的"API配置"标签页中配置API密钥。

## 注意事项

- 请妥善保管您的API密钥，不要泄露给他人
- 配置文件 `config.json` 通常会被添加到 `.gitignore` 中，避免提交到版本控制系统
- 更改配置后，需要重启服务才能生效

## 🔒 安全最佳实践

为确保API密钥安全，请遵循以下最佳实践：

1. **使用环境变量**（推荐）
   - 在生产环境中，始终使用环境变量存储API密钥
   - 避免将API密钥硬编码在代码或配置文件中
   - Docker容器中使用 `-e` 参数或 `.env` 文件传递API密钥

2. **定期轮换API密钥**
   - 定期更换API密钥，降低泄露风险
   - 在不再需要时及时撤销API密钥

3. **最小权限原则**
   - 为API密钥设置适当的权限限制
   - 仅授予必要的访问权限

4. **安全检查**
   - 在提交代码前，使用 `git status` 检查是否有敏感文件被添加
   - 使用 `git log -p --all | grep -i "sk-"` 检查历史提交中是否包含API密钥
   - 确保 `.gitignore` 正确配置，忽略所有包含敏感信息的文件