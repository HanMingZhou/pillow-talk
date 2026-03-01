#!/bin/bash

# Pillow Talk Desktop 安装脚本

set -e  # 遇到错误立即退出

echo "🛏️  Pillow Talk Desktop 安装"
echo "=============================="
echo ""

# 1. 检查依赖
echo "1️⃣  检查系统依赖..."

if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装: https://nodejs.org/"
    exit 1
fi
echo "   ✓ Node.js $(node --version)"

if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装: https://www.python.org/"
    exit 1
fi
echo "   ✓ Python $(python3 --version)"

# 2. 安装前端依赖
echo ""
echo "2️⃣  安装前端依赖..."
npm install
echo "   ✓ 前端依赖安装完成"

# 3. 设置后端环境
echo ""
echo "3️⃣  设置后端环境..."

BACKEND_DIR="../pillow-talk-backend"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "   创建虚拟环境..."
    (cd "$BACKEND_DIR" && python3 -m venv venv)
    echo "   安装后端依赖..."
    (cd "$BACKEND_DIR" && source venv/bin/activate && pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org)
    echo "   ✓ 后端环境创建完成"
else
    echo "   ✓ 后端环境已存在"
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo "   ⚠️  已创建 .env 文件，请编辑配置 API Keys"
    fi
else
    echo "   ✓ 后端配置文件已存在"
fi

# 完成
echo ""
echo "=============================="
echo "✅ 安装完成！"
echo ""
echo "快速开始："
echo "  npm start          # 启动应用"
echo "  npm run build:mac  # 构建 .dmg 安装包"
echo ""
