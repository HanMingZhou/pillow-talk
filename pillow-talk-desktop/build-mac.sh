#!/bin/bash

# macOS 应用构建脚本

set -e  # 遇到错误立即退出

echo "🛏️  构建 Pillow Talk macOS 应用"
echo "=============================="
echo ""

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "❌ 未找到 node_modules，请先运行: ./install.sh"
    exit 1
fi

# 清理旧构建
[ -d "dist" ] && rm -rf dist

# 构建
echo "📦 正在构建..."
npm run build:mac

echo ""
echo "=============================="
echo "✅ 构建完成！"
echo ""
echo "安装包位置: dist/"
ls -lh dist/*.dmg 2>/dev/null || ls -lh dist/
echo ""
echo "安装方法："
echo "  1. 打开 .dmg 文件"
echo "  2. 拖动到 Applications 文件夹"
echo ""
