# 项目文件结构说明

## 核心源代码文件 (src/)
- `main.py` - 主程序入口
- `audio.py` - 音频下载和提取模块（已更新支持抖音）
- `transcribe.py` - 音频转录模块
- `summarize.py` - 文本摘要模块
- `prompts.py` - 提示词模板
- `audio_handler.py` - 音频处理辅助函数
- `batch_processor.py` - 批量处理模块
- `utils.py` - 工具函数模块（已更新支持抖音/TikTok平台检测）
- `webui.py` - Web界面后端（已更新支持抖音功能）
- `config.py` - 配置管理模块（已更新支持TikHub API密钥）
- `douyin_handler.py` - **新增** 抖音/TikTok视频处理模块

## 配置和依赖文件
- `requirements.txt` - 项目依赖列表
- `pyproject.toml` - Python项目配置文件
- `config_example.json` - 配置文件示例
- `.gitignore` - Git忽略文件配置（已更新）

## 启动脚本
- `start.sh` - 视频处理启动脚本
- `start_audio.sh` - 音频处理启动脚本
- `start_webui.sh` - Web界面启动脚本
- `batch_process.sh` - 批量处理启动脚本
- `batch_process_douyin.py` - **新增** 抖音批量处理脚本

## Docker相关文件
- `Dockerfile` - 标准Docker配置文件
- `Dockerfile.beginner` - 新手友好Docker配置文件
- `Dockerfile.simple` - 简化版Docker配置文件
- `docker-compose.yml` - 标准Docker Compose配置
- `docker-compose-simple.yml` - 简化版Docker Compose配置
- `docker_setup_simple.sh` - Docker简化部署脚本

## 文档文件
- `README.md` - 项目说明文档（已更新抖音功能说明）
- `CHANGELOG.md` - 变更日志（已记录抖音功能添加）
- `API_KEY_CONFIG.md` - API密钥配置说明

## 模板和静态资源
- `templates/` - HTML模板目录
- `static/` - 静态资源目录

## 其他文件
- `.gitignore` - 已更新以忽略测试文件和临时文件
- `skill_definition.md` - 技能定义文件
- `build_and_run.sh` - 构建和运行脚本