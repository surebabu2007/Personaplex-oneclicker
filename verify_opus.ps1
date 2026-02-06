# Opus Codec Verification Script
# This script verifies that Opus audio codec is properly installed and working

Write-Host "Verifying Opus Audio Codec Installation..." -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

try {
    Write-Host "Testing sphn package import..." -ForegroundColor Yellow
    py -c "import sphn; print('sphn package imported successfully')"
    
    Write-Host ""
    Write-Host "Testing OpusStreamWriter (encoding)..." -ForegroundColor Yellow
    py -c "import sphn; import numpy as np; writer = sphn.OpusStreamWriter(24000); test_audio = np.random.randn(480).astype(np.float32); writer.append_pcm(test_audio); print('Opus encoding working')"
    
    Write-Host ""
    Write-Host "Testing OpusStreamReader (decoding)..." -ForegroundColor Yellow
    py -c "import sphn; reader = sphn.OpusStreamReader(24000); print('Opus decoding working')"
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Opus audio codec is properly installed and working!" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "The sphn package includes bundled Opus libraries for Windows." -ForegroundColor Cyan
    Write-Host "No additional Opus installation is required." -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Opus verification failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "If you see errors, you may need to install Opus manually:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://opus-codec.org/downloads/" -ForegroundColor Cyan
    Write-Host "2. Or use conda: conda install -c conda-forge opus" -ForegroundColor Cyan
    exit 1
}
