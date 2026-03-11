@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
:: Pillow Talk Android APK 构建脚本 (Windows)
:: 用法: build-apk.bat [debug|release] [install]
:: ============================================================

title Pillow Talk APK Builder

:: 默认参数
set "BUILD_MODE=debug"
set "INSTALL_AFTER_BUILD=false"

:: 解析参数
if "%~1"=="release" set "BUILD_MODE=release"
if "%~1"=="debug" set "BUILD_MODE=debug"
if "%~2"=="install" set "INSTALL_AFTER_BUILD=true"
if "%~1"=="install" (
    set "BUILD_MODE=debug"
    set "INSTALL_AFTER_BUILD=true"
)
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help

:: 路径配置
set "PROJECT_DIR=pillow-talk-mobile"
set "ANDROID_DIR=%PROJECT_DIR%\android"
set "APK_OUTPUT_DIR=%ANDROID_DIR%\app\build\outputs\apk"

echo.
echo ================================================
echo   Pillow Talk Android APK 构建
echo   构建模式: %BUILD_MODE%
echo ================================================
echo.

:: ========== 检查项目目录 ==========

if not exist "%PROJECT_DIR%" (
    echo [错误] 未找到 %PROJECT_DIR% 目录
    echo        请确保在项目根目录 ^(pillow-talk\^) 下运行此脚本
    rem pause
    exit /b 1
)

:: ========== 检查依赖 ==========

echo [步骤] 检查环境依赖...
echo ------------------------------------------------

:: 检查 Node.js
node -v >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js 未安装
    echo        请访问 https://nodejs.org/ 安装 Node.js 18+
    rem pause
    exit /b 1
)
for /f "tokens=1" %%a in ('node -v') do echo [成功] Node.js %%a

:: 检查 npm
call npm -v >nul 2>&1
if errorlevel 1 (
    echo [错误] npm 未安装
    exit /b 1
)
for /f %%a in ('call npm -v') do echo [成功] npm v%%a

:: 检查 Java
if not defined JAVA_HOME (
    :: 尝试自动检测常见 JDK 路径
    if exist "C:\Program Files\Java" (
        for /d %%D in ("C:\Program Files\Java\jdk*") do (
            set "JAVA_HOME=%%D"
        )
    )
    if exist "C:\Program Files\Eclipse Adoptium" (
        for /d %%D in ("C:\Program Files\Eclipse Adoptium\jdk*") do (
            set "JAVA_HOME=%%D"
        )
    )
)

if defined JAVA_HOME (
    echo [成功] JAVA_HOME: %JAVA_HOME%
) else (
    echo [错误] JAVA_HOME 未设置
    echo        请安装 JDK 17+ 并设置 JAVA_HOME 环境变量
    rem pause
    exit /b 1
)

java -version >nul 2>&1
if errorlevel 1 (
    echo [警告] Java 命令不可用，请检查 JAVA_HOME/bin 是否在 PATH 中
) else (
    echo [成功] Java 已就绪
)

:: 检查 Android SDK
if defined ANDROID_HOME (
    echo [成功] ANDROID_HOME: %ANDROID_HOME%
) else if defined ANDROID_SDK_ROOT (
    set "ANDROID_HOME=%ANDROID_SDK_ROOT%"
    echo [成功] ANDROID_SDK_ROOT: %ANDROID_SDK_ROOT%
) else (
    :: 尝试常见路径
    if exist "%LOCALAPPDATA%\Android\Sdk" (
        set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
        echo [信息] 自动检测到 Android SDK: !ANDROID_HOME!
    ) else (
        echo [信息] ANDROID_HOME 未设置 ^(Gradle 可能会自行查找^)
    )
)

echo.

:: ========== 安装依赖 ==========

echo [步骤] 安装项目依赖...
echo ------------------------------------------------

if exist "%PROJECT_DIR%\node_modules" (
    echo [成功] Node 依赖已存在，跳过安装
) else (
    echo [信息] 安装 Node 依赖...
    cd "%PROJECT_DIR%"
    call npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        cd ..
        rem pause
        exit /b 1
    )
    cd ..
    echo [成功] Node 依赖安装完成
)

echo.

:: ========== 初始化 Android 项目 ==========

echo [步骤] 初始化 Android 项目...
echo ------------------------------------------------

if exist "%ANDROID_DIR%" (
    echo [成功] Android 项目已存在，跳过初始化
) else (
    echo [信息] 首次构建，正在初始化 Android 项目...
    cd "%PROJECT_DIR%"

    :: 确保 www 目录存在
    if not exist "www" (
        mkdir www
        copy index.html www\ >nul 2>&1
    )

    :: 添加 Android 平台
    call npx cap add android
    if errorlevel 1 (
        echo [错误] Android 项目初始化失败
        cd ..
        rem pause
        exit /b 1
    )

    cd ..
    echo [成功] Android 项目初始化完成
)

echo.

:: ========== 同步资源 ==========

echo [步骤] 同步前端资源到 Android...
echo ------------------------------------------------

:: 确保 www 目录内容是最新的
if exist "%PROJECT_DIR%\index.html" (
    copy "%PROJECT_DIR%\index.html" "%PROJECT_DIR%\www\" >nul 2>&1
)

cd "%PROJECT_DIR%"
call npx cap sync android
if errorlevel 1 (
    echo [错误] 资源同步失败
    cd ..
    rem pause
    exit /b 1
)
cd ..
echo [成功] 资源同步完成

echo.

:: ========== 构建 APK ==========

echo [步骤] 构建 %BUILD_MODE% APK...
echo ------------------------------------------------
echo.

cd "%ANDROID_DIR%"

:: 清理旧构建
echo [信息] 清理旧构建...
call gradlew.bat clean
if errorlevel 1 (
    echo [错误] 清理失败
    cd ..\..
    rem pause
    exit /b 1
)

:: 执行构建
echo [信息] 构建 APK，请耐心等待...
echo.
if "%BUILD_MODE%"=="release" (
    call gradlew.bat assembleRelease
) else (
    call gradlew.bat assembleDebug
)

if errorlevel 1 (
    echo.
    echo ================================================
    echo   [错误] 构建失败！请检查上方错误信息
    echo ================================================
    cd ..\..
    rem pause
    exit /b 1
)

cd ..\..

:: ========== 显示结果 ==========

echo.

if "%BUILD_MODE%"=="release" (
    set "APK_PATH=%APK_OUTPUT_DIR%\release\app-release-unsigned.apk"
    if not exist "!APK_PATH!" set "APK_PATH=%APK_OUTPUT_DIR%\release\app-release.apk"
) else (
    set "APK_PATH=%APK_OUTPUT_DIR%\debug\app-debug.apk"
)

if exist "!APK_PATH!" (
    echo ================================================
    echo   [成功] APK 构建完成！
    echo ================================================
    echo.
    echo [信息] APK 位置: !APK_PATH!

    :: 显示文件大小
    for %%F in ("!APK_PATH!") do set "SIZE=%%~zF"
    set /a "SIZE_KB=!SIZE! / 1024"
    set /a "SIZE_MB=!SIZE! / 1024 / 1024"
    if !SIZE_MB! gtr 0 (
        echo [信息] 文件大小: ~!SIZE_MB! MB
    ) else (
        echo [信息] 文件大小: ~!SIZE_KB! KB
    )

    echo.
    echo [信息] 安装命令: adb install -r "!APK_PATH!"

    :: 自动安装
    if "%INSTALL_AFTER_BUILD%"=="true" (
        echo.
        echo [步骤] 安装到设备...
        echo ------------------------------------------------

        :: 检查 adb 是否可用
        adb version >nul 2>&1
        if errorlevel 1 (
            echo [错误] adb 命令不可用
            echo        请确保 Android SDK platform-tools 已添加到 PATH
        ) else (
            :: 检查是否有设备连接
            adb devices | findstr /E "device" >nul
            if errorlevel 1 (
                echo [错误] 未检测到连接的设备
                echo        请确保:
                echo          1. 手机通过 USB 连接到电脑
                echo          2. 已开启 USB 调试模式
                echo          3. 已授权此电脑进行调试
            ) else (
                adb install -r "!APK_PATH!"
                if errorlevel 1 (
                    echo [错误] 安装失败
                ) else (
                    echo [成功] 安装完成！
                )
            )
        )
    )
) else (
    echo ================================================
    echo   [错误] 未找到 APK 文件
    echo ================================================
    rem pause
    exit /b 1
)

echo.
echo 按任意键退出...
rem pause >nul
exit /b 0

:: ========== 帮助信息 ==========

:show_help
echo.
echo Pillow Talk Android APK 构建工具
echo.
echo 用法: build-apk.bat [debug^|release] [install]
echo.
echo 参数:
echo   debug      构建 Debug APK (默认)
echo   release    构建 Release APK
echo   install    构建后自动安装到连接的设备 (第二个参数)
echo.
echo 示例:
echo   build-apk.bat                  构建 Debug APK
echo   build-apk.bat debug install    构建 Debug APK 并安装到设备
echo   build-apk.bat release          构建 Release APK
echo   build-apk.bat release install  构建 Release APK 并安装到设备
echo.
exit /b 0
