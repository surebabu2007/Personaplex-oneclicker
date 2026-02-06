#!/usr/bin/env python3
"""
Comprehensive verification of PersonaPlex project setup.
Checks all dependencies, models, and configuration.

Created by SurAiverse - https://www.youtube.com/@suraiverse
"""

import os
import sys
from pathlib import Path


def print_banner():
    """Print SurAiverse banner"""
    print()
    print("=" * 70)
    print("       PersonaPlex Project Verification")
    print("       by SurAiverse - https://www.youtube.com/@suraiverse")
    print("=" * 70)
    print()


def check_import(module_name, package_name=None):
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)


def check_file_exists(filepath):
    """Check if a file exists."""
    return os.path.exists(filepath)


def get_file_size_mb(filepath):
    """Get file size in MB."""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0


def main():
    print_banner()
    
    all_ok = True
    warnings = 0
    
    # 1. Check Python packages
    print("1. Python Dependencies")
    print("-" * 70)
    
    required_packages = [
        ("moshi", "moshi-personaplex"),
        ("torch", "torch"),
        ("numpy", "numpy"),
        ("sphn", "sphn"),
        ("sentencepiece", "sentencepiece"),
        ("sounddevice", "sounddevice"),
        ("huggingface_hub", "huggingface-hub"),
        ("aiohttp", "aiohttp"),
        ("einops", "einops"),
        ("safetensors", "safetensors"),
    ]
    
    for module, package in required_packages:
        ok, error = check_import(module)
        if ok:
            print(f"   [OK] {package}")
        else:
            print(f"   [MISSING] {package}")
            all_ok = False
    print()
    
    # 2. Check CUDA/PyTorch
    print("2. PyTorch and CUDA")
    print("-" * 70)
    try:
        import torch
        print(f"   [OK] PyTorch version: {torch.__version__}")
        if torch.cuda.is_available():
            cuda_ver = torch.version.cuda
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"   [OK] CUDA version: {cuda_ver}")
            print(f"   [OK] GPU: {gpu_name}")
            print(f"   [OK] GPU Memory: {gpu_mem:.1f} GB")
        else:
            print(f"   [WARNING] CUDA not available - will use CPU (slower)")
            warnings += 1
    except Exception as e:
        print(f"   [ERROR] PyTorch check failed: {e}")
        all_ok = False
    print()
    
    # 3. Check Opus
    print("3. Opus Audio Codec")
    print("-" * 70)
    try:
        import sphn
        writer = sphn.OpusStreamWriter(24000)
        reader = sphn.OpusStreamReader(24000)
        print("   [OK] Opus codec working")
    except Exception as e:
        print(f"   [ERROR] Opus codec: {e}")
        all_ok = False
    print()
    
    # 4. Check HuggingFace cache
    print("4. Model Files")
    print("-" * 70)
    
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    print(f"   Cache: {cache_dir}")
    
    # Check for custom model path
    config_file = Path(__file__).parent / "model_config.json"
    custom_path = None
    if config_file.exists():
        try:
            import json
            with open(config_file) as f:
                config = json.load(f)
            custom_path = config.get("custom_model_path")
            if custom_path:
                print(f"   Custom Path: {custom_path}")
        except:
            pass
    
    if not cache_dir.exists() and not custom_path:
        print("   [INFO] Cache directory doesn't exist yet")
        print("   [INFO] Models will download on first server launch")
    else:
        try:
            from huggingface_hub import try_to_load_from_cache
            
            repo = "nvidia/personaplex-7b-v1"
            files = [
                ("model.safetensors", 15000),
                ("tokenizer-e351c8d8-checkpoint125.safetensors", 385),
                ("tokenizer_spm_32k_3.model", 0.55),
            ]
            
            found = 0
            for filename, expected_mb in files:
                # Check custom path first
                if custom_path:
                    custom_file = os.path.join(custom_path, filename)
                    if os.path.exists(custom_file):
                        size_mb = get_file_size_mb(custom_file)
                        print(f"   [OK] {filename} ({size_mb:.1f} MB) [custom]")
                        found += 1
                        continue
                
                # Check HF cache
                cached = try_to_load_from_cache(repo_id=repo, filename=filename)
                if cached and os.path.exists(cached):
                    size_mb = get_file_size_mb(cached)
                    print(f"   [OK] {filename} ({size_mb:.1f} MB)")
                    found += 1
                else:
                    print(f"   [MISSING] {filename}")
            
            if found == 0:
                print("   [INFO] No models found in cache")
                print("   [INFO] Models will download on first server launch")
            elif found < len(files):
                print(f"   [INFO] {found}/{len(files)} files found")
                warnings += 1
        except ImportError:
            print("   [INFO] Cannot check cache (huggingface_hub not installed)")
    print()
    
    # 5. Check HuggingFace authentication
    print("5. HuggingFace Authentication")
    print("-" * 70)
    
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("   [OK] HF_TOKEN is set")
        
        # Try to verify without printing account details
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=hf_token)
            api.whoami()
            print("   [OK] Token verified with HuggingFace")
        except Exception as e:
            print(f"   [WARNING] Could not verify token: {e}")
            warnings += 1
    else:
        # Check cached login
        try:
            from huggingface_hub.utils import HfFolder
            cached_token = HfFolder.get_token()
            if cached_token:
                print("   [OK] Using cached HuggingFace login")
            else:
                print("   [WARNING] No HuggingFace token found")
                print("   [INFO] Set token: $env:HF_TOKEN='your_token'")
                print("   [INFO] Or run: huggingface-cli login")
                warnings += 1
        except:
            print("   [WARNING] HF_TOKEN not set")
            warnings += 1
    print()
    
    # 6. Check project files
    print("6. Project Files")
    print("-" * 70)
    
    project_files = [
        ("moshi/moshi/server.py", "Server module"),
        ("moshi/moshi/models/loaders.py", "Model loaders"),
        ("START_PERSONAPLEX.bat", "Launch script"),
        ("INSTALL_PERSONAPLEX.bat", "Installer"),
    ]
    
    for filepath, desc in project_files:
        if check_file_exists(filepath):
            print(f"   [OK] {filepath}")
        else:
            print(f"   [MISSING] {filepath} ({desc})")
            all_ok = False
    print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    
    if all_ok and warnings == 0:
        print()
        print("   [SUCCESS] All checks passed!")
        print()
        print("   You can now launch PersonaPlex:")
        print("     - Double-click START_PERSONAPLEX.bat")
        print("     - Or run: python -m moshi.server --ssl temp")
        print()
    elif all_ok:
        print()
        print(f"   [OK] Core components ready ({warnings} warning(s))")
        print()
        print("   PersonaPlex should work. Check warnings above if issues occur.")
        print()
    else:
        print()
        print("   [WARNING] Some components need attention")
        print()
        print("   Please fix the issues above before launching.")
        print("   Run INSTALL_PERSONAPLEX.bat to set up missing components.")
        print()
    
    print("-" * 70)
    print("   Subscribe to SurAiverse for AI tutorials!")
    print("   YouTube: https://www.youtube.com/@suraiverse")
    print("-" * 70)
    print()
    
    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
