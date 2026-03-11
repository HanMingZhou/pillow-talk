#!/bin/bash

# ============================================================
# Pillow Talk iOS App 构建脚本 (macOS only)
# 用法: ./build-ios.sh [simulator|device] [open]
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 构建目标
BUILD_TARGET="${1:-simulator}"  # 默认为 simulator
OPEN_XCODE="${2:-false}"

# 路径配置
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PROJECT_DIR="pillow-talk-mobile"
IOS_DIR="$PROJECT_DIR/ios"

# ========== 工具函数 ==========

show_help() {
    echo ""
    echo -e "${BOLD}Pillow Talk iOS App 构建工具${NC}"
    echo ""
    echo "用法: ./build-ios.sh [simulator|device] [open]"
    echo ""
    echo "参数:"
    echo "  simulator  构建模拟器版本 (默认)"
    echo "  device     构建真机版本 (需要签名证书)"
    echo "  open       构建后打开 Xcode 项目 (第二个参数)"
    echo ""
    echo "示例:"
    echo "  ./build-ios.sh                    # 构建模拟器版本"
    echo "  ./build-ios.sh simulator open     # 构建并打开 Xcode"
    echo "  ./build-ios.sh device             # 构建真机版本"
    echo "  ./build-ios.sh open               # 仅打开 Xcode 项目"
    echo ""
    echo -e "${YELLOW}⚠️  注意: 此脚本仅支持 macOS 系统${NC}"
    echo ""
}

print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   🍎 Pillow Talk iOS App 构建             ║${NC}"
    echo -e "${CYAN}║   目标: ${BOLD}${BUILD_TARGET^^}${NC}${CYAN}                          ║${NC}"
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

# ========== 平台检查 ==========

check_platform() {
    if [[ "$(uname)" != "Darwin" ]]; then
        echo ""
        print_error "此脚本仅支持 macOS 系统"
        echo "    iOS 应用只能在 macOS 上构建"
        echo ""
        exit 1
    fi
}

# ========== 检查依赖 ==========

check_dependencies() {
    print_step "检查环境依赖"

    # 检查 Xcode
    if ! command -v xcodebuild &> /dev/null; then
        print_error "Xcode 未安装"
        echo "    请从 App Store 安装 Xcode 或运行:"
        echo "    xcode-select --install"
        exit 1
    fi
    XCODE_VERSION=$(xcodebuild -version | head -1)
    print_success "$XCODE_VERSION"

    # 检查 Xcode Command Line Tools
    if ! xcode-select -p &> /dev/null; then
        print_error "Xcode Command Line Tools 未安装"
        echo "    请运行: xcode-select --install"
        exit 1
    fi
    print_success "Xcode Command Line Tools 已安装"

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

    # 检查 CocoaPods
    if ! command -v pod &> /dev/null; then
        print_info "CocoaPods 未安装，正在安装..."
        sudo gem install cocoapods
        if [ $? -ne 0 ]; then
            print_error "CocoaPods 安装失败"
            echo "    请手动运行: sudo gem install cocoapods"
            exit 1
        fi
    fi
    POD_VERSION=$(pod --version)
    print_success "CocoaPods v$POD_VERSION"
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

    # 安装 Capacitor iOS 平台依赖 (如果尚未安装)
    if ! grep -q "@capacitor/ios" "$PROJECT_DIR/package.json" 2>/dev/null; then
        print_info "安装 @capacitor/ios..."
        cd "$PROJECT_DIR"
        npm install @capacitor/ios
        cd ..
        print_success "@capacitor/ios 安装完成"
    fi
}

# ========== 初始化 Capacitor iOS 项目 ==========

init_ios() {
    print_step "初始化 iOS 项目"

    if [ -d "$IOS_DIR" ]; then
        print_success "iOS 项目已存在，跳过初始化"
        return
    fi

    print_info "首次构建，正在初始化 iOS 项目..."

    cd "$PROJECT_DIR"

    # 确保 www 目录存在且有内容
    if [ ! -d "www" ] || [ -z "$(ls -A www 2>/dev/null)" ]; then
        print_info "创建 www 目录并复制资源..."
        mkdir -p www
        cp index.html www/ 2>/dev/null || true
    fi

    # 添加 iOS 平台
    npx cap add ios

    cd ..
    print_success "iOS 项目初始化完成"
}

# ========== 同步资源 ==========

sync_resources() {
    print_step "同步前端资源到 iOS"

    # 确保 www 目录内容是最新的
    if [ -f "$PROJECT_DIR/index.html" ]; then
        cp "$PROJECT_DIR/index.html" "$PROJECT_DIR/www/" 2>/dev/null || true
    fi

    cd "$PROJECT_DIR"
    npx cap sync ios
    cd ..
    print_success "资源同步完成"
}

# ========== 安装 CocoaPods 依赖 ==========

install_pods() {
    print_step "安装 CocoaPods 依赖"

    if [ -d "$IOS_DIR/App/Pods" ]; then
        print_success "Pods 已存在，跳过安装"
    else
        print_info "运行 pod install..."
        cd "$IOS_DIR/App"
        pod install
        cd ../..
        print_success "CocoaPods 依赖安装完成"
    fi
}

# ========== 构建 iOS App ==========

build_ios() {
    local target=$1

    print_step "构建 iOS App (${target})"

    local WORKSPACE="$IOS_DIR/App/App.xcworkspace"
    local SCHEME="App"

    if [ ! -d "$WORKSPACE" ]; then
        # 如果没有 workspace，使用 xcodeproj
        WORKSPACE="$IOS_DIR/App/App.xcodeproj"
        print_info "使用 xcodeproj: $WORKSPACE"
    fi

    if [ "$target" == "simulator" ]; then
        print_info "构建模拟器版本..."
        xcodebuild \
            -workspace "$IOS_DIR/App/App.xcworkspace" \
            -scheme "$SCHEME" \
            -configuration Debug \
            -destination "generic/platform=iOS Simulator" \
            -derivedDataPath "$IOS_DIR/build" \
            build \
            2>&1 | tail -5

    elif [ "$target" == "device" ]; then
        print_info "构建真机版本..."
        print_info "注意: 真机构建需要有效的签名证书和 Provisioning Profile"
        echo ""
        xcodebuild \
            -workspace "$IOS_DIR/App/App.xcworkspace" \
            -scheme "$SCHEME" \
            -configuration Release \
            -destination "generic/platform=iOS" \
            -derivedDataPath "$IOS_DIR/build" \
            build \
            2>&1 | tail -5
    fi
}

# ========== 打开 Xcode ==========

open_xcode() {
    print_step "打开 Xcode 项目"

    local WORKSPACE="$IOS_DIR/App/App.xcworkspace"

    if [ -d "$WORKSPACE" ]; then
        print_info "打开 $WORKSPACE ..."
        open "$WORKSPACE"
        print_success "Xcode 已打开"
    elif [ -d "$IOS_DIR/App/App.xcodeproj" ]; then
        print_info "打开 App.xcodeproj ..."
        open "$IOS_DIR/App/App.xcodeproj"
        print_success "Xcode 已打开"
    else
        # 使用 Capacitor 打开
        print_info "使用 Capacitor 打开 Xcode..."
        cd "$PROJECT_DIR"
        npx cap open ios
        cd ..
        print_success "Xcode 已打开"
    fi

    echo ""
    print_info "在 Xcode 中你可以："
    echo "      1. 选择模拟器或真机目标"
    echo "      2. 配置签名证书 (真机部署需要)"
    echo "      3. 点击 ▶ 运行应用"
}

# ========== 显示构建结果 ==========

show_result() {
    local target=$1

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ iOS 构建成功！                       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$target" == "simulator" ]; then
        local APP_PATH=$(find "$IOS_DIR/build" -name "*.app" -path "*/Debug-iphonesimulator/*" 2>/dev/null | head -1)
        if [ -n "$APP_PATH" ]; then
            print_info "App 位置: $APP_PATH"

            # 显示文件大小
            if command -v du &> /dev/null; then
                SIZE=$(du -sh "$APP_PATH" | cut -f1)
                print_info "App 大小: $SIZE"
            fi

            echo ""
            print_info "在模拟器中运行:"
            echo "      xcrun simctl install booted \"$APP_PATH\""
            echo "      xcrun simctl launch booted com.pillowtalk.app"
        fi
    elif [ "$target" == "device" ]; then
        print_info "真机版本已构建"
        echo ""
        print_info "后续步骤:"
        echo "      1. 在 Xcode 中打开项目进行签名配置"
        echo "      2. 选择你的 Apple 开发者证书"
        echo "      3. 连接设备并点击运行"
        echo ""
        echo "      或运行: ./build-ios.sh device open"
    fi
}

# ========== 主流程 ==========

main() {
    # 显示帮助
    if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        show_help
        exit 0
    fi

    # 仅打开 Xcode 的快捷方式
    if [ "$1" == "open" ]; then
        check_platform
        if [ -d "$IOS_DIR" ]; then
            open_xcode
        else
            print_error "iOS 项目尚未初始化，请先运行: ./build-ios.sh"
        fi
        exit 0
    fi

    print_header

    # 平台检查
    check_platform

    # 检查是否在项目根目录
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "未找到 $PROJECT_DIR 目录"
        echo "    请确保在项目根目录 (pillow-talk/) 下运行此脚本"
        exit 1
    fi

    check_dependencies
    install_deps
    init_ios
    sync_resources
    install_pods
    build_ios "$BUILD_TARGET"
    show_result "$BUILD_TARGET"

    # 如果指定了 open 参数，打开 Xcode
    if [ "$OPEN_XCODE" == "open" ]; then
        open_xcode
    fi

    echo ""
}

# 捕获错误
trap 'echo ""; print_error "构建过程中出错，请检查上方错误信息"; exit 1' ERR

main "$@"
