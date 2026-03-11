#!/bin/bash

# ============================================================
# Pillow Talk Android APK 构建脚本 (Linux/Mac/WSL)
# 用法: ./build-apk.sh [debug|release] [install]
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 构建模式
BUILD_MODE="${1:-debug}"  # 默认为 debug
INSTALL_AFTER_BUILD="${2:-false}"

# 路径配置
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PROJECT_DIR="pillow-talk-mobile"
ANDROID_DIR="$PROJECT_DIR/android"
APK_OUTPUT_DIR="$ANDROID_DIR/app/build/outputs/apk"

# ========== 工具函数 ==========

show_help() {
    echo ""
    echo -e "${BOLD}Pillow Talk Android APK 构建工具${NC}"
    echo ""
    echo "用法: ./build-apk.sh [debug|release] [install]"
    echo ""
    echo "参数:"
    echo "  debug      构建 Debug APK (默认)"
    echo "  release    构建 Release APK"
    echo "  install    构建后自动安装到连接的设备 (第二个参数)"
    echo ""
    echo "示例:"
    echo "  ./build-apk.sh                  # 构建 Debug APK"
    echo "  ./build-apk.sh debug install    # 构建 Debug APK 并安装到设备"
    echo "  ./build-apk.sh release          # 构建 Release APK"
    echo "  ./build-apk.sh release install  # 构建 Release APK 并安装到设备"
    echo ""
}

print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   🤖 Pillow Talk Android APK 构建         ║${NC}"
    echo -e "${CYAN}║   模式: ${BOLD}${BUILD_MODE^^}${NC}${CYAN}                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "  ${RED}✗${NC} $1"
}

print_info() {
    echo -e "  ${YELLOW}ℹ${NC} $1"
}

print_step() {
    echo ""
    echo -e "${BOLD}📦 $1${NC}"
    echo -e "${CYAN}──────────────────────────────────────────${NC}"
}

# ========== 检查依赖 ==========

check_dependencies() {
    print_step "检查环境依赖"

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装"
        echo "    请访问 https://nodejs.org/ 安装 Node.js 18+"
        exit 1
    fi

    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js 版本过低 (当前: $(node -v))，需要 v18+"
        exit 1
    fi
    print_success "Node.js $(node -v)"

    # 检查 npm
    if ! command -v npm &> /dev/null; then
        print_error "npm 未安装"
        exit 1
    fi
    print_success "npm v$(npm -v)"

    # 检查 Java / JAVA_HOME
    if [ -n "$JAVA_HOME" ]; then
        print_success "JAVA_HOME: $JAVA_HOME"
    else
        # 在 WSL 中自动转换 Windows Java 路径
        if grep -qi microsoft /proc/version 2>/dev/null; then
            JAVA_HOME_WIN=$(cmd.exe /c "echo %JAVA_HOME%" 2>/dev/null | tr -d '\r' || echo "")
            if [ -n "$JAVA_HOME_WIN" ] && [ "$JAVA_HOME_WIN" != "%JAVA_HOME%" ]; then
                JAVA_HOME=$(wslpath "$JAVA_HOME_WIN")
                export JAVA_HOME
                export PATH="$JAVA_HOME/bin:$PATH"
                print_info "WSL 模式: 自动检测到 Windows Java"
                print_success "JAVA_HOME: $JAVA_HOME"
            fi
        fi

        # 如果还是没有 JAVA_HOME，尝试自动检测
        if [ -z "$JAVA_HOME" ]; then
            if command -v java &> /dev/null; then
                JAVA_PATH=$(which java)
                print_info "找到 Java: $JAVA_PATH (建议设置 JAVA_HOME)"
            else
                print_error "Java 未安装或未设置 JAVA_HOME"
                echo "    请安装 JDK 17 或更高版本"
                exit 1
            fi
        fi
    fi

    # 检查 Android SDK (ANDROID_HOME 或 ANDROID_SDK_ROOT)
    if [ -n "$ANDROID_HOME" ]; then
        print_success "ANDROID_HOME: $ANDROID_HOME"
    elif [ -n "$ANDROID_SDK_ROOT" ]; then
        export ANDROID_HOME="$ANDROID_SDK_ROOT"
        print_success "ANDROID_SDK_ROOT: $ANDROID_SDK_ROOT"
    else
        # 尝试常见路径
        if [ -d "$HOME/Android/Sdk" ]; then
            export ANDROID_HOME="$HOME/Android/Sdk"
            print_info "自动检测到 Android SDK: $ANDROID_HOME"
        elif [ -d "$HOME/Library/Android/sdk" ]; then
            export ANDROID_HOME="$HOME/Library/Android/sdk"
            print_info "自动检测到 Android SDK: $ANDROID_HOME"
        else
            print_info "ANDROID_HOME 未设置 (Gradle 可能会自行查找)"
        fi
    fi
}

# ========== 安装依赖 ==========

install_deps() {
    print_step "安装项目依赖"

    if [ -d "$PROJECT_DIR/node_modules" ]; then
        print_success "Node 依赖已存在，跳过安装"
    else
        print_info "安装 Node 依赖..."
        cd "$PROJECT_DIR"
        npm install
        cd ..
        print_success "Node 依赖安装完成"
    fi
}

# ========== 初始化 Capacitor Android 项目 ==========

init_android() {
    print_step "初始化 Android 项目"

    if [ -d "$ANDROID_DIR" ]; then
        print_success "Android 项目已存在，跳过初始化"
        return
    fi

    print_info "首次构建，正在初始化 Android 项目..."

    cd "$PROJECT_DIR"

    # 确保 www 目录存在且有内容
    if [ ! -d "www" ] || [ -z "$(ls -A www 2>/dev/null)" ]; then
        print_info "创建 www 目录并复制资源..."
        mkdir -p www
        cp index.html www/ 2>/dev/null || true
    fi

    # 添加 Android 平台
    npx cap add android

    cd ..
    print_success "Android 项目初始化完成"
}

# ========== 同步资源 ==========

sync_resources() {
    print_step "同步前端资源到 Android"

    # 确保 www 目录内容是最新的
    if [ -f "$PROJECT_DIR/index.html" ]; then
        cp "$PROJECT_DIR/index.html" "$PROJECT_DIR/www/" 2>/dev/null || true
    fi

    cd "$PROJECT_DIR"
    npx cap sync android
    cd ..
    print_success "资源同步完成"
}

# ========== 构建 APK ==========

build_apk() {
    local mode=$1

    print_step "构建 ${mode^^} APK"

    cd "$ANDROID_DIR"

    # 确保 gradlew 可执行
    chmod +x gradlew 2>/dev/null || true

    # 清理旧构建
    print_info "清理旧构建..."
    ./gradlew clean 2>&1 | tail -1

    # 构建
    if [ "$mode" == "release" ]; then
        print_info "构建 Release APK..."
        ./gradlew assembleRelease
    else
        print_info "构建 Debug APK..."
        ./gradlew assembleDebug
    fi

    cd ../..
}

# ========== 显示构建结果 ==========

show_result() {
    local mode=$1
    local apk_path

    if [ "$mode" == "release" ]; then
        apk_path="$APK_OUTPUT_DIR/release/app-release-unsigned.apk"
        # release 签名后的 APK
        [ ! -f "$apk_path" ] && apk_path="$APK_OUTPUT_DIR/release/app-release.apk"
    else
        apk_path="$APK_OUTPUT_DIR/debug/app-debug.apk"
    fi

    echo ""
    if [ -f "$apk_path" ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║   ✅ APK 构建成功！                       ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
        echo ""

        print_info "APK 位置: $apk_path"

        # 显示文件大小
        if command -v du &> /dev/null; then
            SIZE=$(du -h "$apk_path" | cut -f1)
            print_info "文件大小: $SIZE"
        fi

        echo ""
        print_info "安装命令: adb install -r $apk_path"

        # 如果指定了 install 参数，自动安装
        if [ "$INSTALL_AFTER_BUILD" == "install" ]; then
            echo ""
            print_step "安装到设备"

            if ! command -v adb &> /dev/null; then
                print_error "adb 命令不可用，请确保 Android SDK platform-tools 已添加到 PATH"
                return
            fi

            if adb devices | grep -q "device$"; then
                adb install -r "$apk_path"
                print_success "安装完成！"
            else
                print_error "未检测到连接的设备"
                echo "    请确保："
                echo "      1. 手机通过 USB 连接到电脑"
                echo "      2. 已开启 USB 调试模式"
                echo "      3. 已授权此电脑进行调试"
            fi
        fi
    else
        echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
        echo -e "${RED}║   ❌ 未找到 APK 文件                      ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

# ========== 主流程 ==========

main() {
    # 显示帮助
    if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        show_help
        exit 0
    fi

    print_header

    # 检查是否在项目根目录
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "未找到 $PROJECT_DIR 目录"
        echo "    请确保在项目根目录 (pillow-talk/) 下运行此脚本"
        exit 1
    fi

    check_dependencies
    install_deps
    init_android
    sync_resources
    build_apk "$BUILD_MODE"
    show_result "$BUILD_MODE"

    echo ""
}

# 捕获错误
trap 'echo ""; print_error "构建过程中出错，请检查上方错误信息"; exit 1' ERR

main "$@"
