# PersonaPlex Server Launcher (PowerShell)
# Created by SurAiverse - https://www.youtube.com/@suraiverse

$ErrorActionPreference = "Stop"

# Banner
Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                       PersonaPlex Server Launcher                             " -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                    by SurAiverse (Suresh Pydikondala)                         " -ForegroundColor Yellow
Write-Host "             YouTube: https://www.youtube.com/@suraiverse                      " -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check for virtual environment
Write-Host "[*] Checking virtual environment..." -ForegroundColor Gray
$venvPath = ".\venv\Scripts\Activate.ps1"
$venvPython = ".\venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    Write-Host "[OK] Virtual environment found" -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "[WARNING] Virtual environment not found!" -ForegroundColor Yellow
    Write-Host "   Run INSTALL_PERSONAPLEX.bat first to set up the environment." -ForegroundColor Gray
    Write-Host ""
    $continue = Read-Host "Continue with system Python? (y/n)"
    if ($continue -ne "y") {
        Write-Host ""
        Write-Host "Exiting. Please run the installer first." -ForegroundColor Red
        exit 1
    }
}

# Check Python
Write-Host "[*] Checking Python..." -ForegroundColor Gray
try {
    if (Test-Path $venvPython) {
        $pythonVersion = & $venvPython --version 2>&1
    } else {
        $pythonVersion = python --version 2>&1
    }
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "   Please install Python 3.10+ from https://python.org" -ForegroundColor Gray
    exit 1
}

# Check HuggingFace token
Write-Host "[*] Checking HuggingFace authentication..." -ForegroundColor Gray
if ($env:HF_TOKEN) {
    Write-Host "[OK] HF_TOKEN found" -ForegroundColor Green
} else {
    # Try to check cached token
    try {
        $tokenCheck = python -c "from huggingface_hub.utils import HfFolder; t=HfFolder.get_token(); exit(0 if t else 1)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Using cached HuggingFace login" -ForegroundColor Green
        } else {
            throw "No token"
        }
    } catch {
        Write-Host "[WARNING] HuggingFace token not found!" -ForegroundColor Yellow
        Write-Host "   Model downloads may fail." -ForegroundColor Gray
        Write-Host "   Run .\setup_huggingface.ps1 or set `$env:HF_TOKEN" -ForegroundColor Gray
        Write-Host ""
        Start-Sleep -Seconds 2
    }
}

# Set environment variables for Windows compatibility
Write-Host "[*] Configuring environment..." -ForegroundColor Gray
$env:TORCHDYNAMO_DISABLE = "1"
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
Write-Host "[OK] Environment configured" -ForegroundColor Green

# Add moshi to PYTHONPATH
$moshiPath = Join-Path $PSScriptRoot "moshi"
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$moshiPath;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $moshiPath
}

# Create temporary SSL directory
Write-Host "[*] Setting up SSL..." -ForegroundColor Gray
$sslDir = Join-Path ([System.IO.Path]::GetTempPath()) ("personaplex_ssl_" + [System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $sslDir -Force | Out-Null
Write-Host "[OK] SSL directory: $sslDir" -ForegroundColor Green

# Display server info
Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                       Starting PersonaPlex Server                             " -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Server URL: " -NoNewline -ForegroundColor Gray
Write-Host "https://localhost:8998" -ForegroundColor Green
Write-Host ""
Write-Host "  NOTE: Your browser may show a security warning because" -ForegroundColor Yellow
Write-Host "  we use a self-signed certificate. This is normal and safe." -ForegroundColor Yellow
Write-Host "  Click 'Advanced' then 'Proceed' to continue." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Launch server
try {
    if (Test-Path $venvPython) {
        & $venvPython -m moshi.server --ssl $sslDir
    } else {
        python -m moshi.server --ssl $sslDir
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Server crashed or failed to start!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. CUDA out of memory - try CPU offload mode:" -ForegroundColor Gray
    Write-Host "     python -m moshi.server --ssl $sslDir --cpu-offload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Missing models - run:" -ForegroundColor Gray
    Write-Host "     python verify_and_download_models.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Port in use - close other applications using port 8998" -ForegroundColor Gray
    Write-Host ""
}

# Server stopped
Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                           Server Stopped                                      " -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Subscribe to SurAiverse for AI tutorials!" -ForegroundColor Yellow
Write-Host "  YouTube: https://www.youtube.com/@suraiverse" -ForegroundColor Yellow
Write-Host ""

# Cleanup SSL directory
if (Test-Path $sslDir) {
    Remove-Item -Path $sslDir -Recurse -Force -ErrorAction SilentlyContinue
}
