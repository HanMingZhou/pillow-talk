#!/bin/bash

# Pillow Talk Backend 启动脚本

echo "🚀 Starting Pillow Talk Backend..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  .env file not found, copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file and set your API keys"
    exit 1
fi

# 检查 Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# 安装依赖
echo "📦 Installing dependencies..."
poetry install

# 运行服务
echo "🎉 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
poetry run uvicorn pillow_talk.main:app --reload --host 0.0.0.0 --port 8000
