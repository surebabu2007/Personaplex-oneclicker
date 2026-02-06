#!/usr/bin/env python3
"""
Test script to validate PersonaPlex installer components.
Run this to check that all installer files are properly set up.

Created by SurAiverse - https://www.youtube.com/@suraiverse
"""

import os
import sys
import ast
import subprocess
from pathlib import Path


def print_banner():
    print()
    print("=" * 70)
    print("       PersonaPlex Installer Validation Test")
    print("       by SurAiverse - https://www.youtube.com/@suraiverse")
    print("=" * 70)
    print()


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"   [OK] {description}")
        return True
    else:
        print(f"   [MISSING] {description}: {filepath}")
        return False


def check_python_syntax(filepath: str) -> bool:
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f"   [OK] Syntax valid: {os.path.basename(filepath)}")
        return True
    except SyntaxError as e:
        print(f"   [ERROR] Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"   [ERROR] Could not read {filepath}: {e}")
        return False


def check_import(module_name: str) -> bool:
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"   [OK] Import: {module_name}")
        return True
    except ImportError as e:
        print(f"   [WARNING] Cannot import {module_name}: {e}")
        return False


def main():
    print_banner()
    
    script_dir = Path(__file__).parent
    all_ok = True
    warnings = 0
    
    # 1. Check batch files
    print("1. Checking Batch Files")
    print("-" * 70)
    
    batch_files = [
        ("INSTALL_PERSONAPLEX.bat", "Main installer"),
        ("START_PERSONAPLEX.bat", "Server launcher"),
        ("START_PERSONAPLEX_CPU_OFFLOAD.bat", "CPU offload launcher"),
        ("LAUNCHER.bat", "Menu launcher"),
        ("CHECK_STATUS.bat", "Status checker"),
        ("SETUP_HUGGINGFACE.bat", "HuggingFace setup"),
    ]
    
    for filename, description in batch_files:
        filepath = script_dir / filename
        if not check_file_exists(str(filepath), f"{filename} ({description})"):
            all_ok = False
    print()
    
    # 2. Check Python files syntax
    print("2. Checking Python Files Syntax")
    print("-" * 70)
    
    python_files = [
        "installer_gui.py",
        "installer_utils.py",
        "model_manager.py",
        "verify_and_download_models.py",
        "verify_project.py",
    ]
    
    for filename in python_files:
        filepath = script_dir / filename
        if filepath.exists():
            if not check_python_syntax(str(filepath)):
                all_ok = False
        else:
            print(f"   [MISSING] {filename}")
            all_ok = False
    print()
    
    # 3. Check PowerShell files
    print("3. Checking PowerShell Files")
    print("-" * 70)
    
    ps_files = [
        ("launch_server.ps1", "PowerShell launcher"),
        ("setup_huggingface.ps1", "HuggingFace setup"),
    ]
    
    for filename, description in ps_files:
        filepath = script_dir / filename
        if not check_file_exists(str(filepath), f"{filename} ({description})"):
            warnings += 1  # Not critical
    print()
    
    # 4. Check moshi package
    print("4. Checking Moshi Package")
    print("-" * 70)
    
    moshi_files = [
        ("moshi/moshi/__init__.py", "Moshi package init"),
        ("moshi/moshi/server.py", "Server module"),
        ("moshi/moshi/models/loaders.py", "Model loaders"),
        ("moshi/pyproject.toml", "Package config"),
    ]
    
    for filepath, description in moshi_files:
        full_path = script_dir / filepath
        if not check_file_exists(str(full_path), f"{filepath}"):
            all_ok = False
    print()
    
    # 5. Test imports (if in venv)
    print("5. Testing Module Imports")
    print("-" * 70)
    
    # Check if we're in venv
    in_venv = hasattr(sys, 'real_prefix') or \
              (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("   [INFO] Not in virtual environment - skipping import tests")
        print("   [INFO] Run from activated venv for full testing")
    else:
        # Test basic imports
        test_imports = [
            "tkinter",
            "json",
            "pathlib",
            "subprocess",
            "threading",
        ]
        
        for module in test_imports:
            if not check_import(module):
                warnings += 1
        
        # Test installer modules
        try:
            sys.path.insert(0, str(script_dir))
            
            import installer_utils
            print("   [OK] installer_utils module loads")
            
            import model_manager
            print("   [OK] model_manager module loads")
            
        except Exception as e:
            print(f"   [WARNING] Could not load installer modules: {e}")
            warnings += 1
    print()
    
    # 6. Check configuration files
    print("6. Checking Configuration Templates")
    print("-" * 70)
    
    config_files = [
        (".env.example", "Environment template"),
        ("client/.env.local.example", "Client env template"),
    ]
    
    for filepath, description in config_files:
        full_path = script_dir / filepath
        if full_path.exists():
            print(f"   [OK] {filepath}")
        else:
            print(f"   [INFO] {filepath} not found (optional)")
    print()
    
    # 7. Check branding consistency
    print("7. Checking SurAiverse Branding")
    print("-" * 70)
    
    branding_strings = [
        "suraiverse",
        "SurAiverse",
        "youtube.com/@suraiverse",
    ]
    
    files_to_check = batch_files + [(f, "") for f in python_files]
    branded_files = 0
    
    for filename, _ in files_to_check:
        filepath = script_dir / filename
        if filepath.exists():
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                if any(brand.lower() in content.lower() for brand in branding_strings):
                    branded_files += 1
            except:
                pass
    
    print(f"   [OK] Found branding in {branded_files}/{len(files_to_check)} files")
    print()
    
    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    if all_ok and warnings == 0:
        print()
        print("   [SUCCESS] All tests passed!")
        print()
        print("   The installer is ready for distribution.")
        print()
    elif all_ok:
        print()
        print(f"   [OK] Core tests passed ({warnings} warning(s))")
        print()
        print("   The installer should work. Check warnings above.")
        print()
    else:
        print()
        print("   [FAILED] Some tests failed!")
        print()
        print("   Please fix the issues above before distributing.")
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
