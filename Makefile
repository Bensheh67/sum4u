# 音频/视频总结工具 - Make 任务
# 使用方法: make <命令>

# 配置
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := $(shell command -v uv 2> /dev/null)

# 默认目标
.PHONY: help install web video audio batch config clean

# 显示帮助信息
help:
	@echo "🎥 音频/视频总结工具 - 可用命令"
	@echo "=================================="
	@echo ""
	@echo "启动命令:"
	@echo "  make web          - 启动 Web 界面 (http://localhost:8000)"
	@echo "  make video URL=xxx - 处理视频 URL"
	@echo "  make audio FILE=xxx - 处理本地音频文件"
	@echo "  make batch        - 批量处理 uploads/ 文件夹"
	@echo ""
	@echo "配置命令:"
	@echo "  make install      - 创建虚拟环境并安装依赖"
	@echo "  make config       - 配置 API 密钥"
	@echo "  make update       - 更新依赖"
	@echo ""
	@echo "其他命令:"
	@echo "  make clean        - 清理生成的文件"
	@echo "  make test         - 运行测试"
	@echo ""
	@echo "示例:"
	@echo "  make video URL=\"https://www.youtube.com/watch?v=xxx\""
	@echo "  make audio FILE=\"./uploads/audio.mp3\""

# 创建虚拟环境并安装依赖
install:
	@if [ -z "$(UV)" ]; then \
		echo "📦 使用 pip 创建虚拟环境..."; \
		python3 -m venv $(VENV); \
		$(PIP) install -r requirements.txt; \
	else \
		echo "📦 使用 uv 创建虚拟环境..."; \
		uv venv; \
		uv pip install -r requirements.txt; \
	fi
	@echo "✅ 依赖安装完成"

# 确保虚拟环境和依赖存在
$(VENV):
	@make install

# 检查并创建必要的文件夹
dirs:
	@mkdir -p downloads summaries transcriptions uploads reports

# 配置 API 密钥
config: $(VENV)
	@$(PYTHON) setup_api_keys.py

# 启动 Web 界面
web: $(VENV) dirs
	@echo "🌐 启动 Web 服务器..."
	@echo "访问地址: http://localhost:8000"
	@$(PYTHON) -c "import uvicorn; from src.webui import app; uvicorn.run(app, host='0.0.0.0', port=8000)"

# 处理视频 URL
video: $(VENV) dirs
ifndef URL
	@echo "❌ 错误: 请提供视频 URL"
	@echo "用法: make video URL=\"https://...\" [MODEL=small] [PROMPT=模板名]"
	@exit 1
endif
	@echo "🎥 处理视频: $(URL)"
	$(eval MODEL ?= small)
	$(eval PROMPT ?= default课堂笔记)
	@$(PYTHON) src/main.py --url "$(URL)" --model $(MODEL) --prompt_template "$(PROMPT)"

# 处理本地音频文件
audio: $(VENV) dirs
ifndef FILE
	@echo "❌ 错误: 请提供音频文件路径"
	@echo "用法: make audio FILE=\"/path/to/audio.mp3\" [MODEL=small] [PROMPT=模板名]"
	@exit 1
endif
	@echo "🎵 处理音频: $(FILE)"
	$(eval MODEL ?= small)
	$(eval PROMPT ?= default课堂笔记)
	@$(PYTHON) src/main.py --audio-file "$(FILE)" --model $(MODEL) --prompt_template "$(PROMPT)"

# 批量处理
batch: $(VENV) dirs
	@echo "📦 批量处理 uploads/ 文件夹..."
	$(eval MODEL ?= small)
	$(eval PROMPT ?= default课堂笔记)
	@$(PYTHON) src/main.py --batch --upload-dir uploads --model $(MODEL) --prompt_template "$(PROMPT)"

# 更新依赖
update: $(VENV)
	@if [ -z "$(UV)" ]; then \
		$(PIP) install -U -r requirements.txt; \
	else \
		uv pip install -r requirements.txt; \
	fi
	@echo "✅ 依赖更新完成"

# 运行测试
test: $(VENV)
	@$(PYTHON) -m pytest tests/ -v || echo "⚠️ 测试模块未配置"

# 清理生成的文件
clean:
	@echo "🧹 清理生成的文件..."
	@rm -rf downloads/* summaries/* transcriptions/* reports/*
	@echo "✅ 清理完成 (保留 uploads/ 和 config.json)"

# 深度清理（包括虚拟环境）
clean-all:
	@echo "🧹 深度清理..."
	@rm -rf $(VENV) downloads summaries transcriptions uploads reports
	@echo "✅ 所有文件已清理"
