#!/usr/bin/env python3
"""
Verify and download all required PersonaPlex models from HuggingFace.
This script checks for missing models and downloads them if needed.
Supports custom model paths for offline installation.

Created by SurAiverse - https://www.youtube.com/@suraiverse
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download, hf_hub_url, try_to_load_from_cache
    from huggingface_hub.utils import HfHubHTTPError, GatedRepoError
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("[WARNING] huggingface_hub not installed. Install with: pip install huggingface_hub")

# Required files from the PersonaPlex model repository (NVIDIA)
HF_REPO = "nvidia/personaplex-7b-v1"
CONFIG_FILE = "model_config.json"

REQUIRED_FILES = {
    "model.safetensors": {
        "description": "Main Moshi LM model (~15GB)",
        "min_size_bytes": 13_000_000_000,
    },
    "tokenizer-e351c8d8-checkpoint125.safetensors": {
        "description": "Mimi audio encoder/decoder model (~385MB)",
        "min_size_bytes": 80_000_000,
    },
    "tokenizer_spm_32k_3.model": {
        "description": "Text tokenizer model (~553KB)",
        "min_size_bytes": 500_000,
    },
}

OPTIONAL_FILES = {
    "voices.tgz": {
        "description": "Voice prompt embeddings (downloaded on first use if not provided)",
        "min_size_bytes": 1_000_000,
    },
    "dist.tgz": {
        "description": "Client distribution files (optional)",
        "min_size_bytes": 100_000,
    },
}


def print_banner():
    """Print SurAiverse banner"""
    print("=" * 70)
    print("PersonaPlex Model Verification and Download")
    print("by SurAiverse - https://www.youtube.com/@suraiverse")
    print("=" * 70)


def load_config() -> dict:
    """Load model configuration"""
    config_path = Path(__file__).parent / CONFIG_FILE
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict):
    """Save model configuration"""
    config_path = Path(__file__).parent / CONFIG_FILE
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def get_hf_token() -> str | None:
    """Get HuggingFace token from environment or cache"""
    # Try environment variable first
    token = os.getenv("HF_TOKEN")
    if token:
        return token
    
    # Try HuggingFace cache
    if HF_AVAILABLE:
        try:
            from huggingface_hub.utils import HfFolder
            token = HfFolder.get_token()
            if token:
                return token
        except Exception:
            pass
    
    return None


def check_file_in_custom_path(custom_path: str, filename: str) -> tuple[bool, str | None]:
    """Check if a file exists in custom path"""
    filepath = os.path.join(custom_path, filename)
    if os.path.exists(filepath):
        return True, filepath
    return False, None


def check_file_status(repo_id: str, filename: str, custom_path: str | None = None) -> tuple[bool, str | None]:
    """Check if a file exists in cache, custom path, or can be downloaded."""
    # Check custom path first
    if custom_path:
        exists, path = check_file_in_custom_path(custom_path, filename)
        if exists:
            return True, path
    
    if not HF_AVAILABLE:
        return False, None
    
    try:
        # Try to get from cache
        cached_path = try_to_load_from_cache(
            repo_id=repo_id,
            filename=filename,
            cache_dir=None,  # Use default cache
        )
        
        if cached_path and os.path.exists(cached_path):
            return True, cached_path
        
        return False, None
    except Exception:
        return False, None


def validate_file(filepath: str, file_info: dict) -> tuple[bool, str]:
    """Validate a file's integrity"""
    if not os.path.exists(filepath):
        return False, "File does not exist"
    
    size = os.path.getsize(filepath)
    min_size = file_info.get("min_size_bytes", 0)
    
    if size < min_size:
        return False, f"File too small ({size:,} bytes, expected >= {min_size:,})"
    
    # Additional validation for safetensors
    if filepath.endswith(".safetensors"):
        try:
            with open(filepath, "rb") as f:
                header_size = int.from_bytes(f.read(8), "little")
                if header_size > 10_000_000:  # Header shouldn't be > 10MB
                    return False, "Invalid safetensors header"
        except Exception as e:
            return False, f"Could not validate: {e}"
    
    return True, f"Valid ({size / (1024*1024):.2f} MB)"


def download_file(repo_id: str, filename: str, description: str, token: str | None = None) -> str | None:
    """Download a file from HuggingFace Hub."""
    if not HF_AVAILABLE:
        print(f"   [ERROR] huggingface_hub not available")
        return None
    
    try:
        print(f"\n[DOWNLOAD] Downloading {filename}...")
        print(f"   Description: {description}")
        print(f"   This may take a while for large files...")
        
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            token=token,
            cache_dir=None,  # Use default cache
            resume_download=True,
        )
        
        if file_path and os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"   [OK] Downloaded: {file_path}")
            print(f"   Size: {size_mb:.2f} MB")
            return file_path
        else:
            print(f"   [ERROR] Download failed")
            return None
            
    except GatedRepoError:
        print(f"   [ERROR] Access denied! Please accept the model license at:")
        print(f"   https://huggingface.co/{repo_id}")
        return None
    except HfHubHTTPError as e:
        if hasattr(e, 'response') and e.response.status_code == 401:
            print(f"   [ERROR] Authentication required!")
            print(f"   Please set HF_TOKEN or run: huggingface-cli login")
        elif hasattr(e, 'response') and e.response.status_code == 403:
            print(f"   [ERROR] Access denied! Please accept the model license at:")
            print(f"   https://huggingface.co/{repo_id}")
        else:
            print(f"   [ERROR] {e}")
        return None
    except Exception as e:
        print(f"   [ERROR] Error downloading {filename}: {e}")
        return None


def set_custom_path(path: str) -> bool:
    """Set custom model path"""
    if not os.path.exists(path):
        print(f"[ERROR] Path does not exist: {path}")
        return False
    
    if not os.path.isdir(path):
        print(f"[ERROR] Path is not a directory: {path}")
        return False
    
    # Verify required files
    missing = []
    for filename in REQUIRED_FILES:
        filepath = os.path.join(path, filename)
        if not os.path.exists(filepath):
            missing.append(filename)
    
    if missing:
        print(f"[WARNING] Missing required files in custom path:")
        for f in missing:
            print(f"   - {f}")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Save config
    config = load_config()
    config["custom_model_path"] = path
    save_config(config)
    
    print(f"[OK] Custom model path set: {path}")
    return True


def main(args=None):
    """Main function"""
    parser = argparse.ArgumentParser(
        description="PersonaPlex Model Verification and Download"
    )
    parser.add_argument(
        "--set-path", "-p",
        type=str,
        help="Set custom path to model files"
    )
    parser.add_argument(
        "--download-only", "-d",
        action="store_true",
        help="Download missing files without prompts"
    )
    parser.add_argument(
        "--verify-only", "-v",
        action="store_true",
        help="Only verify files, don't download"
    )
    parser.add_argument(
        "--include-optional", "-o",
        action="store_true",
        help="Include optional files in download"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-download even if files exist"
    )
    
    parsed_args = parser.parse_args(args)
    
    print_banner()
    
    # Handle set-path command
    if parsed_args.set_path:
        success = set_custom_path(parsed_args.set_path)
        return 0 if success else 1
    
    # Load configuration
    config = load_config()
    custom_path = config.get("custom_model_path")
    
    print(f"\nRepository: {HF_REPO}")
    print(f"Cache location: {Path.home() / '.cache' / 'huggingface' / 'hub'}")
    if custom_path:
        print(f"Custom model path: {custom_path}")
    print()
    
    # Check HuggingFace authentication
    hf_token = get_hf_token()
    if not hf_token:
        print("[WARNING] HF_TOKEN not set!")
        print("   The model may require authentication.")
        print("   Set it with: $env:HF_TOKEN='your_token'")
        print("   Or login: huggingface-cli login")
        print()
        print("   Get your token at: https://huggingface.co/settings/tokens")
        print()
        if not parsed_args.download_only:
            print("Continuing without token (may fail if authentication required)...")
    else:
        print("[OK] HuggingFace token found")
    
    # Check required files
    print("\n" + "=" * 70)
    print("Checking Required Model Files")
    print("=" * 70)
    
    missing_files = []
    found_files = []
    invalid_files = []
    
    all_files = dict(REQUIRED_FILES)
    if parsed_args.include_optional:
        all_files.update(OPTIONAL_FILES)
    
    for filename, info in all_files.items():
        is_required = filename in REQUIRED_FILES
        prefix = "[REQUIRED]" if is_required else "[OPTIONAL]"
        
        print(f"\n{prefix} Checking {filename}...")
        
        # Check if file exists
        if parsed_args.force:
            exists, path = False, None
        else:
            exists, path = check_file_status(HF_REPO, filename, custom_path)
        
        if exists and path:
            # Validate file
            valid, msg = validate_file(path, info)
            if valid:
                print(f"   [OK] Found: {path}")
                print(f"   {msg}")
                found_files.append((filename, path))
            else:
                print(f"   [INVALID] {msg}")
                invalid_files.append((filename, info["description"]))
                if is_required:
                    missing_files.append((filename, info["description"]))
        else:
            print(f"   [MISSING] Not found in cache or custom path")
            if is_required:
                missing_files.append((filename, info["description"]))
    
    # Download missing files
    if missing_files and not parsed_args.verify_only:
        print("\n" + "=" * 70)
        print("Downloading Missing Files")
        print("=" * 70)
        
        if not parsed_args.download_only:
            print(f"\n{len(missing_files)} required file(s) need to be downloaded.")
            response = input("Download now? (y/n): ")
            if response.lower() != 'y':
                print("\n[INFO] Download cancelled. Run this script again when ready.")
                return 1
        
        download_errors = []
        for filename, description in missing_files:
            path = download_file(HF_REPO, filename, description, hf_token)
            if path:
                found_files.append((filename, path))
            else:
                download_errors.append(filename)
        
        if download_errors:
            print("\n[ERROR] Failed to download:")
            for f in download_errors:
                print(f"   - {f}")
            print("\nPlease check:")
            print("   1. Your internet connection")
            print("   2. HuggingFace authentication (HF_TOKEN)")
            print("   3. Model license acceptance at:")
            print(f"      https://huggingface.co/{HF_REPO}")
            return 1
    elif missing_files and parsed_args.verify_only:
        print(f"\n[INFO] {len(missing_files)} required file(s) are missing.")
        print("Run without --verify-only to download them.")
    
    # Check optional files (info only)
    if not parsed_args.include_optional:
        print("\n" + "=" * 70)
        print("Optional Files (downloaded on first use if needed)")
        print("=" * 70)
        
        for filename, info in OPTIONAL_FILES.items():
            exists, path = check_file_status(HF_REPO, filename, custom_path)
            if exists:
                print(f"[OK] {filename} - Found")
            else:
                print(f"[SKIP] {filename} - Will be downloaded on first use")
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    required_count = len(REQUIRED_FILES)
    found_required = len([f for f, _ in found_files if f in REQUIRED_FILES])
    
    print(f"Required files: {found_required}/{required_count} ready")
    
    total_size = 0
    for _, path in found_files:
        if path and os.path.exists(path):
            total_size += os.path.getsize(path)
    print(f"Total size: {total_size / (1024**3):.2f} GB")
    
    if found_required == required_count:
        print("\n[SUCCESS] All required models are ready!")
        print("\nYou can now launch the server with:")
        print("  START_PERSONAPLEX.bat")
        print("  or: .\\launch_server.ps1")
        print()
        print("=" * 70)
        print("Subscribe for more AI tutorials: youtube.com/@suraiverse")
        print("=" * 70)
        return 0
    else:
        print(f"\n[WARNING] {required_count - found_required} required file(s) are missing.")
        print("Please check the errors above and try again.")
        return 1


if __name__ == "__main__":
    success = main()
    sys.exit(success)
