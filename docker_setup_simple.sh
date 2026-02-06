#!/bin/bash

# 简化版 Docker 部署脚本 - 专为初学者设计
# 使用方法: ./docker_setup_simple.sh [start|stop|restart|logs]

set -e  # 如果任何命令失败则退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认动作
ACTION=${1:-start}

echo -e "${BLUE}🎵 音频/视频总结工具 - 初学者 Docker 部署脚本${NC}"
echo "=================================================="

case $ACTION in
    start)
        echo -e "${GREEN}🚀 开始启动 Docker 容器...${NC}"
        
        # 检查 config.json 是否存在，如果不存在则创建一个示例
        if [ ! -f "./config.json" ]; then
            echo -e "${YELLOW}⚠️  检测到首次运行，正在创建配置文件...${NC}"
            echo "{}" > config.json
            echo -e "${GREEN}✅ 配置文件已创建，请稍后根据提示配置 API 密钥${NC}"
        fi
        
        # 创建数据目录
        mkdir -p data/downloads data/summaries data/transcriptions data/uploads
        
        # 启动服务
        docker-compose -f docker-compose-simple.yml up -d
        
        echo -e "${GREEN}✅ 容器已在后台成功运行！${NC}"
        echo ""
        echo -e "${BLUE}🌐 如何访问工具:${NC}"
        echo -e "   打开浏览器，访问: http://localhost:8000"
        echo ""
        echo -e "${BLUE}📁 数据存储位置:${NC}"
        echo -e "   下载文件: ./data/downloads/"
        echo -e "   总结文件: ./data/summaries/"
        echo -e "   转录文件: ./data/transcriptions/"
        echo -e "   上传文件: ./data/uploads/"
        echo ""
        echo -e "${YELLOW}💡 提示: 首次访问时请按照页面指引配置 API 密钥${NC}"
        ;;
    stop)
        echo -e "${YELLOW}🛑 正在停止 Docker 容器...${NC}"
        docker-compose -f docker-compose-simple.yml down
        echo -e "${GREEN}✅ 容器已停止！${NC}"
        ;;
    restart)
        echo -e "${YELLOW}🔄 正在重启 Docker 容器...${NC}"
        docker-compose -f docker-compose-simple.yml down
        sleep 3
        docker-compose -f docker-compose-simple.yml up -d
        echo -e "${GREEN}✅ 容器已重启！${NC}"
        echo -e "${BLUE}🌐 访问地址: http://localhost:8000${NC}"
        ;;
    logs)
        echo -e "${BLUE}📋 查看容器日志...${NC}"
        docker-compose -f docker-compose-simple.yml logs -f
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $ACTION${NC}"
        echo ""
        echo -e "${YELLOW}可用命令:${NC}"
        echo "  start   - 启动 Docker 容器（默认）"
        echo "  stop    - 停止 Docker 容器"
        echo "  restart - 重启 Docker 容器"
        echo "  logs    - 查看实时日志"
        echo ""
        echo -e "${BLUE}使用示例:${NC}"
        echo "  ./docker_setup_simple.sh      # 启动容器（默认）"
        echo "  ./docker_setup_simple.sh start    # 启动容器"
        echo "  ./docker_setup_simple.sh stop     # 停止容器"
        echo "  ./docker_setup_simple.sh restart  # 重启容器"
        echo "  ./docker_setup_simple.sh logs     # 查看日志"
        echo ""
        echo -e "${GREEN}🎉 完成！现在你可以访问 http://localhost:8000 来使用音频/视频总结工具了！${NC}"
        ;;
esac