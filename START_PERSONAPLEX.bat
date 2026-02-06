@echo off
setlocal EnableDelayedExpansion

REM PersonaPlex Server Launcher - Normal Mode
REM Created by SurAiverse - https://www.youtube.com/@suraiverse

title PersonaPlex Server - by SurAiverse
color 0A

echo.
echo  ===============================================================================
echo  ^|                                                                             ^|
echo  ^|     ____                                    ____  _                         ^|
echo  ^|    ^|  _ \ ___ _ __ ___  ___  _ __   __ _  ^|  _ \^| ^| _____  __              ^|
echo  ^|    ^| ^|_) / _ \ '__/ __^|/ _ \^| '_ \ / _` ^| ^| ^|_) ^| ^|/ _ \ \/ /              ^|
echo  ^|    ^|  __/  __/ ^|  \__ \ (_) ^| ^| ^| ^| (_^| ^| ^|  __/^| ^|  __/^>  ^<               ^|
echo  ^|    ^|_^|   \___^|_^|  ^|___/\___/^|_^| ^|_^|\__,_^| ^|_^|   ^|_^|\___/_/\_\              ^|
echo  ^|                                                                             ^|
echo  ^|                      SERVER LAUNCHER                                        ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.

REM Change to script directory and store path
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM ================================================================================
REM Check Python Environment (venv preferred)
REM ================================================================================
set "PYTHON_CMD="

REM Check for virtual environment (recommended)
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    call venv\Scripts\activate.bat
    set "PYTHON_CMD=venv\Scripts\python.exe"
    goto :python_ready
)

REM No venv found - check if installer was run
echo.
echo  ===============================================================================
echo  ^|                    VIRTUAL ENVIRONMENT NOT FOUND                            ^|
echo  ===============================================================================
echo.
echo   [ERROR] The virtual environment has not been created yet!
echo.
echo   This means the installation was not completed. Please:
echo.
echo     1. Close this window
echo     2. Run INSTALL_PERSONAPLEX.bat or the GUI installer (installer_gui.py)
echo     3. Complete the full installation process
echo     4. Then try launching PersonaPlex again
echo.
echo   If you already ran the installer and still see this error:
echo     - Check if antivirus software blocked the venv creation
echo     - Try running the installer as Administrator
echo     - Make sure you have enough disk space
echo.

REM Check if system Python exists as fallback
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo   [INFO] System Python found. You can continue with system Python,
    echo          but this is NOT recommended as dependencies may be missing.
    echo.
    set /p "USE_SYSTEM=Continue with system Python anyway? (y/n): "
    if /i "!USE_SYSTEM!"=="y" (
        set "PYTHON_CMD=python"
        echo.
        echo   [WARNING] Using system Python - some features may not work!
        echo.
        timeout /t 3 >nul
        goto :python_ready
    )
)

echo.
echo   Please run INSTALL_PERSONAPLEX.bat to set up the environment.
echo.
echo   Press any key to exit...
pause >nul
exit /b 1

:python_ready
echo [OK] Python ready

REM ================================================================================
REM Check HuggingFace token
REM ================================================================================
if defined HF_TOKEN (
    echo [OK] HuggingFace token found
) else (
    REM Try to get from huggingface cache
    "!PYTHON_CMD!" -c "from huggingface_hub.utils import HfFolder; t=HfFolder.get_token(); exit(0 if t else 1)" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [OK] HuggingFace cached login found
    ) else (
        echo [WARNING] HuggingFace token not set!
        echo.
        echo   Models may fail to download. To fix:
        echo   1. Run SETUP_HUGGINGFACE.bat
        echo   2. Or set: setx HF_TOKEN "your_token_here"
        echo.
        echo   Get your token at: https://huggingface.co/settings/tokens
        echo.
        timeout /t 3 >nul
    )
)

REM ================================================================================
REM Check Network Connectivity (for model downloads)
REM ================================================================================
echo [*] Checking network connectivity...
ping -n 1 huggingface.co >nul 2>&1
if !ERRORLEVEL! neq 0 (
    ping -n 1 8.8.8.8 >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] No network connectivity detected!
        echo           Models may fail to download if not already cached.
        echo.
        echo   If you're behind a corporate firewall or VPN:
        echo     - Check if huggingface.co is accessible
        echo     - Try disabling VPN temporarily
        echo     - Check Windows Firewall settings
        echo.
        timeout /t 3 >nul
    ) else (
        echo [WARNING] Cannot reach huggingface.co directly.
        echo           Model downloads may fail. Check firewall settings.
        timeout /t 2 >nul
    )
) else (
    echo [OK] Network connectivity confirmed
)

REM ================================================================================
REM Configure environment
REM ================================================================================

REM Disable torch.compile (Triton not available on Windows)
set TORCHDYNAMO_DISABLE=1
echo [OK] Torch compile disabled for Windows

REM Help with CUDA memory fragmentation
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo [OK] CUDA memory optimization enabled

REM Add moshi directory to PYTHONPATH
set "PYTHONPATH=%SCRIPT_DIR%moshi;%PYTHONPATH%"

REM ================================================================================
REM Check Web Client (Node.js NOT required - server has embedded client)
REM ================================================================================
set "CLIENT_DIST=%SCRIPT_DIR%client\dist"
if exist "%CLIENT_DIST%\index.html" (
    echo [OK] Pre-built web client found
    set "STATIC_PATH=%CLIENT_DIST%"
) else (
    echo [OK] Using server's embedded web client (no build required)
    set "STATIC_PATH=none"
)

echo.
echo ================================================================================
echo  Starting PersonaPlex Server
echo ================================================================================
echo.
echo  Server URL: https://localhost:8998
echo.
if "!STATIC_PATH!"=="none" (
    echo  MODE: Embedded Web UI
    echo        The server includes a built-in web interface.
    echo        Just open the URL above in your browser.
) else (
    echo  MODE: Custom Web UI ^(from client/dist^)
    echo        Using pre-built client files.
)
echo.
echo  IMPORTANT: Your browser may show a security warning because
echo  we use a self-signed certificate. This is normal and safe.
echo  Click "Advanced" and "Proceed" to continue.
echo.
echo  Press Ctrl+C to stop the server
echo.
echo ================================================================================
echo.

REM Create temporary SSL directory
echo [*] Creating SSL directory...
for /f "tokens=*" %%i in ('powershell -Command "$temp = [System.IO.Path]::GetTempPath(); $dir = Join-Path $temp ('personaplex_ssl_' + [System.Guid]::NewGuid().ToString()); New-Item -ItemType Directory -Path $dir -Force | Out-Null; Write-Output $dir"') do set SSL_DIR=%%i

if "!SSL_DIR!"=="" (
    echo [ERROR] Failed to create SSL directory!
    echo         This may be due to permission issues or disk space.
    echo.
    echo  Press any key to exit...
    pause >nul
    exit /b 1
)
echo [OK] SSL directory: !SSL_DIR!

REM Launch server
echo [*] Starting Python server...
echo.

if "!STATIC_PATH!"=="none" (
    "!PYTHON_CMD!" -m moshi.server --ssl "!SSL_DIR!" --static none --voice-prompt-dir "%SCRIPT_DIR%voices"
) else (
    "!PYTHON_CMD!" -m moshi.server --ssl "!SSL_DIR!" --static "!STATIC_PATH!" --voice-prompt-dir "%SCRIPT_DIR%voices"
)

set SERVER_EXIT_CODE=!ERRORLEVEL!

REM Server stopped or crashed
echo.
echo ================================================================================

if !SERVER_EXIT_CODE! neq 0 (
    echo  [ERROR] Server exited with error code: !SERVER_EXIT_CODE!
    echo ================================================================================
    echo.
    echo  TROUBLESHOOTING TIPS:
    echo.
    echo  1. CUDA/GPU Memory Issues:
    echo     - Close other GPU applications (games, browsers with GPU acceleration)
    echo     - Try CPU offload mode: START_PERSONAPLEX_CPU_OFFLOAD.bat
    echo.
    echo  2. Missing Models:
    echo     - Run: python verify_and_download_models.py
    echo     - Make sure you have a valid HuggingFace token
    echo.
    echo  3. Port Already in Use:
    echo     - Another application may be using port 8998
    echo     - Close any other servers or restart your computer
    echo.
    echo  4. Network/SSL Issues:
    echo     - Check your firewall settings
    echo     - Allow Python through Windows Firewall
    echo     - Try disabling VPN if you're using one
    echo.
    echo  5. Missing Dependencies:
    echo     - Re-run INSTALL_PERSONAPLEX.bat
    echo     - Check for antivirus blocking downloads
    echo.
) else (
    echo  Server stopped normally.
    echo ================================================================================
)

echo.
echo  Subscribe to SurAiverse for AI tutorials: youtube.com/@suraiverse
echo.
echo  Press any key to close this window...
pause >nul
endlocal
