#!/bin/bash

# Pillow Talk 移动端开发启动脚本

set -e  # 遇到错误立即退出

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛏️  Pillow Talk 移动端开发服务器启动"
echo "=============================="
echo ""

# 检查后端服务
echo "📡 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ 后端服务正在运行"
else
    echo "   ⚠️  后端服务未运行"
    echo ""
    echo "请先启动后端服务："
    echo "  cd ../pillow-talk-backend"
    echo "  ./start.sh"
    echo ""
    read -p "按 Enter 继续（如果后端已在其他终端启动）或 Ctrl+C 退出..."
fi

# 查找可用端口
echo ""
echo "🌐 启动 Web 服务器..."
PORT=8080

echo "   ✓ 使用端口: $PORT"
echo ""
echo "=============================="
echo "访问地址: http://localhost:$PORT"
echo "按 Ctrl+C 停止服务器"
echo "=============================="
echo ""

# 启动 HTTP 服务器
python3 -m http.server $PORT 2>/dev/null || python -m http.server $PORT
