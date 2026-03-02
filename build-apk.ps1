Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pillow Talk Android APK 打包" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Android 项目
if (-not (Test-Path "pillow-talk-web\android")) {
    Write-Host "❌ Android 项目不存在" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先在 WSL 中运行: ./build-apk.sh" -ForegroundColor Yellow
    Write-Host "创建 Android 项目后，再运行此脚本构建 APK" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[构建 APK]" -ForegroundColor Green
Write-Host ""

# 检查 Java
if (-not $env:JAVA_HOME) {
    Write-Host "❌ JAVA_HOME 未设置" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✓ JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Green
Write-Host ""

cd pillow-talk-web\android

Write-Host "1. 清理旧构建..." -ForegroundColor Yellow
.\gradlew.bat clean

Write-Host ""
Write-Host "2. 构建 Debug APK..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟，请耐心等待..." -ForegroundColor Yellow
Write-Host ""

.\gradlew.bat assembleDebug

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ 构建失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    cd ..\..
    pause
    exit 1
}

cd ..\..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ 构建成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "APK 位置:" -ForegroundColor Cyan
Write-Host "pillow-talk-web\android\app\build\outputs\apk\debug\app-debug.apk" -ForegroundColor White
Write-Host ""

if (Test-Path "pillow-talk-web\android\app\build\outputs\apk\debug\app-debug.apk") {
    $size = (Get-Item "pillow-talk-web\android\app\build\outputs\apk\debug\app-debug.apk").Length / 1MB
    Write-Host "文件大小: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "安装到手机:" -ForegroundColor Yellow
    Write-Host "adb install pillow-talk-web\android\app\build\outputs\apk\debug\app-debug.apk" -ForegroundColor White
}

Write-Host ""
pause
