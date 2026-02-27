#!/bin/bash

echo "启动 Pillow Talk"
echo ""

# 进入后端目录
cd pillow-talk-backend

# 检查虚拟环境是否完整
if [ ! -f "venv/bin/activate" ] || [ ! -f "venv/bin/python" ]; then
    echo "虚拟环境不完整，重新创建..."
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    echo "安装依赖..."
    pip install -r requirements.txt
else
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    # 检查关键依赖是否安装
    if ! python -c "import uvicorn" 2>/dev/null; then
        echo "依赖不完整，重新安装..."
        pip install -r requirements.txt
    fi
fi

# 启动后端
echo "启动后端..."
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
python -m uvicorn pillow_talk.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "等待后端启动..."
sleep 5

# 打开浏览器
echo "打开浏览器..."
if command -v wslview > /dev/null; then
    wslview pillow-talk-web/index.html
else
    echo "请在 Windows 浏览器中打开: file:///C:/pythonProject/pillow-talk/pillow-talk-web/index.html"
fi

echo ""
echo "完成！后端运行在 http://localhost:8000"
echo "按 Ctrl+C 停止"
echo ""

# 等待用户中断
wait $BACKEND_PID
