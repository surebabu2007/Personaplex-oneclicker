@echo off
setlocal EnableDelayedExpansion

REM PersonaPlex Interactive Launcher Menu
REM Created by SurAiverse - https://www.youtube.com/@suraiverse

title PersonaPlex Launcher - by SurAiverse
color 0B

:MENU
cls
echo.
echo  ===============================================================================
echo  ^|                                                                             ^|
echo  ^|     ____                                    ____  _                         ^|
echo  ^|    ^|  _ \ ___ _ __ ___  ___  _ __   __ _  ^|  _ \^| ^| _____  __              ^|
echo  ^|    ^| ^|_) / _ \ '__/ __^|/ _ \^| '_ \ / _` ^| ^| ^|_) ^| ^|/ _ \ \/ /              ^|
echo  ^|    ^|  __/  __/ ^|  \__ \ (_) ^| ^| ^| ^| (_^| ^| ^|  __/^| ^|  __/^>  ^<               ^|
echo  ^|    ^|_^|   \___^|_^|  ^|___/\___/^|_^| ^|_^|\__,_^| ^|_^|   ^|_^|\___/_/\_\              ^|
echo  ^|                                                                             ^|
echo  ^|                         LAUNCHER MENU                                       ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.
echo    Please select an option:
echo.
echo    -----------------------------------------------------------------------
echo    LAUNCH OPTIONS:
echo    -----------------------------------------------------------------------
echo    [1] Start PersonaPlex Server (Normal Mode - Recommended)
echo    [2] Start PersonaPlex Server (CPU Offload - For limited VRAM)
echo    [10] Start PersonaPlex Server (Public Share - Gradio Tunnel)
echo    [11] Start PersonaPlex Server (Public Share + CPU Offload)
echo.
echo    -----------------------------------------------------------------------
echo    INSTALLATION ^& SETUP:
echo    -----------------------------------------------------------------------
echo    [3] Run GUI Installer (Recommended for new users)
echo    [4] Run Console Installer
echo    [5] Fresh Install / Reset (Clean reinstall)
echo.
echo    -----------------------------------------------------------------------
echo    CONFIGURATION:
echo    -----------------------------------------------------------------------
echo    [6] Set Up HuggingFace Authentication
echo    [7] Download/Verify Models
echo    [8] Check Installation Status
echo.
echo    -----------------------------------------------------------------------
echo    OTHER:
echo    -----------------------------------------------------------------------
echo    [9] Open YouTube Tutorial (SurAiverse)
echo    [0] Exit
echo.
echo  ===============================================================================
echo.
set /p choice="   Enter your choice (0-11): "

if "%choice%"=="1" goto START_NORMAL
if "%choice%"=="2" goto START_CPU
if "%choice%"=="3" goto GUI_INSTALL
if "%choice%"=="4" goto CONSOLE_INSTALL
if "%choice%"=="5" goto FRESH_INSTALL
if "%choice%"=="6" goto SETUP_HF
if "%choice%"=="7" goto DOWNLOAD_MODELS
if "%choice%"=="8" goto CHECK_STATUS
if "%choice%"=="9" goto OPEN_YOUTUBE
if "%choice%"=="10" goto START_PUBLIC
if "%choice%"=="11" goto START_PUBLIC_CPU
if "%choice%"=="0" goto EXIT

echo.
echo    Invalid choice! Please enter a number between 0 and 11.
timeout /t 2 >nul
goto MENU

:START_NORMAL
cls
echo.
echo ================================================================================
echo  Starting PersonaPlex Server (Normal Mode)
echo ================================================================================
echo.
if exist "START_PERSONAPLEX.bat" (
    call "START_PERSONAPLEX.bat"
) else (
    echo [ERROR] START_PERSONAPLEX.bat not found!
    echo         Please run the installer first.
    pause
)
goto MENU

:START_CPU
cls
echo.
echo ================================================================================
echo  Starting PersonaPlex Server (CPU Offload Mode)
echo ================================================================================
echo.
if exist "START_PERSONAPLEX_CPU_OFFLOAD.bat" (
    call "START_PERSONAPLEX_CPU_OFFLOAD.bat"
) else (
    echo [ERROR] START_PERSONAPLEX_CPU_OFFLOAD.bat not found!
    pause
)
goto MENU

:START_PUBLIC
cls
echo.
echo ================================================================================
echo  Starting PersonaPlex Server (Public Share)
echo ================================================================================
echo.
if exist "START_PERSONAPLEX_PUBLIC.bat" (
    call "START_PERSONAPLEX_PUBLIC.bat"
) else (
    echo [ERROR] START_PERSONAPLEX_PUBLIC.bat not found!
    pause
)
goto MENU

:START_PUBLIC_CPU
cls
echo.
echo ================================================================================
echo  Starting PersonaPlex Server (Public Share + CPU Offload)
echo ================================================================================
echo.
if exist "START_PERSONAPLEX_PUBLIC_CPU_OFFLOAD.bat" (
    call "START_PERSONAPLEX_PUBLIC_CPU_OFFLOAD.bat"
) else (
    echo [ERROR] START_PERSONAPLEX_PUBLIC_CPU_OFFLOAD.bat not found!
    pause
)
goto MENU

:GUI_INSTALL
cls
echo.
echo ================================================================================
echo  Launching GUI Installer
echo ================================================================================
echo.
cd /d "%~dp0"

REM Find Python
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
    echo [ERROR] Python not found! Please install Python 3.10+ first.
    pause
    goto MENU
)

REM Check for tkinter
!PYTHON_CMD! -c "import tkinter" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [WARNING] tkinter not available. Falling back to console installer.
    pause
    goto CONSOLE_INSTALL
)

if exist "installer_gui.py" (
    echo [*] Starting GUI installer...
    !PYTHON_CMD! installer_gui.py
) else (
    echo [ERROR] installer_gui.py not found!
    echo         Falling back to console installer...
    pause
    goto CONSOLE_INSTALL
)
goto MENU

:CONSOLE_INSTALL
cls
echo.
echo ================================================================================
echo  Running Console Installer
echo ================================================================================
echo.
cd /d "%~dp0"
if exist "INSTALL_PERSONAPLEX.bat" (
    call INSTALL_PERSONAPLEX.bat --console
) else (
    echo [ERROR] INSTALL_PERSONAPLEX.bat not found!
    pause
)
goto MENU

:FRESH_INSTALL
cls
echo.
echo ================================================================================
echo  Fresh Install / Reset
echo ================================================================================
echo.
echo  WARNING: This will:
echo    - Remove the existing virtual environment
echo    - Clear cached Python files
echo    - Perform a clean reinstallation
echo.
echo  Your HuggingFace token and downloaded models will be preserved.
echo.
set /p confirm="Are you sure you want to proceed? (y/n): "
if /i not "%confirm%"=="y" (
    echo.
    echo  Fresh install cancelled.
    timeout /t 2 >nul
    goto MENU
)

echo.
echo [*] Cleaning up existing installation...

REM Remove venv
if exist "venv" (
    echo [*] Removing virtual environment...
    rmdir /s /q venv 2>nul
    if exist "venv" (
        echo [WARNING] Could not fully remove venv. Please close any programs using it.
        echo           Retrying...
        timeout /t 3 >nul
        rmdir /s /q venv 2>nul
    )
    echo [OK] Virtual environment removed
)

REM Remove __pycache__
echo [*] Cleaning up Python cache files...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" 2>nul
)

REM Remove .pyc files
del /s /q *.pyc 2>nul

echo [OK] Cleanup complete
echo.
echo [*] Starting fresh installation...
timeout /t 2 >nul

cd /d "%~dp0"
if exist "INSTALL_PERSONAPLEX.bat" (
    call INSTALL_PERSONAPLEX.bat --fresh
) else (
    echo [ERROR] INSTALL_PERSONAPLEX.bat not found!
    pause
)
goto MENU

:CHECK_STATUS
cls
echo.
echo ================================================================================
echo  Installation Status Check
echo ================================================================================
echo.
cd /d "%~dp0"

REM Find Python
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
    pause
    goto MENU
)

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

if exist "verify_project.py" (
    python verify_project.py
) else if exist "installer_utils.py" (
    python installer_utils.py
) else (
    echo [INFO] Running basic checks...
    echo.
    python --version
    echo.
    python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')" 2>nul
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] PyTorch not installed or not working
    )
    echo.
    python -c "import moshi; print('[OK] moshi package installed')" 2>nul
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] moshi package not installed
    )
)
echo.
echo ================================================================================
pause
goto MENU

:SETUP_HF
cls
echo.
echo ================================================================================
echo  HuggingFace Authentication Setup
echo ================================================================================
echo.
cd /d "%~dp0"
if exist "SETUP_HUGGINGFACE.bat" (
    call "SETUP_HUGGINGFACE.bat"
) else (
    echo [INFO] Running manual HuggingFace setup...
    echo.
    echo  To set up HuggingFace authentication:
    echo.
    echo  1. Visit: https://huggingface.co/settings/tokens
    echo  2. Create a new token (Read access is sufficient)
    echo  3. Accept the model license at:
echo     https://huggingface.co/nvidia/personaplex-7b-v1
    echo.
    echo  4. Set your token:
    echo.
    set /p token="     Enter your HuggingFace token: "
    if not "!token!"=="" (
        setx HF_TOKEN "!token!" >nul 2>&1
        set "HF_TOKEN=!token!"
        echo.
        echo [OK] Token saved!
    )
    pause
)
goto MENU

:DOWNLOAD_MODELS
cls
echo.
echo ================================================================================
echo  Download/Verify Models
echo ================================================================================
echo.
cd /d "%~dp0"

REM Activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

if exist "verify_and_download_models.py" (
    python verify_and_download_models.py
    if !ERRORLEVEL! neq 0 (
        echo.
        echo [WARNING] Some issues occurred. Check the output above.
    )
) else if exist "model_manager.py" (
    python model_manager.py --status
    echo.
    set /p download="Download missing models? (y/n): "
    if /i "!download!"=="y" (
        python model_manager.py --download
    )
) else (
    echo [ERROR] Model verification scripts not found!
)
echo.
pause
goto MENU

:OPEN_YOUTUBE
echo.
echo  Opening SurAiverse YouTube channel...
start "" "https://www.youtube.com/@suraiverse"
timeout /t 2 >nul
goto MENU

:EXIT
cls
echo.
echo ================================================================================
echo.
echo   Thank you for using PersonaPlex!
echo.
echo   Subscribe to SurAiverse for more AI tutorials:
echo   https://www.youtube.com/@suraiverse
echo.
echo   By: Suresh Pydikondala
echo.
echo ================================================================================
echo.
timeout /t 3 >nul
exit

endlocal
