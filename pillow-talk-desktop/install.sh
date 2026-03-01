#!/bin/bash

# Pillow Talk Desktop 安装脚本

echo "🛏️ Pillow Talk Desktop 安装脚本"
echo "================================"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo "请先安装 Node.js: https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js 版本: $(node --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    exit 1
fi

echo "✓ npm 版本: $(npm --version)"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请先安装 Python 3.10+: https://www.python.org/"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"

# 安装 Node.js 依赖
echo ""
echo "📦 安装 Node.js 依赖..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Node.js 依赖安装失败"
    exit 1
fi

echo "✓ Node.js 依赖安装完成"

# 检查后端虚拟环境
echo ""
echo "🔍 检查后端环境..."

BACKEND_DIR="../pillow-talk-backend"
VENV_DIR="$BACKEND_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  后端虚拟环境不存在"
    echo "正在创建虚拟环境..."
    
    cd "$BACKEND_DIR"
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
    
    echo "✓ 虚拟环境创建完成"
    
    echo "正在安装后端依赖..."
    source venv/bin/activate
    pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
    
    if [ $? -ne 0 ]; then
        echo "❌ 后端依赖安装失败"
        exit 1
    fi
    
    echo "✓ 后端依赖安装完成"
    deactivate
    cd -
else
    echo "✓ 后端虚拟环境已存在"
fi

# 检查 .env 文件
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "⚠️  后端 .env 文件不存在"
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        echo "正在从 .env.example 创建 .env..."
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo "✓ .env 文件已创建，请编辑配置 API Keys"
    else
        echo "❌ 未找到 .env.example 文件"
    fi
else
    echo "✓ 后端 .env 文件已存在"
fi

echo ""
echo "================================"
echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  开发模式: npm start"
echo "  构建应用: npm run build:mac"
echo ""
echo "注意事项："
echo "  1. 请确保在 $BACKEND_DIR/.env 中配置了 API Keys"
echo "  2. 首次运行可能需要授权摄像头访问权限"
echo "  3. 应用会自动启动后端服务"
echo ""
