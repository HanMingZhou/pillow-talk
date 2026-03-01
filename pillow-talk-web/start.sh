#!/bin/bash

# Pillow Talk Web 版启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛏️  Pillow Talk Web 版启动脚本"
echo "================================"
echo "当前目录: $(pwd)"
echo ""

# 检查后端是否运行
echo "📡 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务正在运行"
else
    echo "⚠️  后端服务未运行"
    echo ""
    echo "请选择启动方式："
    echo "  1) Docker (推荐，隔离环境)"
    echo "  2) Poetry 虚拟环境 (开发模式)"
    echo "  3) 手动启动"
    echo ""
    read -p "请选择 (1/2/3): " -n 1 -r
    echo ""
    
    if [[ $REPLY == "1" ]]; then
        # Docker 方式
        cd ../pillow-talk-backend
        echo "🐳 使用 Docker 启动后端服务..."
        
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker 未安装，请先安装 Docker"
            exit 1
        fi
        
        docker-compose up -d
        cd ../pillow-talk-web
        echo "⏳ 等待后端启动..."
        sleep 5
        
    elif [[ $REPLY == "2" ]]; then
        # Poetry 虚拟环境方式
        cd ../pillow-talk-backend
        echo "📦 使用 Poetry 虚拟环境启动后端服务..."
        
        if ! command -v poetry &> /dev/null; then
            echo "❌ Poetry 未安装，请先安装 Poetry："
            echo "   curl -sSL https://install.python-poetry.org | python3 -"
            exit 1
        fi
        
        # 检查 .env 文件
        if [ ! -f .env ]; then
            echo "⚠️  .env 文件不存在，从 .env.example 复制..."
            cp .env.example .env
            echo "⚠️  请编辑 .env 文件并设置 API Keys"
            echo ""
            read -p "按 Enter 继续..."
        fi
        
        # 检查并安装依赖
        if poetry env info --path > /dev/null 2>&1; then
            echo "✅ 虚拟环境已存在，检查依赖..."
            poetry install --no-interaction
        else
            echo "📦 首次运行，创建虚拟环境并安装依赖..."
            poetry install
        fi
        
        # 在后台启动服务
        echo "🚀 启动后端服务（后台运行）..."
        nohup poetry run uvicorn pillow_talk.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        BACKEND_PID=$!
        echo "后端进程 PID: $BACKEND_PID"
        echo $BACKEND_PID > backend.pid
        
        cd ../pillow-talk-web
        echo "⏳ 等待后端启动..."
        sleep 5
        
        # 保存清理函数
        cleanup() {
            echo ""
            echo "🛑 停止后端服务..."
            if [ -f ../pillow-talk-backend/backend.pid ]; then
                kill $(cat ../pillow-talk-backend/backend.pid) 2>/dev/null
                rm ../pillow-talk-backend/backend.pid
            fi
            exit 0
        }
        trap cleanup EXIT INT TERM
        
    else
        echo "❌ 取消启动"
        echo ""
        echo "请手动启动后端服务："
        echo "  方式 1 - Docker:"
        echo "    cd pillow-talk-backend && docker-compose up -d"
        echo ""
        echo "  方式 2 - Poetry 虚拟环境:"
        echo "    cd pillow-talk-backend"
        echo "    poetry install"
        echo "    poetry run uvicorn pillow_talk.main:app --reload"
        exit 1
    fi
fi

echo ""
echo "🌐 启动 Web 服务器..."

# 查找可用端口
PORT=8080
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    echo "⚠️  端口 $PORT 已被占用，尝试下一个端口..."
    PORT=$((PORT + 1))
done

echo "✅ 使用端口: $PORT"
echo ""
echo "访问地址："
echo "  http://localhost:$PORT"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动简单的 HTTP 服务器
if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    python -m http.server $PORT
else
    echo "❌ 未找到 Python，请手动打开 index.html"
    echo ""
    echo "或者安装 Python："
    echo "  https://www.python.org/downloads/"
    exit 1
fi
