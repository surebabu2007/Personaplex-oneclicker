# Quick Model Check Script for PersonaPlex
# Checks if required models are downloaded

Write-Host "Checking PersonaPlex Model Files..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

$repo = "nvidia/personaplex-7b-v1"
$cacheDir = "$env:USERPROFILE\.cache\huggingface\hub"

Write-Host "HuggingFace cache: $cacheDir" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $cacheDir)) {
    Write-Host "[WARNING] HuggingFace cache directory not found!" -ForegroundColor Yellow
    Write-Host "Models will be downloaded on first server launch." -ForegroundColor Yellow
    exit 0
}

# Required files
$requiredFiles = @(
    "config.json",
    "model.safetensors",
    "tokenizer-e351c8d8-checkpoint125.safetensors",
    "tokenizer_spm_32k_3.model"
)

$found = 0
$missing = 0

foreach ($file in $requiredFiles) {
    # Search in cache directory
    $foundFile = Get-ChildItem -Path $cacheDir -Recurse -Filter $file -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($foundFile) {
        $sizeMB = [math]::Round($foundFile.Length / 1MB, 2)
        Write-Host "[OK] $file" -ForegroundColor Green
        Write-Host "    Size: $sizeMB MB" -ForegroundColor Gray
        Write-Host "    Path: $($foundFile.FullName)" -ForegroundColor Gray
        $found++
    } else {
        Write-Host "[MISSING] $file" -ForegroundColor Red
        $missing++
    }
    Write-Host ""
}

Write-Host "====================================" -ForegroundColor Green
Write-Host "Summary: $found/$($requiredFiles.Count) files found" -ForegroundColor $(if ($missing -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($missing -eq 0) {
    Write-Host "[SUCCESS] All required models are downloaded!" -ForegroundColor Green
    Write-Host "You can launch the server with: .\launch_server.ps1" -ForegroundColor Cyan
} else {
    Write-Host "[INFO] Missing models will be downloaded automatically on first server launch." -ForegroundColor Yellow
    Write-Host "Make sure you have:" -ForegroundColor Yellow
    Write-Host "  1. Accepted the license at: https://huggingface.co/$repo" -ForegroundColor Cyan
    Write-Host "  2. Set HF_TOKEN or logged in with: huggingface-cli login" -ForegroundColor Cyan
}
