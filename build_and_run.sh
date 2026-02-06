#!/bin/bash

# 构建和运行视频总结工具的 Docker 容器
# 使用方法: ./build_and_run.sh [build|run|rebuild|stop|clean]

set -e  # 如果任何命令失败则退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认动作
ACTION=${1:-run}

echo -e "${BLUE}🎵 音频/视频总结工具 Docker 部署脚本${NC}"
echo "========================================"

case $ACTION in
    build)
        echo -e "${GREEN}🏗️  构建 Docker 镜像...${NC}"
        docker build -t video-summarizer .
        echo -e "${GREEN}✅ 镜像构建完成！${NC}"
        ;;
    run)
        echo -e "${GREEN}🚀 启动 Docker 容器...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ 容器已在后台运行！${NC}"
        echo -e "${BLUE}🌐 访问 Web UI: http://localhost:8000${NC}"
        ;;
    rebuild)
        echo -e "${YELLOW}🔄 停止并删除现有容器...${NC}"
        docker-compose down
        echo -e "${GREEN}🏗️  重新构建 Docker 镜像...${NC}"
        docker build -t video-summarizer .
        echo -e "${GREEN}🚀 启动新容器...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ 重建并启动完成！${NC}"
        echo -e "${BLUE}🌐 访问 Web UI: http://localhost:8000${NC}"
        ;;
    stop)
        echo -e "${YELLOW}🛑 停止 Docker 容器...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ 容器已停止！${NC}"
        ;;
    clean)
        echo -e "${YELLOW}🗑️  删除 Docker 镜像和相关容器...${NC}"
        docker-compose down
        docker rmi -f video-summarizer:latest 2>/dev/null || echo "镜像不存在或已被删除"
        docker system prune -f
        echo -e "${GREEN}✅ 清理完成！${NC}"
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $ACTION${NC}"
        echo -e "${YELLOW}可用命令:${NC}"
        echo "  build   - 构建 Docker 镜像"
        echo "  run     - 运行 Docker 容器"
        echo "  rebuild - 重新构建并运行 Docker 容器"
        echo "  stop    - 停止 Docker 容器"
        echo "  clean   - 清理 Docker 镜像和容器"
        echo ""
        echo -e "${BLUE}使用示例:${NC}"
        echo "  ./build_and_run.sh build    # 仅构建镜像"
        echo "  ./build_and_run.sh run      # 运行容器（默认）"
        echo "  ./build_and_run.sh          # 运行容器（默认）"
        ;;
esac