@echo off
setlocal EnableDelayedExpansion

REM PersonaPlex Status Check
REM Created by SurAiverse - https://www.youtube.com/@suraiverse

title PersonaPlex Status Check - by SurAiverse
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
echo  ^|                    INSTALLATION STATUS CHECK                                ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM ================================================================================
REM Find Python
REM ================================================================================
set "PYTHON_CMD="
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_CMD=py"
    )
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] Python not found!
    echo.
    echo   Please install Python 3.10 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM ================================================================================
REM Activate venv if available
REM ================================================================================
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [INFO] No virtual environment found (using system Python)
)

echo.
echo ================================================================================
echo  Running Status Checks
echo ================================================================================

REM Run verification script if available
if exist "verify_project.py" (
    python verify_project.py
) else if exist "installer_utils.py" (
    python installer_utils.py
) else (
    REM Fallback to basic checks
    echo.
    echo [*] Python Version:
    python --version
    
    echo.
    echo [*] PyTorch Status:
    python -c "import torch; print(f'   Version: {torch.__version__}'); print(f'   CUDA Available: {torch.cuda.is_available()}'); print(f'   CUDA Version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'   GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>nul
    if !ERRORLEVEL! neq 0 (
        echo    [WARNING] PyTorch not installed or not working
    )
    
    echo.
    echo [*] Moshi Package:
    python -c "import moshi; print('   [OK] moshi package installed')" 2>nul
    if !ERRORLEVEL! neq 0 (
        echo    [WARNING] moshi package not installed
    )
    
    echo.
    echo [*] HuggingFace Token:
    if defined HF_TOKEN (
        echo    [OK] HF_TOKEN environment variable is set
    ) else (
        python -c "from huggingface_hub.utils import HfFolder; t=HfFolder.get_token(); print('   [OK] Cached token found' if t else '   [WARNING] No token found')" 2>nul
    )
    
    echo.
    echo [*] Virtual Environment:
    if exist "venv\Scripts\activate.bat" (
        echo    [OK] Virtual environment exists
    ) else (
        echo    [WARNING] Virtual environment not found
    )
)

echo.
echo ================================================================================
echo  Quick Links
echo ================================================================================
echo.
echo  - HuggingFace Token: https://huggingface.co/settings/tokens
echo  - Model License: https://huggingface.co/nvidia/personaplex-7b-v1
echo  - SurAiverse YouTube: https://www.youtube.com/@suraiverse
echo.
echo ================================================================================
echo.
pause
endlocal
