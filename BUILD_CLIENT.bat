@echo off
setlocal EnableDelayedExpansion

REM ================================================================================
REM PersonaPlex Web Client Builder
REM Created by SurAiverse - https://www.youtube.com/@suraiverse
REM ================================================================================

title PersonaPlex - Build Web Client
color 0E

echo.
echo  ===============================================================================
echo  ^|                                                                             ^|
echo  ^|     ____                                    ____  _                         ^|
echo  ^|    ^|  _ \ ___ _ __ ___  ___  _ __   __ _  ^|  _ \^| ^| _____  __              ^|
echo  ^|    ^| ^|_) / _ \ '__/ __^|/ _ \^| '_ \ / _` ^| ^| ^|_) ^| ^|/ _ \ \/ /              ^|
echo  ^|    ^|  __/  __/ ^|  \__ \ (_) ^| ^| ^| ^| (_^| ^| ^|  __/^| ^|  __/^>  ^<               ^|
echo  ^|    ^|_^|   \___^|_^|  ^|___/\___/^|_^| ^|_^|\__,_^| ^|_^|   ^|_^|\___/_/\_\              ^|
echo  ^|                                                                             ^|
echo  ^|                    WEB CLIENT BUILDER                                       ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM ================================================================================
REM Check for Node.js
REM ================================================================================
echo [*] Checking for Node.js...
where node >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo.
    echo  ===============================================================================
    echo   ERROR: Node.js is NOT installed!
    echo  ===============================================================================
    echo.
    echo   Node.js is required to build the web interface.
    echo.
    echo   Please install Node.js:
    echo     1. Download from: https://nodejs.org/
    echo     2. Choose the LTS version (recommended)
    echo     3. Run the installer and follow the prompts
    echo     4. IMPORTANT: Make sure "Add to PATH" is checked during installation
    echo     5. After installation, CLOSE and REOPEN this window
    echo     6. Run this script again
    echo.
    echo   Opening Node.js download page...
    start "" "https://nodejs.org/"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do (
    echo [OK] Node.js found: %%v
)

REM Check for npm
where npm >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [ERROR] npm not found! Please reinstall Node.js.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('npm --version 2^>^&1') do (
    echo [OK] npm found: %%v
)

REM ================================================================================
REM Check for client folder
REM ================================================================================
if not exist "client\package.json" (
    echo [ERROR] client/package.json not found!
    echo         Make sure you're running this from the PersonaPlex root folder.
    pause
    exit /b 1
)

echo [OK] Client folder found
echo.

REM ================================================================================
REM Build the client
REM ================================================================================
echo ================================================================================
echo  Building Web Client
echo ================================================================================
echo.

pushd client

REM Clean previous build if exists and user wants fresh build
if exist "dist" (
    echo [*] Previous build found.
    set /p "REBUILD=Do you want to rebuild? (y/n): "
    if /i "!REBUILD!"=="y" (
        echo [*] Removing previous build...
        rmdir /s /q dist 2>nul
    ) else (
        echo [OK] Using existing build
        popd
        goto build_done
    )
)

REM Install dependencies
echo [*] Installing dependencies (this may take a few minutes)...
echo.
call npm install
if !ERRORLEVEL! neq 0 (
    echo.
    echo [WARNING] npm install failed, trying with --legacy-peer-deps...
    call npm install --legacy-peer-deps
    if !ERRORLEVEL! neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies!
        echo         Please check the error messages above.
        popd
        pause
        exit /b 1
    )
)
echo.
echo [OK] Dependencies installed
echo.

REM Build
echo [*] Building web interface...
echo.
call npm run build
if !ERRORLEVEL! neq 0 (
    echo.
    echo [ERROR] Build failed!
    echo         Please check the error messages above.
    popd
    pause
    exit /b 1
)

popd

:build_done

REM Verify build
if exist "client\dist\index.html" (
    echo.
    echo ================================================================================
    echo  BUILD SUCCESSFUL!
    echo ================================================================================
    echo.
    echo  The web client has been built successfully!
    echo.
    echo  You can now run START_PERSONAPLEX.bat to launch the server
    echo  with the full web interface.
    echo.
    echo  Server URL: https://localhost:8998
    echo.
) else (
    echo.
    echo [ERROR] Build completed but dist/index.html was not created.
    echo         Please check for errors above.
)

echo.
echo  -----------------------------------------------------------------------
echo   Like this tool? Subscribe to SurAiverse for more AI tutorials!
echo   YouTube: https://www.youtube.com/@suraiverse
echo  -----------------------------------------------------------------------
echo.
pause
endlocal
