@echo off
setlocal EnableDelayedExpansion

REM PersonaPlex Server Launcher - Public Share (Gradio Tunnel)
REM Created by SurAiverse - https://www.youtube.com/@suraiverse

title PersonaPlex Server (Public Share) - by SurAiverse
color 0B

echo.
echo  ===============================================================================
echo  ^|                                                                             ^|
echo  ^|     ____                                    ____  _                         ^|
echo  ^|    ^|  _ \ ___ _ __ ___  ___  _ __   __ _  ^|  _ \^| ^| _____  __              ^|
echo  ^|    ^| ^|_) / _ \ '__/ __^|/ _ \^| '_ \ / _` ^| ^| ^|_) ^| ^|/ _ \ \/ /              ^|
echo  ^|    ^|  __/  __/ ^|  \__ \ (_) ^| ^| ^| ^| (_^| ^| ^|  __/^| ^|  __/^>  ^<               ^|
echo  ^|    ^|_^|   \___^|_^|  ^|___/\___/^|_^| ^|_^|\__,_^| ^|_^|   ^|_^|\___/_/\_\              ^|
echo  ^|                                                                             ^|
echo  ^|                SERVER LAUNCHER - PUBLIC SHARE (TUNNEL)                      ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.
echo  This mode creates a public shareable link using a Gradio tunnel.
echo  Anyone with the link can access the microphone-enabled UI.
echo.

REM Change to script directory
cd /d "%~dp0"

REM ================================================================================
REM Check virtual environment
REM ================================================================================
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found!
    echo.
    echo   Please run INSTALL_PERSONAPLEX.bat first.
    echo.
    set /p CONTINUE_ANYWAY="Continue with system Python? (y/n): "
    if /i not "!CONTINUE_ANYWAY!"=="y" (
        pause
        exit /b 1
    )
)

REM ================================================================================
REM Check Python
REM ================================================================================
python --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    py --version >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Python not found!
        pause
        exit /b 1
    )
)
echo [OK] Python available

REM ================================================================================
REM Check HuggingFace token
REM ================================================================================
if defined HF_TOKEN (
    echo [OK] HuggingFace token found
) else (
    python -c "from huggingface_hub.utils import HfFolder; t=HfFolder.get_token(); exit(0 if t else 1)" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [OK] HuggingFace cached login found
    ) else (
        echo [WARNING] HuggingFace token not set!
        echo           Run SETUP_HUGGINGFACE.bat to configure.
        timeout /t 2 >nul
    )
)

REM ================================================================================
REM Check and install gradio (required for tunnel)
REM ================================================================================
python -c "import gradio" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [*] Installing gradio for public tunnel support...
    python -m pip install gradio --quiet
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to install gradio!
        echo         Public share requires the gradio package.
        pause
        exit /b 1
    )
)
echo [OK] Gradio package available

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
set "PYTHONPATH=%~dp0moshi;%PYTHONPATH%"

REM ================================================================================
REM Check Web Client
REM ================================================================================
set "CLIENT_DIST=%~dp0client\dist"
if exist "%CLIENT_DIST%\index.html" (
    echo [OK] Pre-built web client found
    set "STATIC_PATH=%CLIENT_DIST%"
) else (
    echo [OK] Using server's embedded web client (no build required)
    set "STATIC_PATH=none"
)

REM Optional stable tunnel token
set "TUNNEL_TOKEN_ARG="
if defined PERSONAPLEX_TUNNEL_TOKEN (
    set "TUNNEL_TOKEN_ARG=--gradio-tunnel-token !PERSONAPLEX_TUNNEL_TOKEN!"
    echo [OK] Using PERSONAPLEX_TUNNEL_TOKEN for a stable share URL
)

echo.
echo ================================================================================
echo  Starting PersonaPlex Server (Public Share)
echo ================================================================================
echo.
echo  Public Link: will be printed after the server starts.
echo  Keep this window open to keep the link active.
echo.
echo  Press Ctrl+C to stop the server
echo.
echo ================================================================================
echo.

REM Launch server with public tunnel
if "!STATIC_PATH!"=="none" (
    python -m moshi.server --static none --gradio-tunnel !TUNNEL_TOKEN_ARG!
) else (
    python -m moshi.server --static "!STATIC_PATH!" --gradio-tunnel !TUNNEL_TOKEN_ARG!
)

REM Server stopped
echo.
echo ================================================================================
echo  Server stopped.
echo ================================================================================
echo.
echo  Subscribe to SurAiverse for AI tutorials: youtube.com/@suraiverse
echo.
pause
endlocal
