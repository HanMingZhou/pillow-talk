@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
:: Pillow Talk Android APK BUILD SCRIPT (Windows)
:: ============================================================

title Pillow Talk APK Builder

set "BUILD_MODE=debug"
set "INSTALL_AFTER_BUILD=false"

if "%~1"=="release" set "BUILD_MODE=release"
if "%~1"=="debug" set "BUILD_MODE=debug"
if "%~1"=="install" (
    set "BUILD_MODE=debug"
    set "INSTALL_AFTER_BUILD=true"
)
if "%~2"=="install" set "INSTALL_AFTER_BUILD=true"

if "%~1"=="--help" goto :show_help

set "PROJECT_NAME=pillow-talk-mobile"
set "ANDROID_PATH=%PROJECT_NAME%\android"
set "APK_OUT_ROOT=%ANDROID_PATH%\app\build\outputs\apk"

echo.
echo ================================================
echo   Pillow Talk Android APK Build
echo   Mode: %BUILD_MODE%
echo ================================================
echo.

:: ========== Step 1: Detect Env ==========
echo [Step 1/5] Checking environment...
echo ------------------------------------------------

node -v >nul 2>&1 || (echo [Error] Node.js not found && pause && exit /b 1)
for /f "tokens=1" %%a in ('node -v') do echo [OK] Node %%a

call npm -v >nul 2>&1 || (echo [Error] npm not found && pause && exit /b 1)
for /f %%a in ('call npm -v') do echo [OK] npm v%%a

if not defined JAVA_HOME (
    for /d %%D in ("C:\Program Files\Java\jdk*") do set "JAVA_HOME=%%D"
)
if defined JAVA_HOME (
    echo [OK] JAVA_HOME: %JAVA_HOME%
) else (
    echo [Error] JAVA_HOME not set
    pause && exit /b 1
)

if not defined ANDROID_HOME (
    if exist "%LOCALAPPDATA%\Android\Sdk" set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
)
if defined ANDROID_HOME echo [OK] Android SDK ready

echo.

:: ========== Step 2: Install Deps ==========
echo [Step 2/5] Installing dependencies...
echo ------------------------------------------------

if exist "%PROJECT_NAME%\node_modules" (
    echo [Info] Dependencies exists. Skipping.
) else (
    echo [Info] Running npm install...
    cd "%PROJECT_NAME%"
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        echo [Error] npm install failed
        cd .. && pause && exit /b 1
    )
    cd ..
)

echo.

:: ========== Step 3: Sync & Patch ==========
echo [Step 3/5] Syncing resources and patching...
echo ------------------------------------------------

if exist "%PROJECT_NAME%\index.html" (
    if not exist "%PROJECT_NAME%\www" mkdir "%PROJECT_NAME%\www"
    copy /y "%PROJECT_NAME%\index.html" "%PROJECT_NAME%\www\" >nul
)

cd "%PROJECT_NAME%"
call npx cap sync android
if errorlevel 1 (
    echo [Error] Sync failed
    cd .. && pause && exit /b 1
)

:: ----- Patching Java 17 compatibility -----
echo [Info] Configuring Java 17 for build.gradle files...
powershell -ExecutionPolicy Bypass -Command "(Get-Content android\app\capacitor.build.gradle) -replace 'VERSION_21', 'VERSION_17' | Set-Content android\app\capacitor.build.gradle"
powershell -ExecutionPolicy Bypass -Command "(Get-Content android\capacitor-cordova-android-plugins\build.gradle) -replace 'VERSION_21', 'VERSION_17' | Set-Content android\capacitor-cordova-android-plugins\build.gradle"
powershell -ExecutionPolicy Bypass -Command "(Get-Content node_modules\@capacitor\android\capacitor\build.gradle) -replace 'VERSION_21', 'VERSION_17' | Set-Content node_modules\@capacitor\android\capacitor\build.gradle"
:: ------------------------------------------

cd ..
echo [OK] Synchronization and environment setup complete

echo.

:: ========== Step 4: Gradle Build ==========
echo [Step 4/5] Building APK (This might take a while)...
echo ------------------------------------------------

cd "%ANDROID_PATH%"
call gradlew.bat clean >nul
if "%BUILD_MODE%"=="release" (
    call gradlew.bat assembleRelease
) else (
    call gradlew.bat assembleDebug
)

if errorlevel 1 (
    echo.
    echo [Error] Build failed. Please check the logs.
    cd ..\.. && pause && exit /b 1
)

cd ..\..

echo.

:: ========== Step 5: Finalize ==========
echo [Step 5/5] Build finished! Gathering output...
echo ------------------------------------------------

if "%BUILD_MODE%"=="release" (
    set "APK_FILE_PATH=%APK_OUT_ROOT%\release\app-release-unsigned.apk"
    if not exist "!APK_FILE_PATH!" set "APK_FILE_PATH=%APK_OUT_ROOT%\release\app-release.apk"
) else (
    set "APK_FILE_PATH=%APK_OUT_ROOT%\debug\app-debug.apk"
)

if exist "!APK_FILE_PATH!" (
    echo [OK] APK Location: !APK_FILE_PATH!
    
    if "%INSTALL_AFTER_BUILD%"=="true" (
        echo [Info] Attempting to install on device...
        adb install -r "!APK_FILE_PATH!"
        if errorlevel 1 (
            echo [Warning] Installation failed.
        ) else (
            echo [OK] App installed and updated on the device!
        )
    )
) else (
    echo [Error] APK not found in !APK_FILE_PATH!
    pause && exit /b 1
)

echo.
echo Build process complete.
pause
exit /b 0

:show_help
echo.
echo Pillow Talk Android APK Build Helper
echo.
echo Usage: build-apk.bat [debug|release] [install]
exit /b 0
