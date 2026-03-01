#!/bin/bash

# 快速测试脚本

echo "🛏️ Pillow Talk Desktop 测试"
echo "============================"
echo ""

# 检查后端
echo "1️⃣ 检查后端服务..."
BACKEND_DIR="../pillow-talk-backend"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "❌ 后端虚拟环境不存在"
    echo "请先运行: ./install.sh"
    exit 1
fi

echo "✓ 后端虚拟环境存在"

# 检查 .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "❌ 后端 .env 文件不存在"
    exit 1
fi

echo "✓ 后端配置文件存在"

# 检查前端依赖
echo ""
echo "2️⃣ 检查前端依赖..."

if [ ! -d "node_modules" ]; then
    echo "❌ Node.js 依赖未安装"
    echo "请先运行: ./install.sh"
    exit 1
fi

echo "✓ Node.js 依赖已安装"

# 启动测试
echo ""
echo "3️⃣ 启动应用测试..."
echo ""
echo "提示："
echo "  - 应用会自动启动后端服务"
echo "  - 首次运行可能需要授权摄像头访问"
echo "  - 按 Ctrl+C 停止应用"
echo ""
echo "按 Enter 继续..."
read

npm start
