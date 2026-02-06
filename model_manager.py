#!/usr/bin/env python3
"""
PersonaPlex Model Manager
Handles model downloading, validation, and custom path configuration
Created by SurAiverse - https://www.youtube.com/@suraiverse
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Callable, Tuple, Dict, List
from dataclasses import dataclass
import time

# HuggingFace Hub imports
try:
    from huggingface_hub import (
        hf_hub_download, 
        hf_hub_url, 
        try_to_load_from_cache,
        HfApi,
        snapshot_download
    )
    from huggingface_hub.utils import (
        HfHubHTTPError, 
        RepositoryNotFoundError,
        GatedRepoError
    )
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


# Constants
HF_REPO = "nvidia/personaplex-7b-v1"
CONFIG_FILE = "model_config.json"

# Required model files with expected sizes (in bytes, approximate)
REQUIRED_FILES = {
    "model.safetensors": {
        "description": "Main Moshi LM model",
        "min_size_bytes": 13_000_000_000,  # ~13GB minimum
        "max_size_bytes": 18_000_000_000,  # ~18GB maximum
    },
    "tokenizer-e351c8d8-checkpoint125.safetensors": {
        "description": "Mimi audio encoder/decoder model",
        "min_size_bytes": 300_000_000,  # ~300MB minimum
        "max_size_bytes": 500_000_000,  # ~500MB maximum
    },
    "tokenizer_spm_32k_3.model": {
        "description": "Text tokenizer model",
        "min_size_bytes": 500_000,  # ~500KB minimum
        "max_size_bytes": 2_000_000,  # ~2MB maximum
    },
}

OPTIONAL_FILES = {
    "voices.tgz": {
        "description": "Voice prompt embeddings (downloaded on first use)",
        "min_size_bytes": 1_000_000,
        "max_size_bytes": 100_000_000,
    },
    "dist.tgz": {
        "description": "Client distribution files (optional)",
        "min_size_bytes": 100_000,
        "max_size_bytes": 50_000_000,
    },
}


@dataclass
class ModelFile:
    """Represents a model file with its status"""
    filename: str
    description: str
    required: bool
    exists: bool = False
    path: Optional[str] = None
    size_bytes: int = 0
    valid: bool = False
    error: Optional[str] = None


@dataclass
class ModelConfig:
    """Configuration for model paths"""
    custom_model_path: Optional[str] = None
    use_symlinks: bool = False
    hf_cache_dir: Optional[str] = None
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "ModelConfig":
        """Load configuration from file"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                CONFIG_FILE
            )
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                pass
        
        return cls()
    
    def save(self, config_path: Optional[str] = None):
        """Save configuration to file"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                CONFIG_FILE
            )
        
        data = {
            "custom_model_path": self.custom_model_path,
            "use_symlinks": self.use_symlinks,
            "hf_cache_dir": self.hf_cache_dir,
        }
        
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)


class ModelManager:
    """Manages PersonaPlex model files"""
    
    def __init__(self, 
                 progress_callback: Optional[Callable[[str, float], None]] = None,
                 log_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the model manager.
        
        Args:
            progress_callback: Function(message, progress_0_to_1) for progress updates
            log_callback: Function(message, level) for logging (level: info, success, warning, error)
        """
        self.progress_callback = progress_callback or (lambda msg, prog: None)
        self.log_callback = log_callback or (lambda msg, level: print(f"[{level.upper()}] {msg}"))
        self.config = ModelConfig.load()
        self._cancel_flag = False
    
    def log(self, message: str, level: str = "info"):
        """Log a message"""
        self.log_callback(message, level)
    
    def progress(self, message: str, value: float):
        """Report progress"""
        self.progress_callback(message, value)
    
    def cancel(self):
        """Set cancel flag to stop operations"""
        self._cancel_flag = True
    
    def get_hf_cache_dir(self) -> Path:
        """Get the HuggingFace cache directory"""
        if self.config.hf_cache_dir:
            return Path(self.config.hf_cache_dir)
        return Path.home() / ".cache" / "huggingface" / "hub"
    
    def get_hf_token(self) -> Optional[str]:
        """Get HuggingFace token from environment or cache"""
        # Try environment variable first
        token = os.environ.get("HF_TOKEN")
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
    
    def check_authentication(self) -> Tuple[bool, str]:
        """
        Check if HuggingFace authentication is set up.
        
        Returns:
            Tuple of (is_authenticated, message)
        """
        if not HF_AVAILABLE:
            return False, "huggingface_hub not installed"
        
        token = self.get_hf_token()
        if not token:
            return False, "No HuggingFace token found. Set HF_TOKEN environment variable or run 'huggingface-cli login'"
        
        try:
            api = HfApi(token=token)
            user_info = api.whoami()
            return True, f"Authenticated as: {user_info.get('name', 'Unknown')}"
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"
    
    def check_license_accepted(self) -> Tuple[bool, str]:
        """
        Check if the model license has been accepted.
        
        Returns:
            Tuple of (is_accepted, message)
        """
        if not HF_AVAILABLE:
            return False, "huggingface_hub not installed"
        
        token = self.get_hf_token()
        
        try:
            # Try to get file info - will fail if license not accepted
            api = HfApi(token=token)
            api.hf_hub_url(repo_id=HF_REPO, filename="config.json")
            return True, "License accepted"
        except GatedRepoError:
            return False, f"License not accepted. Please visit: https://huggingface.co/{HF_REPO}"
        except RepositoryNotFoundError:
            return False, f"Repository not found: {HF_REPO}"
        except Exception as e:
            # Might still work - try to proceed
            return True, f"Could not verify license status: {str(e)}"
    
    def get_cached_file_path(self, filename: str) -> Optional[str]:
        """
        Get the path to a cached file if it exists.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            Path to cached file or None
        """
        if not HF_AVAILABLE:
            return None
        
        try:
            cached = try_to_load_from_cache(
                repo_id=HF_REPO,
                filename=filename,
                cache_dir=str(self.get_hf_cache_dir()) if self.config.hf_cache_dir else None,
            )
            if cached and os.path.exists(cached):
                return cached
        except Exception:
            pass
        
        return None
    
    def validate_file(self, filepath: str, file_info: Dict) -> Tuple[bool, str]:
        """
        Validate a model file.
        
        Args:
            filepath: Path to the file
            file_info: Dictionary with min_size_bytes, max_size_bytes
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not os.path.exists(filepath):
            return False, "File does not exist"
        
        size = os.path.getsize(filepath)
        min_size = file_info.get("min_size_bytes", 0)
        max_size = file_info.get("max_size_bytes", float("inf"))
        
        if size < min_size:
            return False, f"File too small ({size:,} bytes, expected >= {min_size:,})"
        
        if size > max_size:
            return False, f"File too large ({size:,} bytes, expected <= {max_size:,})"
        
        # Additional validation for safetensors files
        if filepath.endswith(".safetensors"):
            try:
                # Just check if the file header is valid
                with open(filepath, "rb") as f:
                    header_size = int.from_bytes(f.read(8), "little")
                    if header_size > 10_000_000:  # Header shouldn't be larger than 10MB
                        return False, "Invalid safetensors header"
            except Exception as e:
                return False, f"Could not validate safetensors file: {str(e)}"
        
        return True, f"Valid ({size / (1024*1024):.2f} MB)"
    
    def check_model_status(self) -> List[ModelFile]:
        """
        Check the status of all required and optional model files.
        
        Returns:
            List of ModelFile objects with status information
        """
        results = []
        
        # Check custom model path first
        custom_path = self.config.custom_model_path
        
        for filename, info in {**REQUIRED_FILES, **OPTIONAL_FILES}.items():
            model_file = ModelFile(
                filename=filename,
                description=info["description"],
                required=filename in REQUIRED_FILES,
            )
            
            # Check custom path
            if custom_path:
                custom_file = os.path.join(custom_path, filename)
                if os.path.exists(custom_file):
                    model_file.exists = True
                    model_file.path = custom_file
                    model_file.size_bytes = os.path.getsize(custom_file)
                    valid, msg = self.validate_file(custom_file, info)
                    model_file.valid = valid
                    if not valid:
                        model_file.error = msg
            
            # Check HuggingFace cache if not found in custom path
            if not model_file.exists:
                cached_path = self.get_cached_file_path(filename)
                if cached_path:
                    model_file.exists = True
                    model_file.path = cached_path
                    model_file.size_bytes = os.path.getsize(cached_path)
                    valid, msg = self.validate_file(cached_path, info)
                    model_file.valid = valid
                    if not valid:
                        model_file.error = msg
            
            results.append(model_file)
        
        return results
    
    def download_file(self, filename: str, force: bool = False) -> Tuple[bool, str]:
        """
        Download a single file from HuggingFace.
        
        Args:
            filename: Name of file to download
            force: If True, re-download even if cached
            
        Returns:
            Tuple of (success, path_or_error)
        """
        if not HF_AVAILABLE:
            return False, "huggingface_hub not installed"
        
        if self._cancel_flag:
            return False, "Download cancelled"
        
        token = self.get_hf_token()
        
        # Check if already cached and valid
        if not force:
            cached = self.get_cached_file_path(filename)
            if cached:
                file_info = REQUIRED_FILES.get(filename, OPTIONAL_FILES.get(filename, {}))
                valid, _ = self.validate_file(cached, file_info)
                if valid:
                    return True, cached
        
        self.log(f"Downloading {filename}...", "info")
        
        try:
            file_path = hf_hub_download(
                repo_id=HF_REPO,
                filename=filename,
                token=token,
                cache_dir=str(self.get_hf_cache_dir()) if self.config.hf_cache_dir else None,
                resume_download=True,
            )
            
            if file_path and os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                self.log(f"Downloaded {filename} ({size_mb:.2f} MB)", "success")
                return True, file_path
            else:
                return False, "Download completed but file not found"
                
        except GatedRepoError:
            return False, f"License not accepted. Visit: https://huggingface.co/{HF_REPO}"
        except HfHubHTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication required. Set HF_TOKEN or run 'huggingface-cli login'"
            elif e.response.status_code == 403:
                return False, f"Access denied. Accept license at: https://huggingface.co/{HF_REPO}"
            else:
                return False, f"HTTP error {e.response.status_code}: {str(e)}"
        except Exception as e:
            return False, f"Download error: {str(e)}"
    
    def download_all_models(self, 
                           include_optional: bool = False,
                           force: bool = False) -> Tuple[bool, List[str]]:
        """
        Download all required (and optionally optional) model files.
        
        Args:
            include_optional: If True, also download optional files
            force: If True, re-download even if cached
            
        Returns:
            Tuple of (all_success, list_of_errors)
        """
        errors = []
        files_to_download = dict(REQUIRED_FILES)
        
        if include_optional:
            files_to_download.update(OPTIONAL_FILES)
        
        total = len(files_to_download)
        
        for i, (filename, info) in enumerate(files_to_download.items()):
            if self._cancel_flag:
                errors.append("Download cancelled by user")
                break
            
            progress = i / total
            self.progress(f"Downloading {filename}...", progress)
            
            success, result = self.download_file(filename, force=force)
            
            if not success:
                if filename in REQUIRED_FILES:
                    errors.append(f"{filename}: {result}")
                else:
                    self.log(f"Optional file {filename} failed: {result}", "warning")
        
        self.progress("Download complete", 1.0)
        
        return len(errors) == 0, errors
    
    def setup_custom_model_path(self, 
                                source_path: str, 
                                create_symlinks: bool = False) -> Tuple[bool, str]:
        """
        Configure custom model path.
        
        Args:
            source_path: Path to folder containing model files
            create_symlinks: If True, create symlinks in HF cache pointing to source
            
        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(source_path):
            return False, f"Path does not exist: {source_path}"
        
        if not os.path.isdir(source_path):
            return False, f"Path is not a directory: {source_path}"
        
        # Validate required files exist
        missing = []
        for filename in REQUIRED_FILES:
            filepath = os.path.join(source_path, filename)
            if not os.path.exists(filepath):
                missing.append(filename)
        
        if missing:
            return False, f"Missing required files: {', '.join(missing)}"
        
        # Update configuration
        self.config.custom_model_path = source_path
        self.config.use_symlinks = create_symlinks
        self.config.save()
        
        self.log(f"Custom model path configured: {source_path}", "success")
        
        return True, "Custom model path configured successfully"
    
    def get_model_path(self, filename: str) -> Optional[str]:
        """
        Get the path to a model file.
        
        Args:
            filename: Name of the model file
            
        Returns:
            Path to the file or None if not found
        """
        # Check custom path first
        if self.config.custom_model_path:
            custom_file = os.path.join(self.config.custom_model_path, filename)
            if os.path.exists(custom_file):
                return custom_file
        
        # Check HuggingFace cache
        cached = self.get_cached_file_path(filename)
        if cached:
            return cached
        
        return None
    
    def get_total_size_bytes(self) -> int:
        """Get total size of all downloaded models in bytes"""
        total = 0
        for model_file in self.check_model_status():
            if model_file.exists:
                total += model_file.size_bytes
        return total
    
    def cleanup_invalid_files(self) -> List[str]:
        """
        Remove invalid/corrupt model files from cache.
        
        Returns:
            List of removed file paths
        """
        removed = []
        
        for model_file in self.check_model_status():
            if model_file.exists and not model_file.valid and model_file.path:
                try:
                    os.remove(model_file.path)
                    removed.append(model_file.path)
                    self.log(f"Removed invalid file: {model_file.filename}", "warning")
                except Exception as e:
                    self.log(f"Could not remove {model_file.filename}: {e}", "error")
        
        return removed


def print_model_status():
    """Print current model status to console"""
    manager = ModelManager()
    
    print("=" * 70)
    print("PersonaPlex Model Status")
    print("=" * 70)
    print(f"HuggingFace Repo: {HF_REPO}")
    print(f"Cache Directory: {manager.get_hf_cache_dir()}")
    
    config = ModelConfig.load()
    if config.custom_model_path:
        print(f"Custom Model Path: {config.custom_model_path}")
    
    # Check authentication
    auth_ok, auth_msg = manager.check_authentication()
    print(f"\nAuthentication: {'OK' if auth_ok else 'FAILED'} - {auth_msg}")
    
    # Check model files
    print("\n" + "-" * 70)
    print("Model Files:")
    print("-" * 70)
    
    status = manager.check_model_status()
    
    for model in status:
        prefix = "[REQUIRED]" if model.required else "[OPTIONAL]"
        if model.exists and model.valid:
            size_mb = model.size_bytes / (1024 * 1024)
            print(f"  {prefix} {model.filename}")
            print(f"          Status: OK ({size_mb:.2f} MB)")
            print(f"          Path: {model.path}")
        elif model.exists and not model.valid:
            print(f"  {prefix} {model.filename}")
            print(f"          Status: INVALID - {model.error}")
        else:
            print(f"  {prefix} {model.filename}")
            print(f"          Status: NOT FOUND")
    
    # Summary
    required_files = [m for m in status if m.required]
    found_valid = [m for m in required_files if m.exists and m.valid]
    
    print("\n" + "-" * 70)
    print(f"Required files: {len(found_valid)}/{len(required_files)} ready")
    
    total_size = manager.get_total_size_bytes()
    print(f"Total size: {total_size / (1024**3):.2f} GB")
    
    if len(found_valid) == len(required_files):
        print("\n[SUCCESS] All required models are ready!")
    else:
        print("\n[ACTION NEEDED] Run download to get missing files")


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PersonaPlex Model Manager")
    parser.add_argument("--status", action="store_true", help="Show model status")
    parser.add_argument("--download", action="store_true", help="Download missing models")
    parser.add_argument("--download-all", action="store_true", help="Download all models including optional")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    parser.add_argument("--set-path", type=str, help="Set custom model path")
    parser.add_argument("--cleanup", action="store_true", help="Remove invalid files")
    
    args = parser.parse_args()
    
    manager = ModelManager()
    
    if args.set_path:
        success, msg = manager.setup_custom_model_path(args.set_path)
        print(msg)
        return 0 if success else 1
    
    if args.cleanup:
        removed = manager.cleanup_invalid_files()
        print(f"Removed {len(removed)} invalid files")
        return 0
    
    if args.download or args.download_all:
        print("Starting model download...")
        success, errors = manager.download_all_models(
            include_optional=args.download_all,
            force=args.force
        )
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        return 0 if success else 1
    
    # Default: show status
    print_model_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
