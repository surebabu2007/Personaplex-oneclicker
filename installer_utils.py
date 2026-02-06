#!/usr/bin/env python3
"""
PersonaPlex Installer Utilities
Shared utilities for system checks, error handling, and common operations
Created by SurAiverse - https://www.youtube.com/@suraiverse
"""

import os
import sys
import subprocess
import shutil
import platform
import socket
import urllib.request
import json
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass
from enum import Enum


# ==================== CONSTANTS ====================

YOUTUBE_CHANNEL = "https://www.youtube.com/@suraiverse"
HUGGINGFACE_TOKEN_URL = "https://huggingface.co/settings/tokens"
HUGGINGFACE_LICENSE_URL = "https://huggingface.co/nvidia/personaplex-7b-v1"
PYTHON_DOWNLOAD_URL = "https://www.python.org/downloads/"

MIN_PYTHON_VERSION = (3, 10)
MIN_DISK_SPACE_GB = 20
MIN_RAM_GB = 8

NVIDIA_SMI_PATHS = [
    r"C:\Windows\System32\nvidia-smi.exe",
    r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
    "nvidia-smi"  # Try PATH
]


# ==================== DATA CLASSES ====================

class CheckStatus(Enum):
    """Status of a system check"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """Result of a system check"""
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    fix_hint: Optional[str] = None


@dataclass
class SystemInfo:
    """System information"""
    os_name: str
    os_version: str
    python_version: str
    python_path: str
    cuda_available: bool
    cuda_version: Optional[str]
    gpu_name: Optional[str]
    gpu_memory_mb: Optional[int]
    total_ram_gb: float
    free_disk_gb: float
    has_internet: bool


# ==================== SYSTEM CHECKS ====================

def get_python_version() -> Tuple[int, int, int]:
    """Get Python version as tuple"""
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def check_python_version() -> CheckResult:
    """Check if Python version meets requirements"""
    version = get_python_version()
    version_str = f"{version[0]}.{version[1]}.{version[2]}"
    
    if version[0] < MIN_PYTHON_VERSION[0] or \
       (version[0] == MIN_PYTHON_VERSION[0] and version[1] < MIN_PYTHON_VERSION[1]):
        return CheckResult(
            name="Python Version",
            status=CheckStatus.ERROR,
            message=f"Python {version_str} found, {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required",
            details=f"Current: {sys.executable}",
            fix_hint=f"Download Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ from {PYTHON_DOWNLOAD_URL}"
        )
    
    return CheckResult(
        name="Python Version",
        status=CheckStatus.OK,
        message=f"Python {version_str}",
        details=sys.executable
    )


def find_nvidia_smi() -> Optional[str]:
    """Find nvidia-smi executable"""
    for path in NVIDIA_SMI_PATHS:
        if os.path.exists(path):
            return path
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["where" if platform.system() == "Windows" else "which", path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
    return None


def check_nvidia_gpu() -> CheckResult:
    """Check for NVIDIA GPU"""
    nvidia_smi = find_nvidia_smi()
    
    if not nvidia_smi:
        return CheckResult(
            name="NVIDIA GPU",
            status=CheckStatus.WARNING,
            message="nvidia-smi not found",
            details="NVIDIA drivers may not be installed",
            fix_hint="Install NVIDIA drivers from nvidia.com/drivers or use CPU mode"
        )
    
    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                parts = lines[0].split(',')
                gpu_name = parts[0].strip() if len(parts) > 0 else "Unknown"
                gpu_memory = parts[1].strip() if len(parts) > 1 else "Unknown"
                
                return CheckResult(
                    name="NVIDIA GPU",
                    status=CheckStatus.OK,
                    message=f"{gpu_name}",
                    details=f"Memory: {gpu_memory} MB"
                )
        
        return CheckResult(
            name="NVIDIA GPU",
            status=CheckStatus.WARNING,
            message="Could not query GPU information",
            details=result.stderr if result.stderr else "Unknown error"
        )
        
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="NVIDIA GPU",
            status=CheckStatus.WARNING,
            message="GPU query timed out",
            fix_hint="GPU may be busy or drivers may be unstable"
        )
    except Exception as e:
        return CheckResult(
            name="NVIDIA GPU",
            status=CheckStatus.WARNING,
            message=f"Error checking GPU: {str(e)}"
        )


def check_cuda_availability() -> CheckResult:
    """Check CUDA availability through PyTorch"""
    try:
        import torch
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda
            device_name = torch.cuda.get_device_name(0)
            return CheckResult(
                name="CUDA",
                status=CheckStatus.OK,
                message=f"CUDA {cuda_version} available",
                details=f"Device: {device_name}"
            )
        else:
            return CheckResult(
                name="CUDA",
                status=CheckStatus.WARNING,
                message="CUDA not available in PyTorch",
                fix_hint="Install PyTorch with CUDA support"
            )
    except ImportError:
        return CheckResult(
            name="CUDA",
            status=CheckStatus.UNKNOWN,
            message="PyTorch not installed",
            details="Cannot check CUDA availability"
        )
    except Exception as e:
        return CheckResult(
            name="CUDA",
            status=CheckStatus.WARNING,
            message=f"Error checking CUDA: {str(e)}"
        )


def check_disk_space(path: str = ".") -> CheckResult:
    """Check available disk space"""
    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        total_gb = total / (1024**3)
        
        if free_gb < MIN_DISK_SPACE_GB:
            return CheckResult(
                name="Disk Space",
                status=CheckStatus.WARNING,
                message=f"{free_gb:.1f} GB free (need ~{MIN_DISK_SPACE_GB} GB)",
                details=f"Total: {total_gb:.1f} GB",
                fix_hint="Free up disk space or install to a different drive"
            )
        
        return CheckResult(
            name="Disk Space",
            status=CheckStatus.OK,
            message=f"{free_gb:.1f} GB free",
            details=f"Total: {total_gb:.1f} GB"
        )
    except Exception as e:
        return CheckResult(
            name="Disk Space",
            status=CheckStatus.UNKNOWN,
            message=f"Could not check: {str(e)}"
        )


def check_ram() -> CheckResult:
    """Check available RAM"""
    try:
        if platform.system() == "Windows":
            import ctypes
            
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            
            meminfo = MEMORYSTATUSEX()
            meminfo.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(meminfo))
            
            total_gb = meminfo.ullTotalPhys / (1024**3)
            avail_gb = meminfo.ullAvailPhys / (1024**3)
        else:
            # Linux/Mac
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            total = int([x for x in meminfo.split('\n') if 'MemTotal' in x][0].split()[1]) / (1024**2)
            avail = int([x for x in meminfo.split('\n') if 'MemAvailable' in x][0].split()[1]) / (1024**2)
            total_gb = total
            avail_gb = avail
        
        if total_gb < MIN_RAM_GB:
            return CheckResult(
                name="RAM",
                status=CheckStatus.WARNING,
                message=f"{total_gb:.1f} GB total ({MIN_RAM_GB} GB recommended)",
                details=f"Available: {avail_gb:.1f} GB",
                fix_hint="Use CPU offload mode if memory issues occur"
            )
        
        return CheckResult(
            name="RAM",
            status=CheckStatus.OK,
            message=f"{total_gb:.1f} GB total",
            details=f"Available: {avail_gb:.1f} GB"
        )
    except Exception as e:
        return CheckResult(
            name="RAM",
            status=CheckStatus.UNKNOWN,
            message=f"Could not check: {str(e)}"
        )


def check_internet_connection(timeout: int = 5) -> CheckResult:
    """Check internet connectivity"""
    test_urls = [
        ("huggingface.co", 443),
        ("github.com", 443),
        ("google.com", 443),
    ]
    
    for host, port in test_urls:
        try:
            socket.create_connection((host, port), timeout=timeout)
            return CheckResult(
                name="Internet",
                status=CheckStatus.OK,
                message="Connected",
                details=f"Can reach {host}"
            )
        except (socket.timeout, socket.error):
            continue
    
    return CheckResult(
        name="Internet",
        status=CheckStatus.ERROR,
        message="No internet connection",
        fix_hint="Check your network connection or use offline installation with local models"
    )


def check_huggingface_access(token: Optional[str] = None) -> CheckResult:
    """Check HuggingFace API access"""
    if token is None:
        token = os.environ.get("HF_TOKEN")
    
    if not token:
        return CheckResult(
            name="HuggingFace Token",
            status=CheckStatus.WARNING,
            message="No token configured",
            fix_hint=f"Get your token from {HUGGINGFACE_TOKEN_URL}"
        )
    
    if not token.startswith("hf_"):
        return CheckResult(
            name="HuggingFace Token",
            status=CheckStatus.WARNING,
            message="Token format may be invalid",
            details="Token should start with 'hf_'"
        )
    
    # Try to verify token (basic check)
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        user = api.whoami()
        username = user.get("name", "Unknown")
        return CheckResult(
            name="HuggingFace Token",
            status=CheckStatus.OK,
            message=f"Authenticated as {username}",
            details="Token is valid"
        )
    except ImportError:
        return CheckResult(
            name="HuggingFace Token",
            status=CheckStatus.UNKNOWN,
            message="Token set but cannot verify",
            details="huggingface_hub not installed"
        )
    except Exception as e:
        return CheckResult(
            name="HuggingFace Token",
            status=CheckStatus.WARNING,
            message="Token may be invalid",
            details=str(e)
        )


def run_all_checks() -> List[CheckResult]:
    """Run all system checks"""
    checks = [
        check_python_version(),
        check_nvidia_gpu(),
        check_disk_space(),
        check_ram(),
        check_internet_connection(),
        check_huggingface_access(),
    ]
    return checks


# ==================== UTILITY FUNCTIONS ====================

def get_script_directory() -> Path:
    """Get the directory containing this script"""
    return Path(__file__).parent.absolute()


def get_venv_python() -> Optional[str]:
    """Get path to Python in virtual environment"""
    venv_path = get_script_directory() / "venv" / "Scripts" / "python.exe"
    if venv_path.exists():
        return str(venv_path)
    return None


def get_venv_pip() -> Optional[str]:
    """Get path to pip in virtual environment"""
    pip_path = get_script_directory() / "venv" / "Scripts" / "pip.exe"
    if pip_path.exists():
        return str(pip_path)
    return None


def is_venv_active() -> bool:
    """Check if virtual environment is active"""
    return hasattr(sys, 'real_prefix') or \
           (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def venv_exists() -> bool:
    """Check if virtual environment exists"""
    venv_path = get_script_directory() / "venv"
    activate_script = venv_path / "Scripts" / "activate.bat"
    return venv_path.exists() and activate_script.exists()


def run_in_venv(command: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command using the virtual environment Python"""
    venv_python = get_venv_python()
    if venv_python and command[0] in ("python", "python3"):
        command = [venv_python] + command[1:]
    return subprocess.run(command, **kwargs)


def cleanup_installation(remove_venv: bool = True, 
                         remove_cache: bool = False,
                         remove_pycache: bool = True) -> Dict[str, bool]:
    """
    Clean up installation files.
    
    Args:
        remove_venv: Remove virtual environment
        remove_cache: Remove HuggingFace model cache
        remove_pycache: Remove __pycache__ directories
    
    Returns:
        Dictionary of cleanup results
    """
    results = {}
    script_dir = get_script_directory()
    
    # Remove venv
    if remove_venv:
        venv_path = script_dir / "venv"
        try:
            if venv_path.exists():
                shutil.rmtree(venv_path)
            results["venv"] = True
        except Exception as e:
            results["venv"] = False
    
    # Remove HuggingFace cache for this repo
    if remove_cache:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        try:
            # Only remove personaplex-related cache
            for item in cache_dir.glob("*personaplex*"):
                shutil.rmtree(item)
            results["cache"] = True
        except Exception as e:
            results["cache"] = False
    
    # Remove __pycache__ directories
    if remove_pycache:
        try:
            for pycache in script_dir.rglob("__pycache__"):
                shutil.rmtree(pycache)
            results["pycache"] = True
        except Exception as e:
            results["pycache"] = False
    
    # Remove .pyc files
    try:
        for pyc in script_dir.rglob("*.pyc"):
            pyc.unlink()
    except:
        pass
    
    return results


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def is_admin() -> bool:
    """Check if running with admin privileges (Windows)"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def request_admin() -> bool:
    """Request admin privileges by relaunching script (Windows)"""
    try:
        import ctypes
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
    except:
        pass
    return False


# ==================== BRANDING ====================

ASCII_BANNER = r"""
 ____                                    ____  _           
|  _ \ ___ _ __ ___  ___  _ __   __ _  |  _ \| | _____  __
| |_) / _ \ '__/ __|/ _ \| '_ \ / _` | | |_) | |/ _ \ \/ /
|  __/  __/ |  \__ \ (_) | | | | (_| | |  __/| |  __/>  < 
|_|   \___|_|  |___/\___/|_| |_|\__,_| |_|   |_|\___/_/\_\

                    by SurAiverse
        YouTube: youtube.com/@suraiverse
"""

def print_banner():
    """Print the ASCII banner"""
    print(ASCII_BANNER)


def get_suraiverse_info() -> Dict[str, str]:
    """Get SurAiverse branding information"""
    return {
        "name": "SurAiverse",
        "youtube": YOUTUBE_CHANNEL,
        "creator": "Suresh Pydikondala",
        "project": "PersonaPlex One-Click Installer",
    }


# ==================== MAIN ====================

def print_system_info():
    """Print system information and check results"""
    print_banner()
    print("=" * 60)
    print("System Check Results")
    print("=" * 60)
    print()
    
    checks = run_all_checks()
    
    status_icons = {
        CheckStatus.OK: "[OK]",
        CheckStatus.WARNING: "[WARN]",
        CheckStatus.ERROR: "[ERROR]",
        CheckStatus.UNKNOWN: "[?]",
    }
    
    has_errors = False
    has_warnings = False
    
    for check in checks:
        icon = status_icons.get(check.status, "[?]")
        print(f"{icon} {check.name}: {check.message}")
        if check.details:
            print(f"       {check.details}")
        if check.fix_hint:
            print(f"       Fix: {check.fix_hint}")
        print()
        
        if check.status == CheckStatus.ERROR:
            has_errors = True
        elif check.status == CheckStatus.WARNING:
            has_warnings = True
    
    print("=" * 60)
    if has_errors:
        print("Status: ISSUES FOUND - Please resolve errors before installing")
    elif has_warnings:
        print("Status: READY (with warnings)")
    else:
        print("Status: ALL CHECKS PASSED")
    print("=" * 60)
    
    return not has_errors


if __name__ == "__main__":
    success = print_system_info()
    sys.exit(0 if success else 1)
