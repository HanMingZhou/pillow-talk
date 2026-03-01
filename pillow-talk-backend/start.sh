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

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found at ./venv"
    echo "Please create it first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "📦 Activating virtual environment..."
source venv/bin/activate

# 运行服务
echo "🎉 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
python -m uvicorn src.pillow_talk.main:app --reload --host 0.0.0.0 --port 8000
