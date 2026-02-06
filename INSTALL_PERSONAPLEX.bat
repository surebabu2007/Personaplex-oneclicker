@echo off
setlocal EnableDelayedExpansion

REM ================================================================================
REM PersonaPlex One-Click Installer for Windows
REM This script launches the GUI installer or falls back to console mode
REM Created by SurAiverse - https://www.youtube.com/@suraiverse
REM ================================================================================

title PersonaPlex - One-Click Installer by SurAiverse
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
echo  ^|                    ONE-CLICK INSTALLER FOR WINDOWS                          ^|
echo  ^|                                                                             ^|
echo  ^|         Installer by: Suresh Pydikondala (SurAiverse)                       ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM ================================================================================
REM Check for Python
REM ================================================================================
echo [*] Checking for Python...

set "PYTHON_CMD="

REM Check for Python in PATH
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
    set "PYTHON_CMD=python"
    goto :check_python_version
)

where py >nul 2>&1
if !ERRORLEVEL! equ 0 (
    set "PYTHON_CMD=py"
    goto :check_python_version
)

REM Python not found - show helpful message
echo.
echo  ===============================================================================
echo   Python Not Found
echo  ===============================================================================
echo.
echo   Python 3.10 or higher is required to run PersonaPlex.
echo.
echo   Please install Python from:
echo     https://www.python.org/downloads/
echo.
echo   IMPORTANT during installation:
echo     [x] Check "Add Python to PATH" (at the bottom of installer)
echo.
echo   After installing Python:
echo     1. CLOSE this window
echo     2. Run INSTALL_PERSONAPLEX.bat again
echo.
set /p "OPEN_PYTHON_PAGE=Open Python download page now? (y/n): "
if /i "!OPEN_PYTHON_PAGE!"=="y" (
    start "" "https://www.python.org/downloads/"
)
echo.
pause
exit /b 1

:check_python_version
REM Get and display Python version
for /f "tokens=2" %%i in ('!PYTHON_CMD! --version 2^>^&1') do set "PYTHON_VERSION=%%i"

REM Extract major.minor version
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set "PYTHON_MAJOR=%%a"
    set "PYTHON_MINOR=%%b"
)

REM Check if version is sufficient
if !PYTHON_MAJOR! LSS 3 goto :python_version_error
if !PYTHON_MAJOR! EQU 3 if !PYTHON_MINOR! LSS 10 goto :python_version_error

echo [OK] Python !PYTHON_VERSION! found
goto :python_found

:python_version_error
echo.
echo  ===============================================================================
echo   Python Version Too Old
echo  ===============================================================================
echo.
echo   Found: Python !PYTHON_VERSION!
echo   Required: Python 3.10 or higher
echo.
echo   Please download the latest Python from:
echo     https://www.python.org/downloads/
echo.
echo   IMPORTANT during installation:
echo     [x] Check "Add Python to PATH"
echo     [x] Select "Install for all users" (recommended)
echo.
set /p "OPEN_PYTHON_PAGE=Open Python download page now? (y/n): "
if /i "!OPEN_PYTHON_PAGE!"=="y" (
    start "" "https://www.python.org/downloads/"
)
echo.
pause
exit /b 1

:python_found

REM ================================================================================
REM Check for installation mode argument
REM ================================================================================
set "INSTALL_MODE="
if "%~1"=="--console" set "INSTALL_MODE=console"
if "%~1"=="--fresh" set "INSTALL_MODE=fresh"
if "%~1"=="--reset" set "INSTALL_MODE=fresh"
if "%~1"=="--gui" set "INSTALL_MODE=gui"

REM ================================================================================
REM Try to launch GUI installer
REM ================================================================================
if not "!INSTALL_MODE!"=="console" (
    echo.
    echo [*] Launching graphical installer...
    
    REM Check if tkinter is available
    !PYTHON_CMD! -c "import tkinter" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        if exist "installer_gui.py" (
            echo [OK] Starting GUI installer...
            echo.
            !PYTHON_CMD! installer_gui.py
            if !ERRORLEVEL! equ 0 (
                exit /b 0
            ) else (
                echo [WARNING] GUI installer exited with error, falling back to console mode...
            )
        ) else (
            echo [WARNING] installer_gui.py not found, using console mode...
        )
    ) else (
        echo [WARNING] tkinter not available, using console mode...
    )
)

REM ================================================================================
REM Console Mode Installation
REM ================================================================================
echo.
echo ================================================================================
echo  Console Mode Installation
echo ================================================================================
echo.

REM Check for fresh install/reset request
if "!INSTALL_MODE!"=="fresh" (
    echo [*] Fresh install requested - cleaning up existing installation...
    if exist "venv" (
        echo [*] Removing existing virtual environment...
        rmdir /s /q venv 2>nul
        if exist "venv" (
            echo [WARNING] Could not fully remove venv folder. Please close any programs using it.
            timeout /t 3 >nul
            rmdir /s /q venv 2>nul
        )
    )
    echo [OK] Cleanup complete
    echo.
)

echo  This installer will:
echo    1. Check system requirements (Python, Node.js, NVIDIA GPU)
echo    2. Create a virtual environment
echo    3. Install all dependencies
echo    4. Build the web interface (client)
echo    5. Set up HuggingFace authentication
echo    6. Download/configure AI models
echo    7. Launch PersonaPlex
echo.
echo  Press any key to begin installation...
pause >nul

REM ================================================================================
REM STEP 1: System Requirements
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 1: Checking System Requirements
echo ================================================================================
echo.

REM Check for NVIDIA GPU
echo [*] Checking for NVIDIA GPU...
where nvidia-smi >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [WARNING] nvidia-smi not found. NVIDIA drivers may not be installed.
    echo           PersonaPlex requires an NVIDIA GPU with CUDA support.
    echo           CPU-only mode is available but slower.
    echo.
    set /p "CONTINUE_ANYWAY=Continue anyway? (y/n): "
    if /i not "!CONTINUE_ANYWAY!"=="y" (
        pause
        exit /b 1
    )
) else (
    nvidia-smi --query-gpu=name --format=csv,noheader >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "tokens=*" %%g in ('nvidia-smi --query-gpu=name --format=csv,noheader') do (
            echo [OK] NVIDIA GPU detected: %%g
        )
    ) else (
        echo [WARNING] Could not query GPU info
    )
)

REM Check for Node.js
echo [*] Checking for Node.js...
where node >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [WARNING] Node.js is not installed or not in PATH!
    echo           Node.js is required to build the web interface.
    echo           Please install from: https://nodejs.org/
    echo.
    set /p "CONTINUE_NO_NODE=Continue anyway? Web UI build will be skipped. (y/n): "
    if /i not "!CONTINUE_NO_NODE!"=="y" (
        pause
        exit /b 1
    )
    set "SKIP_CLIENT_BUILD=1"
) else (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do (
        echo [OK] Node.js found: %%v
    )
    set "SKIP_CLIENT_BUILD=0"
)

REM Check disk space
echo [*] Checking disk space...
for /f "tokens=3" %%a in ('dir /-c 2^>nul ^| findstr /c:"bytes free"') do (
    set "FREE_BYTES=%%a"
)
echo [OK] Disk space check complete

REM ================================================================================
REM STEP 2: Virtual Environment (Clean venv approach)
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 2: Setting Up Virtual Environment
echo ================================================================================
echo.

REM Check for existing venv
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment already exists
    set /p "USE_EXISTING=Use existing environment? (y/n): "
    if /i "!USE_EXISTING!"=="n" (
        echo [*] Removing old virtual environment...
        rmdir /s /q venv 2>nul
        timeout /t 2 >nul
        rmdir /s /q venv 2>nul
    ) else (
        goto :activate_venv
    )
)

REM Create virtual environment using Python's built-in venv
echo [*] Creating virtual environment...
!PYTHON_CMD! -m venv venv

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Failed to create virtual environment!
    echo         Make sure you have write permissions to this folder.
    pause
    exit /b 1
)

:activate_venv
echo [OK] Virtual environment created

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Set the Python command to use venv
set "VENV_PYTHON=venv\Scripts\python.exe"
set "VENV_PIP=venv\Scripts\pip.exe"

echo [OK] Virtual environment ready (clean isolated environment)

REM ================================================================================
REM STEP 3: Install Dependencies
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 3: Installing Dependencies
echo ================================================================================
echo.

REM Upgrade pip
echo [*] Upgrading pip...
!VENV_PYTHON! -m pip install --upgrade pip --quiet

REM Uninstall existing PyTorch to avoid conflicts
echo [*] Removing any existing PyTorch installation...
!VENV_PYTHON! -m pip uninstall torch torchvision torchaudio -y --quiet 2>nul

REM Install PyTorch with CUDA
echo [*] Installing PyTorch 2.4 with CUDA support...
echo     (This may take a few minutes)
!VENV_PYTHON! -m pip install "torch>=2.4.0,<2.5" "torchvision>=0.19,<0.20" "torchaudio>=2.4,<2.5" --index-url https://download.pytorch.org/whl/cu124 --quiet
if !ERRORLEVEL! neq 0 (
    echo [WARNING] Failed to install PyTorch with CUDA 12.4, trying CUDA 11.8...
    !VENV_PYTHON! -m pip install "torch>=2.4.0,<2.5" "torchvision>=0.19,<0.20" "torchaudio>=2.4,<2.5" --index-url https://download.pytorch.org/whl/cu118 --quiet
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] Trying default PyTorch installation...
        !VENV_PYTHON! -m pip install "torch>=2.4.0,<2.5" "torchvision>=0.19,<0.20" "torchaudio>=2.4,<2.5" --quiet
    )
)
echo [OK] PyTorch installed

REM Install moshi package
echo [*] Installing PersonaPlex (moshi package)...
!VENV_PYTHON! -m pip install moshi/. --quiet
if !ERRORLEVEL! neq 0 (
    echo [WARNING] Retrying moshi installation with verbose output...
    !VENV_PYTHON! -m pip install moshi/.
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to install moshi package!
        echo         Please check the error messages above.
        pause
        exit /b 1
    )
)
echo [OK] PersonaPlex (moshi) installed

REM Install accelerate for CPU offload support
echo [*] Installing accelerate (for CPU offload support)...
!VENV_PYTHON! -m pip install accelerate --quiet
echo [OK] Accelerate installed

REM Verify installation
echo [*] Verifying installation...
!VENV_PYTHON! -c "import moshi; import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
if !ERRORLEVEL! neq 0 (
    echo [WARNING] Installation verification had issues, but continuing...
) else (
    echo [OK] Installation verified
)

REM ================================================================================
REM STEP 4: Build Web Interface (Client)
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 4: Building Web Interface
echo ================================================================================
echo.

if "!SKIP_CLIENT_BUILD!"=="1" (
    echo [SKIP] Skipping client build - Node.js not available
    echo.
    echo  -----------------------------------------------------------------------
    echo   The web UI requires Node.js to build.
    echo   Server will show a status page instead of the full web interface.
    echo.
    echo   To enable the full web UI later:
    echo     1. Install Node.js from: https://nodejs.org/
    echo     2. Run: cd client ^&^& npm install ^&^& npm run build
    echo     3. Restart the server
    echo  -----------------------------------------------------------------------
    echo.
    goto skip_client_build
)

if exist "client\package.json" (
    echo [*] Found client/package.json
    echo [*] Installing client dependencies (this may take a few minutes)...
    pushd client
    
    REM Clean install for fresh builds
    if exist "node_modules" (
        echo [*] Using existing node_modules...
    )
    
    call npm install
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] npm install failed!
        echo           Trying with legacy peer deps...
        call npm install --legacy-peer-deps
        if !ERRORLEVEL! neq 0 (
            echo [ERROR] Failed to install client dependencies.
            echo         The server will run in API-only mode.
            popd
            goto skip_client_build
        )
    )
    echo [OK] Client dependencies installed
    
    echo [*] Building web interface...
    call npm run build
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] Client build failed.
        echo          The server will run in API-only mode with a status page.
        popd
        goto skip_client_build
    )
    
    REM Verify the build succeeded
    if exist "dist\index.html" (
        echo [OK] Web interface built successfully!
        echo [OK] Client dist folder ready at: client\dist
    ) else (
        echo [WARNING] Build completed but dist/index.html not found.
        echo          The server will run in API-only mode.
    )
    popd
) else (
    echo [WARNING] client/package.json not found
    echo          The server will run in API-only mode.
)

:skip_client_build

REM ================================================================================
REM STEP 5: HuggingFace Authentication
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 5: HuggingFace Authentication Setup
echo ================================================================================
echo.

REM Check if HF_TOKEN is already set
if defined HF_TOKEN (
    echo [OK] HF_TOKEN is already set
    goto skip_hf_setup
)

REM Check if huggingface-cli is logged in
!VENV_PYTHON! -c "from huggingface_hub import HfApi; api = HfApi(); print(api.whoami()['name'])" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Already logged in to HuggingFace
    goto skip_hf_setup
)

echo.
echo  ===============================================================================
echo   HuggingFace Token Required
echo  ===============================================================================
echo.
echo   You need a HuggingFace account and token to download the models.
echo.
echo   BEFORE CONTINUING, please:
echo     1. Create an account at: https://huggingface.co/join
echo     2. Accept the model license (IMPORTANT!):
echo        - https://huggingface.co/nvidia/personaplex-7b-v1
echo     3. Get your token from: https://huggingface.co/settings/tokens
echo.
echo   Opening the license page in your browser...
start "" "https://huggingface.co/nvidia/personaplex-7b-v1"
timeout /t 3 >nul

:enter_token
echo.
set "HF_TOKEN_INPUT="
set /p "HF_TOKEN_INPUT=Enter your HuggingFace token (starts with hf_): "

if "!HF_TOKEN_INPUT!"=="" (
    echo [ERROR] No token provided!
    set /p "TRY_AGAIN=Try again? (y/n): "
    if /i "!TRY_AGAIN!"=="y" goto enter_token
    echo [WARNING] Continuing without token. Model downloads may fail.
    goto skip_hf_setup
)

REM Validate token format
echo !HF_TOKEN_INPUT! | findstr /b "hf_" >nul
if !ERRORLEVEL! neq 0 (
    echo [WARNING] Token doesn't start with 'hf_'. This may not be a valid token.
    set /p "USE_ANYWAY=Use it anyway? (y/n): "
    if /i not "!USE_ANYWAY!"=="y" goto enter_token
)

REM Set token for current session
set "HF_TOKEN=!HF_TOKEN_INPUT!"

REM Ask to save permanently
echo.
set /p "SAVE_TOKEN=Save token permanently for future sessions? (y/n): "
if /i "!SAVE_TOKEN!"=="y" (
    setx HF_TOKEN "!HF_TOKEN_INPUT!" >nul 2>&1
    echo [OK] Token saved permanently
) else (
    echo [OK] Token set for this session only
)

:skip_hf_setup

REM ================================================================================
REM STEP 6: Download/Verify Models
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 6: Model Configuration
echo ================================================================================
echo.

echo  Would you like to:
echo    [1] Download models from HuggingFace (recommended, ~14GB)
echo    [2] Use existing models from a local folder
echo    [3] Skip - models will download on first run
echo.
set /p "MODEL_CHOICE=Enter choice (1-3): "

if "!MODEL_CHOICE!"=="1" (
    echo.
    echo [*] Downloading models from HuggingFace...
    echo     This may take 30-60 minutes depending on your internet speed.
    echo.
    if exist "verify_and_download_models.py" (
        !VENV_PYTHON! verify_and_download_models.py
    ) else if exist "model_manager.py" (
        !VENV_PYTHON! model_manager.py --download
    ) else (
        echo [INFO] Model download script not found.
        echo        Models will be downloaded automatically on first server launch.
    )
    
    REM Download voice prompts from nvidia/personaplex-7b-v1
    echo.
    echo [*] Downloading voice prompts from nvidia/personaplex-7b-v1...
    echo     This contains 18 different voice options for the AI.
    !VENV_PYTHON! -c "from huggingface_hub import hf_hub_download; import tarfile; from pathlib import Path; voices_tgz = hf_hub_download('nvidia/personaplex-7b-v1', 'voices.tgz'); voices_tgz = Path(voices_tgz); voices_dir = voices_tgz.parent / 'voices'; voices_dir.mkdir(exist_ok=True) if not voices_dir.exists() else None; tarfile.open(voices_tgz, 'r:gz').extractall(path=voices_dir) if not (voices_dir / 'NATF0.pt').exists() else print('Voices already extracted'); print(f'Voice prompts ready at: {voices_dir}')"
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] Failed to download voice prompts.
        echo          Voice options may not work correctly.
        echo          Make sure you accepted the nvidia/personaplex-7b-v1 license.
    ) else (
        echo [OK] Voice prompts downloaded and extracted
    )
)

if "!MODEL_CHOICE!"=="2" (
    echo.
    set /p "MODEL_PATH=Enter path to folder containing model files: "
    if exist "model_manager.py" (
        !VENV_PYTHON! model_manager.py --set-path "!MODEL_PATH!"
    ) else (
        echo [INFO] Custom model path configured: !MODEL_PATH!
        echo {"custom_model_path": "!MODEL_PATH!"} > model_config.json
    )
)

REM ================================================================================
REM STEP 7: Installation Complete
REM ================================================================================
echo.
echo ================================================================================
echo  STEP 7: Installation Complete!
echo ================================================================================
echo.
echo  PersonaPlex has been successfully installed!
echo.
echo  To start PersonaPlex:
echo    - Double-click: START_PERSONAPLEX.bat
echo    - Or run: LAUNCHER.bat for menu options
echo.
echo  Server will be available at: https://localhost:8998
echo.
echo ================================================================================
echo.
echo  -----------------------------------------------------------------------
echo   Like this installer? Subscribe to SurAiverse for more AI tutorials!
echo   YouTube: https://www.youtube.com/@suraiverse
echo   By: Suresh Pydikondala
echo  -----------------------------------------------------------------------
echo.

set /p "LAUNCH_NOW=Would you like to launch PersonaPlex now? (y/n): "
if /i "!LAUNCH_NOW!"=="y" (
    echo.
    echo Starting PersonaPlex...
    echo.
    call START_PERSONAPLEX.bat
) else (
    echo.
    echo To launch later, double-click: START_PERSONAPLEX.bat
    echo.
    pause
)

endlocal
