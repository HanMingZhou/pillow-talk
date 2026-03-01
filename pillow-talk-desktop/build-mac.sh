#!/bin/bash

# macOS 应用构建脚本

echo "🛏️ 构建 Pillow Talk macOS 应用"
echo "================================"
echo ""

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "❌ 错误: 未找到 node_modules"
    echo "请先运行: ./install.sh"
    exit 1
fi

# 清理旧的构建
if [ -d "dist" ]; then
    echo "🧹 清理旧的构建文件..."
    rm -rf dist
fi

# 构建应用
echo "📦 开始构建 macOS 应用..."
npm run build:mac

if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo ""
echo "================================"
echo "✅ 构建完成！"
echo ""
echo "构建产物位于 dist/ 目录："
ls -lh dist/

echo ""
echo "安装方法："
echo "  1. 打开 dist/ 目录中的 .dmg 文件"
echo "  2. 将 Pillow Talk 拖到 Applications 文件夹"
echo "  3. 首次运行可能需要在"系统偏好设置"中允许运行"
echo ""
