# HuggingFace Setup Script for PersonaPlex
# Created by SurAiverse - https://www.youtube.com/@suraiverse

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                   PersonaPlex HuggingFace Setup                               " -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                    by SurAiverse (Suresh Pydikondala)                         " -ForegroundColor Yellow
Write-Host "             YouTube: https://www.youtube.com/@suraiverse                      " -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Accept the Model License
Write-Host "STEP 1: Accept the Model License" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "Before downloading models, you must accept the license agreement." -ForegroundColor White
Write-Host ""
Write-Host "Opening the model page in your browser..." -ForegroundColor Yellow
Start-Process "https://huggingface.co/nvidia/personaplex-7b-v1"
Write-Host ""

$continue = Read-Host "Have you accepted the license? (y/n)"
if ($continue -ne "y") {
    Write-Host ""
    Write-Host "Please accept the license first, then run this script again." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Step 2: Choose authentication method
Write-Host ""
Write-Host "STEP 2: Set Up Authentication" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""
Write-Host "Choose how to authenticate with HuggingFace:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] Login using huggingface-cli (recommended)" -ForegroundColor Cyan
Write-Host "      - Interactive login, token saved securely" -ForegroundColor Gray
Write-Host ""
Write-Host "  [2] Set token as environment variable" -ForegroundColor Cyan
Write-Host "      - Manual token entry" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Installing/updating huggingface-hub..." -ForegroundColor Yellow
    
    # Try to use venv python if available
    $venvPython = ".\venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        & $venvPython -m pip install --upgrade huggingface-hub --quiet
        Write-Host ""
        Write-Host "Running huggingface-cli login..." -ForegroundColor Yellow
        Write-Host "Follow the prompts to enter your token." -ForegroundColor Gray
        Write-Host ""
        & ".\venv\Scripts\huggingface-cli.exe" login
    } else {
        py -m pip install --upgrade huggingface-hub --quiet
        Write-Host ""
        Write-Host "Running huggingface-cli login..." -ForegroundColor Yellow
        Write-Host "Follow the prompts to enter your token." -ForegroundColor Gray
        Write-Host ""
        huggingface-cli login
    }
    
    Write-Host ""
    Write-Host "[OK] Authentication complete!" -ForegroundColor Green

} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "To get your token:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Go to: https://huggingface.co/settings/tokens" -ForegroundColor White
    Write-Host "  2. Click 'New token'" -ForegroundColor White
    Write-Host "  3. Name it (e.g., 'PersonaPlex')" -ForegroundColor White
    Write-Host "  4. Select 'Read' access" -ForegroundColor White
    Write-Host "  5. Copy the token (starts with 'hf_')" -ForegroundColor White
    Write-Host ""
    
    Start-Process "https://huggingface.co/settings/tokens"
    Write-Host "Opening tokens page in browser..." -ForegroundColor Gray
    Write-Host ""
    
    $token = Read-Host "Enter your HuggingFace token"
    
    if ($token) {
        # Set for current session
        $env:HF_TOKEN = $token
        
        Write-Host ""
        Write-Host "[OK] Token set for this session." -ForegroundColor Green
        
        $saveChoice = Read-Host "Save permanently? (y/n)"
        if ($saveChoice -eq "y") {
            # Save to user environment variable
            [Environment]::SetEnvironmentVariable("HF_TOKEN", $token, "User")
            Write-Host "[OK] Token saved permanently." -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "To use in other PowerShell sessions:" -ForegroundColor Yellow
        Write-Host '  $env:HF_TOKEN="your_token_here"' -ForegroundColor Gray
        
    } else {
        Write-Host ""
        Write-Host "[ERROR] No token provided." -ForegroundColor Red
        exit 1
    }

} else {
    Write-Host ""
    Write-Host "[ERROR] Invalid choice." -ForegroundColor Red
    exit 1
}

# Done
Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                         Setup Complete!                                       " -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now:" -ForegroundColor White
Write-Host "  - Run .\launch_server.ps1 to start PersonaPlex" -ForegroundColor Cyan
Write-Host "  - Or double-click START_PERSONAPLEX.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "  Subscribe to SurAiverse for AI tutorials!" -ForegroundColor Yellow
Write-Host "  YouTube: https://www.youtube.com/@suraiverse" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""
