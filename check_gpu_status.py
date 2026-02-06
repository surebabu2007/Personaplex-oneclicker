"""
GPU Diagnostic Script for PersonaPlex
Run this while the server is running to check GPU utilization and identify issues.
"""

import sys
import subprocess
import time

def check_nvidia_smi():
    """Check if nvidia-smi is available and get GPU info"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def check_torch_cuda():
    """Check PyTorch CUDA availability and settings"""
    try:
        import torch
        info = []
        info.append(f"PyTorch version: {torch.__version__}")
        info.append(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            info.append(f"CUDA version: {torch.version.cuda}")
            info.append(f"cuDNN version: {torch.backends.cudnn.version()}")
            info.append(f"cuDNN enabled: {torch.backends.cudnn.enabled}")
            info.append(f"cuDNN benchmark: {torch.backends.cudnn.benchmark}")
            info.append(f"Device count: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                info.append(f"\nGPU {i}: {props.name}")
                info.append(f"  Compute capability: {props.major}.{props.minor}")
                info.append(f"  Total memory: {props.total_memory / 1024**3:.2f} GB")
                info.append(f"  Multi-processor count: {props.multi_processor_count}")
                
                # Current memory usage
                allocated = torch.cuda.memory_allocated(i) / 1024**3
                reserved = torch.cuda.memory_reserved(i) / 1024**3
                info.append(f"  Memory allocated: {allocated:.2f} GB")
                info.append(f"  Memory reserved: {reserved:.2f} GB")
        
        return "\n".join(info)
    except ImportError:
        return "PyTorch not installed"
    except Exception as e:
        return f"Error checking PyTorch: {e}"

def monitor_gpu(duration=10, interval=1):
    """Monitor GPU utilization over time"""
    print(f"\n=== Monitoring GPU for {duration} seconds ===\n")
    samples = []
    
    for i in range(int(duration / interval)):
        gpu_info = check_nvidia_smi()
        if gpu_info:
            parts = gpu_info.split(', ')
            if len(parts) >= 5:
                name, mem_total, mem_used, mem_free, util, temp = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5] if len(parts) > 5 else "N/A"
                print(f"[{i*interval:3d}s] GPU Util: {util:>3}% | Mem: {mem_used:>5}/{mem_total:>5} MB | Temp: {temp}°C")
                samples.append({
                    'util': int(util) if util.isdigit() else 0,
                    'mem_used': int(mem_used) if mem_used.isdigit() else 0,
                    'mem_total': int(mem_total) if mem_total.isdigit() else 0
                })
        time.sleep(interval)
    
    if samples:
        avg_util = sum(s['util'] for s in samples) / len(samples)
        max_util = max(s['util'] for s in samples)
        min_util = min(s['util'] for s in samples)
        
        print(f"\n=== Summary ===")
        print(f"Average GPU utilization: {avg_util:.1f}%")
        print(f"Max GPU utilization: {max_util}%")
        print(f"Min GPU utilization: {min_util}%")
        
        if avg_util < 30:
            print("\n[WARNING] Low GPU utilization detected!")
            print("Possible causes:")
            print("  - CPU bottleneck (audio encoding/decoding)")
            print("  - Network latency issues")
            print("  - Model not using GPU efficiently")
        elif max_util - min_util > 50:
            print("\n[WARNING] High GPU utilization variance detected!")
            print("This can cause choppy audio due to:")
            print("  - Inconsistent frame processing times")
            print("  - GPU memory pressure causing swapping")
            print("  - Other processes competing for GPU")

def check_environment():
    """Check environment variables that affect GPU performance"""
    import os
    
    env_vars = [
        'CUDA_VISIBLE_DEVICES',
        'PYTORCH_CUDA_ALLOC_CONF',
        'TORCHDYNAMO_DISABLE',
        'NO_CUDA_GRAPH',
        'NO_TORCH_COMPILE',
    ]
    
    print("\n=== Environment Variables ===\n")
    for var in env_vars:
        value = os.environ.get(var, "(not set)")
        print(f"{var}: {value}")

def main():
    print("=" * 60)
    print("PersonaPlex GPU Diagnostic Tool")
    print("=" * 60)
    
    # Check nvidia-smi
    print("\n=== NVIDIA GPU Info ===\n")
    gpu_info = check_nvidia_smi()
    if gpu_info:
        parts = gpu_info.split(', ')
        if len(parts) >= 5:
            print(f"GPU: {parts[0]}")
            print(f"Total Memory: {parts[1]} MB")
            print(f"Used Memory: {parts[2]} MB")
            print(f"Free Memory: {parts[3]} MB")
            print(f"GPU Utilization: {parts[4]}%")
            if len(parts) > 5:
                print(f"Temperature: {parts[5]}°C")
    else:
        print("nvidia-smi not available or no NVIDIA GPU detected")
    
    # Check PyTorch CUDA
    print("\n=== PyTorch CUDA Info ===\n")
    print(check_torch_cuda())
    
    # Check environment
    check_environment()
    
    # Ask if user wants to monitor
    print("\n" + "=" * 60)
    try:
        response = input("\nWould you like to monitor GPU for 30 seconds? (y/n): ")
        if response.lower() in ('y', 'yes'):
            monitor_gpu(duration=30, interval=1)
    except KeyboardInterrupt:
        print("\nMonitoring cancelled.")
    
    print("\n=== Recommendations for Choppy Audio ===\n")
    print("1. Ensure cuDNN benchmark is enabled (should be fixed now)")
    print("2. Check that GPU utilization is consistent (not spiking)")
    print("3. Ensure no other GPU-intensive apps are running")
    print("4. If using CPU offload, choppy audio is expected")
    print("5. Try closing browser tabs to reduce WebSocket latency")
    print("6. Ensure your GPU has at least 8GB VRAM for smooth operation")

if __name__ == "__main__":
    main()
