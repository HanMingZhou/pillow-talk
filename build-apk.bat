@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
:: Pillow Talk Android APK 构建脚本 (Windows)
:: 
:: 功能:
:: 1. 自动同步 Web 资源到 Android 工程
:: 2. 验证并同步 Java 17 编译环境
:: 3. 自动构建 Debug/Release APK
:: 4. 可选自动安装到连接的设备
:: ============================================================

title Pillow Talk APK Builder

:: 默认参数
set "BUILD_MODE=debug"
set "INSTALL_AFTER_BUILD=false"

:: 解析参数
if "%~1"=="release" set "BUILD_MODE=release"
if "%~1"=="debug" set "BUILD_MODE=debug"
if "%~1"=="install" (
    set "BUILD_MODE=debug"
    set "INSTALL_AFTER_BUILD=true"
)
if "%~2"=="install" set "INSTALL_AFTER_BUILD=true"

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

:: ========== 检查环境依赖 ==========
echo [步骤 1/5] 正在检查环境依赖...
echo ------------------------------------------------

:: Node.js
node -v >nul 2>&1 || (echo [错误] 未安装 Node.js && pause && exit /b 1)
for /f "tokens=1" %%a in ('node -v') do echo [成功] Node.js %%a

:: npm
call npm -v >nul 2>&1 || (echo [错误] 未安装 npm && pause && exit /b 1)
for /f %%a in ('call npm -v') do echo [成功] npm v%%a

:: JAVA_HOME
if not defined JAVA_HOME (
    for /d %%D in ("C:\Program Files\Java\jdk*") do set "JAVA_HOME=%%D"
)
if defined JAVA_HOME (
    echo [成功] JAVA_HOME: %JAVA_HOME%
) else (
    echo [错误] 未找到 JDK 环境，请设置 JAVA_HOME
    pause && exit /b 1
)

:: Android SDK
if not defined ANDROID_HOME (
    if exist "%LOCALAPPDATA%\Android\Sdk" set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
)
if defined ANDROID_HOME echo [成功] Android SDK 已就绪

echo.

:: ========== 安装依赖 ==========
echo [步骤 2/5] 正在安装项目依赖...
echo ------------------------------------------------

if exist "%PROJECT_DIR%\node_modules" (
    echo [信息] Node 依赖已存在，跳过安装
) else (
    echo [信息] 正在安装 Node 依赖...
    cd "%PROJECT_DIR%"
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        cd .. && pause && exit /b 1
    )
    cd ..
)

echo.

:: ========== 同步资源 & 环境修复 ==========
echo [步骤 3/5] 正在同步资源并修复环境兼容性...
echo ------------------------------------------------

:: 确保 www 目录内容是最新的
if exist "%PROJECT_DIR%\index.html" (
    if not exist "%PROJECT_DIR%\www" mkdir "%PROJECT_DIR%\www"
    copy /y "%PROJECT_DIR%\index.html" "%PROJECT_DIR%\www\" >nul
)

cd "%PROJECT_DIR%"
call npx cap sync android
if errorlevel 1 (
    echo [错误] 资源同步失败
    cd .. && pause && exit /b 1
)

:: ----- 自动适配: 确保使用 Java 17 进行编译 (匹配本地环境) -----
echo [信息] 正在配置 Java 17 编译环境...
powershell -Command "(Get-Content android\app\capacitor.build.gradle) -replace 'VERSION_21', 'VERSION_17' | Set-Content android\app\capacitor.build.gradle"
powershell -Command "(Get-Content android\capacitor-cordova-android-plugins\build.gradle) -replace 'VERSION_21', 'VERSION_17' | Set-Content android\capacitor-cordova-android-plugins\build.gradle"
powershell -Command "(Get-Content node_modules\@capacitor\android\capacitor\build.gradle) -replace 'VERSION_21', 'VERSION_17' | Set-Content node_modules\@capacitor\android\capacitor\build.gradle"
:: -----------------------------------------------------------

cd ..
echo [成功] 同步及版本补丁应用完成

echo.

:: ========== 构建 APK ==========
echo [步骤 4/5] 正在构建 APK (这将需要几分钟)...
echo ------------------------------------------------

cd "%ANDROID_DIR%"
call gradlew.bat clean >nul
if "%BUILD_MODE%"=="release" (
    call gradlew.bat assembleRelease
) else (
    call gradlew.bat assembleDebug
)

if errorlevel 1 (
    echo.
    echo [错误] 构建失败！请检查上方输出。
    cd ..\.. && pause && exit /b 1
)

cd ..\..

echo.

:: ========== 完成展示 & 安装 ==========
echo [步骤 5/5] 构建成功！正在整理结果...
echo ------------------------------------------------

if "%BUILD_MODE%"=="release" (
    set "APK_PATH=%APK_OUTPUT_DIR%\release\app-release-unsigned.apk"
    if not exist "!APK_PATH!" set "APK_PATH=%APK_OUTPUT_DIR%\release\app-release.apk"
) else (
    set "APK_PATH=%APK_OUTPUT_DIR%\debug\app-debug.apk"
)

if exist "!APK_PATH!" (
    echo [成功] APK 已生成: !APK_PATH!
    
    :: 自动安装
    if "%INSTALL_AFTER_BUILD%"=="true" (
        echo [信息] 检测到设备，正在尝试安装...
        adb install -r "!APK_PATH!"
        if errorlevel 1 (
            echo [警告] 自动安装失败，请手动安装。
        ) else (
            echo [成功] 应用已连带更新到手机！
        )
    )
) else (
    echo [错误] 找不到 APK 文件
    pause && exit /b 1
)

echo.
echo 构建计划已完成。可以关闭此窗口。
pause
exit /b 0

:show_help
echo.
echo Pillow Talk Android APK 构建助手
echo.
echo 用法: build-apk.bat [debug^|release] [install]
echo.
echo 示例:
echo   .\build-apk.bat           - 仅构建包
echo   .\build-apk.bat install   - 构建并安装到手机
echo.
exit /b 0
