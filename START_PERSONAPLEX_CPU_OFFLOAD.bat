@echo off
setlocal EnableDelayedExpansion

REM PersonaPlex Server Launcher - CPU Offload Mode
REM For systems with limited VRAM
REM Created by SurAiverse - https://www.youtube.com/@suraiverse

title PersonaPlex Server (CPU Offload) - by SurAiverse
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
echo  ^|                  SERVER LAUNCHER - CPU OFFLOAD MODE                         ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.
echo  CPU Offload Mode: Uses less VRAM by moving some layers to CPU
echo  Use this if you have a GPU with less than 12GB VRAM
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
REM Check and install accelerate
REM ================================================================================
python -c "import accelerate" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [*] Installing accelerate package for CPU offload...
    python -m pip install accelerate --quiet
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to install accelerate!
        echo         CPU offload requires the accelerate package.
        pause
        exit /b 1
    )
)
echo [OK] Accelerate package available

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
REM Check/Build Web Client
REM ================================================================================
if exist "client\dist\index.html" (
    echo [OK] Web client found
    set "STATIC_PATH=%~dp0client\dist"
) else (
    echo [*] Web client not built, checking for Node.js...
    where node >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [OK] Node.js found, building web client...
        pushd client
        call npm install --silent 2>nul
        call npm run build --silent 2>nul
        popd
        if exist "client\dist\index.html" (
            echo [OK] Web client built successfully
            set "STATIC_PATH=%~dp0client\dist"
        ) else (
            echo [WARNING] Could not build web client
            echo           Server will run in API-only mode
            set "STATIC_PATH=none"
        )
    ) else (
        echo [INFO] Node.js not found - server will run in API-only mode
        echo        To enable web UI, install Node.js and run:
        echo          cd client ^&^& npm install ^&^& npm run build
        set "STATIC_PATH=none"
    )
)

echo.
echo ================================================================================
echo  Starting PersonaPlex Server (CPU Offload Mode)
echo ================================================================================
echo.
echo  Server URL: https://localhost:8998
echo.
echo  NOTE: CPU Offload mode may be slower but uses less GPU memory.
echo  Model layers will be distributed between GPU and CPU.
echo.
echo  Press Ctrl+C to stop the server
echo.
echo ================================================================================
echo.

REM Create temporary SSL directory
for /f "tokens=*" %%i in ('powershell -Command "$temp = [System.IO.Path]::GetTempPath(); $dir = Join-Path $temp ('personaplex_ssl_' + [System.Guid]::NewGuid().ToString()); New-Item -ItemType Directory -Path $dir -Force | Out-Null; Write-Output $dir"') do set SSL_DIR=%%i

REM Launch server with CPU offload
if "!STATIC_PATH!"=="none" (
    python -m moshi.server --ssl "%SSL_DIR%" --static none --cpu-offload
) else (
    python -m moshi.server --ssl "%SSL_DIR%" --static "!STATIC_PATH!" --cpu-offload
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
