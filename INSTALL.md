# PersonaPlex Installation Guide

Complete step-by-step installation guide for PersonaPlex on Windows.

> **Windows Installer by:** [Suresh Pydikondala (SurAI Verse)](https://www.youtube.com/@suraiverse)  
> Subscribe for more AI tutorials and guides!

---

## One-Click Installation (Recommended)

**The easiest way to install PersonaPlex:**

1. Double-click **`INSTALL_PERSONAPLEX.bat`**
2. Follow the on-screen prompts
3. Done!

The installer will:
- Check your system requirements
- Create a virtual environment
- Install all dependencies
- Build the web interface (client)
- Set up HuggingFace authentication
- Optionally launch PersonaPlex

**After installation, just double-click `START_PERSONAPLEX.bat` to run PersonaPlex anytime.**

---

## Manual Installation

If you prefer manual installation or the one-click installer doesn't work, follow the steps below.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Project Installation](#project-installation)
4. [HuggingFace Setup](#huggingface-setup)
5. [Launching the Server](#launching-the-server)
6. [Using the Web UI](#using-the-web-ui)
7. [Troubleshooting](#troubleshooting)
8. [File Reference](#file-reference)

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | NVIDIA GPU with 12GB VRAM | RTX 3090/4090 (24GB VRAM) |
| **RAM** | 16GB | 32GB |
| **Disk Space** | 25GB free | 50GB free |
| **Internet** | Required for model download | Fast connection (models ~14GB) |

### Software Requirements

| Software | Version | Required |
|----------|---------|----------|
| **Windows** | 10/11 | Yes |
| **Python** | 3.10 or higher | Yes |
| **Node.js** | 18+ (LTS recommended) | Yes |
| **NVIDIA Drivers** | Latest | Yes |
| **CUDA** | 11.8+ | Yes |

---

## Prerequisites Installation

### Step 1: Install Python

1. **Download Python** from [python.org](https://www.python.org/downloads/)
   - Version 3.10, 3.11, or 3.12 recommended
   
2. **Run the installer**
   - **IMPORTANT**: Check "Add Python to PATH" at the bottom of the installer
   - Click "Install Now"

3. **Verify installation** - Open Command Prompt or PowerShell:
   ```powershell
   python --version
   ```
   Should show: `Python 3.10.x` or higher

### Step 2: Install NVIDIA Drivers and CUDA

1. **Update NVIDIA Drivers**
   - Download from [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx)
   - Select your GPU model and install

2. **Verify GPU detection**:
   ```powershell
   nvidia-smi
   ```
   Should show your GPU name and CUDA version

### Step 3: Install Node.js

Node.js is required to build the web interface.

1. **Download Node.js** from [nodejs.org](https://nodejs.org/)
   - Choose the **LTS** (Long Term Support) version
   - Version 18 or higher recommended

2. **Run the installer**
   - Use default settings
   - Make sure "Add to PATH" is checked

3. **Verify installation** - Open a new Command Prompt or PowerShell:
   ```powershell
   node --version
   npm --version
   ```
   Should show versions like: `v18.x.x` and `9.x.x` or higher

### Step 4: Install Git (Optional but Recommended)

1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default settings

---

## Project Installation

### Step 1: Get the Project Files

**Option A: Clone with Git (Recommended)**
```powershell
git clone https://github.com/NVIDIA/personaplex.git
cd personaplex
```

**Option B: Download ZIP**
1. Go to https://github.com/NVIDIA/personaplex
2. Click "Code" → "Download ZIP"
3. Extract to a folder (e.g., `D:\persona\personaplex`)
4. Open PowerShell in that folder

### Step 2: Create a Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

> **Note**: You'll need to activate the virtual environment each time you open a new terminal.

### Step 3: Install Python Dependencies

```powershell
# Install the moshi package
pip install moshi/.

# Install accelerate for CPU offload support (recommended)
pip install accelerate
```

### Step 4: Build the Web Interface

Build the client (web UI) locally to ensure reliable access:

```powershell
# Navigate to the client directory
cd client

# Install Node.js dependencies
npm install

# Build the production client
npm run build

# Return to project root
cd ..
```

This creates a `client/dist` folder containing the web interface. The server will automatically serve this when you access it via browser.

> **Why build locally?** The server can download a pre-built UI from HuggingFace, but this can fail due to network issues or API changes. Building locally ensures the web UI always works.

### Step 5: Verify Installation

```powershell
# Test that moshi imports correctly
python -c "import moshi; print('Moshi installed successfully!')"

# Test PyTorch and CUDA
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

# Verify client was built
dir client\dist
```

Expected output:
```
Moshi installed successfully!
PyTorch: 2.x.x+cu1xx
CUDA available: True
```

And the `client\dist` directory should contain files like `index.html`, `assets/`, etc.

### Step 6: (Blackwell GPUs Only) Install PyTorch cu130

If you have a Blackwell-based GPU (RTX 50xx series):
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
```

---

## HuggingFace Setup

PersonaPlex models are hosted on HuggingFace and require authentication.

### Step 1: Create a HuggingFace Account

1. Go to [huggingface.co](https://huggingface.co)
2. Click "Sign Up" and create an account
3. Verify your email

### Step 2: Accept the Model License

1. Go to the Moshi model page:
   **https://huggingface.co/nvidia/personaplex-7b-v1**
   
2. Log in with your HuggingFace account

3. Read the license and click **"Accept"** (or "Agree and access repository")

> **Important**: You must accept the license before downloading models!

### Step 3: Create an Access Token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

2. Click **"New token"**

3. Configure the token:
   - **Name**: `personaplex` (or any name you prefer)
   - **Type**: `Read` (read-only is sufficient)

4. Click **"Generate"**

5. **Copy the token** (starts with `hf_...`)

### Step 4: Set Up Authentication

**Option A: Use the Setup Script (Easiest)**
```powershell
# Double-click SETUP_HUGGINGFACE.bat
# Or run from PowerShell:
.\SETUP_HUGGINGFACE.bat
```

**Option B: Set Environment Variable (Permanent)**
```powershell
# Replace with your actual token
[Environment]::SetEnvironmentVariable("HF_TOKEN", "hf_your_token_here", "User")

# Restart your terminal for changes to take effect
```

**Option C: Use HuggingFace CLI**
```powershell
pip install huggingface-hub
huggingface-cli login
```
Enter your token when prompted.

### Step 5: Verify Authentication

```powershell
python -c "from huggingface_hub import HfApi; api = HfApi(); print(api.whoami())"
```

Should show your HuggingFace username.

---

## Launching the Server

### Quick Start (Double-Click)

Just double-click: **`START_PERSONAPLEX.bat`**

That's it! The server will start and you can access it at https://localhost:8998

### Alternative Launch Methods

#### Normal Mode (Full GPU)
```powershell
# Double-click START_PERSONAPLEX.bat
# Or run from PowerShell:
.\launch_server.ps1
```

#### CPU Offload Mode (If Out of Memory)
```powershell
# Double-click START_PERSONAPLEX_CPU_OFFLOAD.bat
# Or run from PowerShell:
.\launch_server.ps1 --cpu-offload
```

#### Public Share (Gradio Tunnel)
```powershell
# Double-click START_PERSONAPLEX_PUBLIC.bat
# Or use the launcher menu (Public Share)
```
This prints a public HTTPS link in the terminal. Keep the window open to keep the link active.

#### Interactive Menu
```powershell
# Double-click LAUNCHER.bat for menu options
```

### First Launch - What to Expect

On first launch, the server will:

1. **Download models** (~14GB total)
   - `config.json` - Model configuration
   - `model.safetensors` - Main model (~14GB)
   - `tokenizer-e351c8d8-checkpoint125.safetensors` - Audio codec
   - `tokenizer_spm_32k_3.model` - Text tokenizer

2. **Show download progress** - Be patient, this takes 30-60 minutes

3. **Start the server** - You'll see:
   ```
   Access the Web UI at https://localhost:8998
   ```

### Subsequent Launches

After models are downloaded (cached):
- Startup takes ~30-60 seconds
- No re-downloading needed

---

## Using the Web UI

### Step 1: Access the Interface

1. Open your web browser (Chrome recommended)

2. Go to: **https://localhost:8998**

3. **Security Warning**: You'll see a certificate warning because the server uses a self-signed SSL certificate
   - Click "Advanced"
   - Click "Proceed to localhost (unsafe)"
   - This is safe for local use

### Step 2: Configure the Conversation

1. **Select a Voice** - Choose from:
   - Natural voices: `NATF0-3`, `NATM0-3` (more conversational)
   - Variety voices: `VARF0-4`, `VARM0-4` (more expressive)

2. **Set a Prompt** (optional) - Examples:
   ```
   You are a wise and friendly teacher. Answer questions in a clear and engaging way.
   ```
   ```
   You enjoy having a good conversation.
   ```

3. **Allow Microphone Access** - Click "Allow" when your browser asks

### Step 3: Start Talking

1. Click the **Start** or **Connect** button
2. Wait for connection confirmation
3. Start speaking - PersonaPlex will respond in real-time!

### Tips for Best Experience

- **Use a good microphone** - Reduces background noise issues
- **Speak clearly** - Natural pace, not too fast
- **Use headphones** - Prevents echo/feedback
- **Good internet** - For smooth audio streaming

---

## Troubleshooting

### Installation Issues

#### "Python not found"
```
Solution: Install Python 3.10+ from python.org
Make sure to check "Add Python to PATH" during installation
```

#### "pip is not recognized"
```powershell
# Try using Python module syntax
python -m pip install moshi/.
```

#### "CUDA not available"
```powershell
# Check NVIDIA driver installation
nvidia-smi

# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Authentication Issues

#### "401 Unauthorized" or "Access Denied"
1. Verify you accepted the license at https://huggingface.co/nvidia/personaplex-7b-v1
2. Check your token is set:
   ```powershell
   echo $env:HF_TOKEN
   ```
3. Re-run authentication setup:
   ```powershell
   .\SETUP_HUGGINGFACE.bat
   ```

#### "403 Forbidden"
You haven't accepted the model license. Go to the model page and click "Accept".

### Server Issues

#### "CUDA out of memory"
```
Solution: Use CPU offload mode
Double-click: START_PERSONAPLEX_CPU_OFFLOAD.bat
```

#### "Port 8998 already in use"
```powershell
# Find what's using the port
netstat -ano | findstr :8998

# Kill the process (replace PID with the number shown)
taskkill /PID <PID> /F
```

#### Server starts but no audio
1. Check microphone permissions in browser
2. Try a different browser (Chrome works best)
3. Check your audio input/output devices

### Model Download Issues

#### Downloads keep failing
```powershell
# Check internet connection
ping huggingface.co

# Try pre-downloading models
python verify_and_download_models.py
```

#### Download stuck/frozen
- Check available disk space
- Restart the download (it will resume)
- Try a different network

### Performance Issues

#### Choppy/stuttering audio
1. Close other GPU-intensive applications
2. Check GPU utilization:
   ```powershell
   nvidia-smi -l 1
   ```
3. Try CPU offload mode if VRAM is full

#### High latency
- Check network connection
- Use wired internet if possible
- Close background applications

---

## File Reference

### Launcher Scripts

| File | Purpose |
|------|---------|
| `INSTALL_PERSONAPLEX.bat` | **One-click installer** - Complete setup from scratch |
| `START_PERSONAPLEX.bat` | **Main launcher** - Double-click to start server |
| `START_PERSONAPLEX_CPU_OFFLOAD.bat` | Start with CPU offload (for memory issues) |
| `START_PERSONAPLEX_PUBLIC.bat` | Public share link via Gradio tunnel |
| `START_PERSONAPLEX_PUBLIC_CPU_OFFLOAD.bat` | Public share + CPU offload |
| `LAUNCHER.bat` | Interactive menu with all options |
| `CHECK_STATUS.bat` | Verify installation and dependencies |
| `SETUP_HUGGINGFACE.bat` | Set up HuggingFace authentication |

### PowerShell Scripts

| File | Purpose |
|------|---------|
| `launch_server.ps1` | Advanced server launcher |
| `setup_huggingface.ps1` | HuggingFace setup helper |
| `check_models.ps1` | Check downloaded model files |
| `verify_opus.ps1` | Verify Opus codec |

### Python Scripts

| File | Purpose |
|------|---------|
| `verify_project.py` | Full project verification |
| `verify_and_download_models.py` | Download models manually |
| `check_gpu_status.py` | GPU diagnostic tool |

### Project Structure

```
personaplex/
├── moshi/                 # Python backend package
│   └── moshi/
│       ├── server.py      # Main server
│       ├── models/        # Model implementations
│       └── ...
├── client/                # Web frontend (React)
│   └── src/
├── assets/                # Test files and images
├── START_PERSONAPLEX.bat  # Main launcher
├── INSTALL.md             # This file
└── README.md              # Official documentation
```

---

## Quick Reference Commands

```powershell
# Check Python version
python --version

# Check PyTorch and CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Check moshi installation
python -c "import moshi; print('OK')"

# Check HuggingFace token
echo $env:HF_TOKEN

# Monitor GPU usage
nvidia-smi -l 1

# Start server (normal)
.\launch_server.ps1

# Start server (CPU offload)
.\launch_server.ps1 --cpu-offload

# Verify installation
python verify_project.py

# Download models manually
python verify_and_download_models.py
```

---

## Getting Help

- **GitHub Issues**: https://github.com/NVIDIA/personaplex/issues
- **HuggingFace Model**: https://huggingface.co/nvidia/personaplex-7b-v1
- **Paper**: https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf
- **Discord**: https://discord.gg/5jAXrrbwRb

---

## Summary

1. Install Python 3.10+, Node.js 18+, and NVIDIA drivers
2. Clone/download the project
3. Run `pip install moshi/.`
4. Build the web UI: `cd client && npm install && npm run build`
5. Accept license at https://huggingface.co/nvidia/personaplex-7b-v1
6. Run `SETUP_HUGGINGFACE.bat` to set up authentication
7. Double-click `START_PERSONAPLEX.bat`
8. Open https://localhost:8998 in your browser
9. Start talking!

**First launch downloads ~14GB of models. Subsequent launches are fast.**
