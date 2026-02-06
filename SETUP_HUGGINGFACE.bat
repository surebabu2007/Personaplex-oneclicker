@echo off
setlocal EnableDelayedExpansion

REM HuggingFace Authentication Setup
REM Created by SurAiverse - https://www.youtube.com/@suraiverse

title HuggingFace Setup - by SurAiverse
color 0D

echo.
echo  ===============================================================================
echo  ^|                                                                             ^|
echo  ^|     ____                                    ____  _                         ^|
echo  ^|    ^|  _ \ ___ _ __ ___  ___  _ __   __ _  ^|  _ \^| ^| _____  __              ^|
echo  ^|    ^| ^|_) / _ \ '__/ __^|/ _ \^| '_ \ / _` ^| ^| ^|_) ^| ^|/ _ \ \/ /              ^|
echo  ^|    ^|  __/  __/ ^|  \__ \ (_) ^| ^| ^| ^| (_^| ^| ^|  __/^| ^|  __/^>  ^<               ^|
echo  ^|    ^|_^|   \___^|_^|  ^|___/\___/^|_^| ^|_^|\__,_^| ^|_^|   ^|_^|\___/_/\_\              ^|
echo  ^|                                                                             ^|
echo  ^|                HUGGINGFACE AUTHENTICATION SETUP                             ^|
echo  ^|                                                                             ^|
echo  ^|         By: Suresh Pydikondala (SurAiverse)                                 ^|
echo  ^|         YouTube: https://www.youtube.com/@suraiverse                        ^|
echo  ^|                                                                             ^|
echo  ===============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM ================================================================================
REM Check current status
REM ================================================================================
echo  Checking current authentication status...
echo.

if defined HF_TOKEN (
    echo  [OK] HF_TOKEN environment variable is already set
    echo.
    set /p RECONFIGURE="Do you want to reconfigure? (y/n): "
    if /i not "!RECONFIGURE!"=="y" (
        echo.
        echo  Keeping existing configuration.
        pause
        exit /b 0
    )
)

REM ================================================================================
REM Step 1: Accept License
REM ================================================================================
echo.
echo  ===============================================================================
echo   STEP 1: Accept the Model License
echo  ===============================================================================
echo.
echo   Before you can download models, you must:
echo.
echo   1. Create a HuggingFace account (if you don't have one)
echo   2. Go to the model page and accept the license
echo.
echo   Opening the model page in your browser...
echo.
start "" "https://huggingface.co/nvidia/personaplex-7b-v1"

echo.
set /p LICENSE_ACCEPTED="Have you accepted the license? (y/n): "
if /i not "!LICENSE_ACCEPTED!"=="y" (
    echo.
    echo   Please accept the license first, then run this setup again.
    echo.
    pause
    exit /b 1
)

REM ================================================================================
REM Step 2: Get Token
REM ================================================================================
echo.
echo  ===============================================================================
echo   STEP 2: Get Your Access Token
echo  ===============================================================================
echo.
echo   To get your HuggingFace token:
echo.
echo   1. Go to: https://huggingface.co/settings/tokens
echo   2. Click "New token" or use an existing one
echo   3. Give it a name (e.g., "PersonaPlex")
echo   4. Select "Read" access (that's all you need)
echo   5. Click "Generate token"
echo   6. Copy the token (starts with "hf_")
echo.
echo   Opening the tokens page in your browser...
echo.
start "" "https://huggingface.co/settings/tokens"

echo.
echo   -----------------------------------------------------------------------
echo.
set /p HF_TOKEN_INPUT="   Enter your HuggingFace token: "

if "!HF_TOKEN_INPUT!"=="" (
    echo.
    echo   [ERROR] No token entered!
    pause
    exit /b 1
)

REM Validate token format
echo !HF_TOKEN_INPUT! | findstr /b "hf_" >nul
if !ERRORLEVEL! neq 0 (
    echo.
    echo   [WARNING] Token doesn't start with 'hf_'
    echo   This might not be a valid HuggingFace token.
    echo.
    set /p USE_ANYWAY="   Use it anyway? (y/n): "
    if /i not "!USE_ANYWAY!"=="y" (
        echo.
        echo   Please get a valid token and try again.
        pause
        exit /b 1
    )
)

REM ================================================================================
REM Step 3: Save Token
REM ================================================================================
echo.
echo  ===============================================================================
echo   STEP 3: Saving Token
echo  ===============================================================================
echo.

REM Set for current session
set "HF_TOKEN=!HF_TOKEN_INPUT!"
echo   [OK] Token set for current session

REM Save permanently
echo.
set /p SAVE_PERMANENT="   Save token permanently for future sessions? (y/n): "
if /i "!SAVE_PERMANENT!"=="y" (
    setx HF_TOKEN "!HF_TOKEN_INPUT!" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo   [OK] Token saved permanently
    ) else (
        echo   [WARNING] Could not save permanently. Token valid for this session only.
    )
) else (
    echo   [OK] Token will only be valid for this session
)

REM ================================================================================
REM Verify (optional)
REM ================================================================================
echo.
echo  ===============================================================================
echo   Verifying Token
echo  ===============================================================================
echo.

REM Activate venv if available
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python -c "from huggingface_hub import HfApi; api = HfApi(token='!HF_TOKEN_INPUT!'); user = api.whoami(); print(f'   [OK] Authenticated as: {user[\"name\"]}')" 2>nul
if !ERRORLEVEL! neq 0 (
    echo   [WARNING] Could not verify token. It may still work.
    echo   If downloads fail, please check your token.
)

REM ================================================================================
REM Done
REM ================================================================================
echo.
echo  ===============================================================================
echo   Setup Complete!
echo  ===============================================================================
echo.
echo   Your HuggingFace authentication is now configured.
echo.
echo   Next steps:
echo   - Run INSTALL_PERSONAPLEX.bat to install dependencies
echo   - Or run START_PERSONAPLEX.bat to launch the server
echo.
echo  -----------------------------------------------------------------------
echo   Subscribe to SurAiverse for more AI tutorials!
echo   YouTube: https://www.youtube.com/@suraiverse
echo  -----------------------------------------------------------------------
echo.
pause
endlocal
