#!/bin/bash

echo "========================================"
echo "Pillow Talk Android APK 打包"
echo "========================================"
echo ""

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

# 检查 Android 项目是否存在
if [ ! -d "pillow-talk-web/android" ]; then
    echo "[创建 Android 项目]"
    echo ""
    
    cd pillow-talk-web
    
    echo "1. 安装 Capacitor..."
    npm init -y 2>/dev/null || true
    npm install @capacitor/core @capacitor/cli @capacitor/android
    
    echo ""
    echo "2. 初始化 Capacitor..."
    # 创建一个临时的 www 目录作为 web 根目录
    mkdir -p www
    cp index.html www/ 2>/dev/null || true
    npx cap init "Pillow Talk" "com.pillowtalk.app" --web-dir=www
    
    echo ""
    echo "3. 添加 Android 平台..."
    npx cap add android
    
    echo ""
    echo "4. 同步文件..."
    npx cap sync
    
    cd ..
    
    echo ""
    echo "✓ Android 项目创建完成"
    echo ""
fi

echo "[构建 APK]"
echo ""

cd pillow-talk-web/android

# 在 WSL 中设置 JAVA_HOME 指向 Windows Java
if grep -qi microsoft /proc/version; then
    # 从 Windows 获取 JAVA_HOME
    JAVA_HOME_WIN=$(cmd.exe /c "echo %JAVA_HOME%" | tr -d '\r')
    
    if [ "$JAVA_HOME_WIN" != "%JAVA_HOME%" ] && [ -n "$JAVA_HOME_WIN" ]; then
        # 转换 Windows 路径到 WSL 路径，处理空格
        JAVA_HOME_WSL=$(wslpath "$JAVA_HOME_WIN")
        export JAVA_HOME="$JAVA_HOME_WSL"
        export PATH="$JAVA_HOME/bin:$PATH"
        echo "✓ 使用 Windows Java: $JAVA_HOME"
    else
        echo "❌ Windows JAVA_HOME 未设置"
        echo "请在 Windows 中设置 JAVA_HOME 环境变量"
        cd ../..
        exit 1
    fi
    echo ""
fi

echo "1. 清理旧构建..."
./gradlew clean

echo ""
echo "2. 构建 Debug APK..."
echo "这可能需要几分钟，请耐心等待..."
echo ""
./gradlew assembleDebug

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "❌ 构建失败"
    echo "========================================"
    cd ../..
    exit 1
fi

cd ../..

echo ""
echo "========================================"
echo "✓ 构建成功！"
echo "========================================"
echo ""
echo "APK 位置:"
echo "pillow-talk-web/android/app/build/outputs/apk/debug/app-debug.apk"
echo ""

if [ -f "pillow-talk-web/android/app/build/outputs/apk/debug/app-debug.apk" ]; then
    SIZE=$(du -h "pillow-talk-web/android/app/build/outputs/apk/debug/app-debug.apk" | cut -f1)
    echo "文件大小: $SIZE"
    echo ""
    echo "安装到手机:"
    echo "adb install pillow-talk-web/android/app/build/outputs/apk/debug/app-debug.apk"
fi

echo ""
