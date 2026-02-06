# PersonaPlex One-Click Installer (Windows)

[![Weights](https://img.shields.io/badge/🤗-Weights-yellow)](https://huggingface.co/nvidia/personaplex-7b-v1)
[![Paper](https://img.shields.io/badge/📄-Paper-blue)](https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf)
[![Demo](https://img.shields.io/badge/🎮-Demo-green)](https://research.nvidia.com/labs/adlr/personaplex/)
[![Discord](https://img.shields.io/badge/Discord-Join-purple?logo=discord)](https://discord.gg/5jAXrrbwRb)

PersonaPlex is a real-time, full-duplex speech-to-speech conversational model with persona control via text prompts and audio voice conditioning. This repository provides a **Windows one-click installer** so you can get up and running without manual setup.

<p align="center">
  <img src="assets/architecture_diagram.png" alt="PersonaPlex Model Architecture">
  <br>
  <em>PersonaPlex Architecture</em>
</p>

---

## Credits

- **Main project:** [NVIDIA PersonaPlex](https://github.com/NVIDIA/personaplex) — original model and research.
- **Windows one-click installer:** Created by **Suresh Pydikondala** for easy Windows installation and launch.

This project is a Windows-focused packaging of the upstream [NVIDIA/personaplex](https://github.com/NVIDIA/personaplex) repository.

---

## Quick Start (Windows)

1. **Download or clone** this repository.
2. **Double-click** `INSTALL_PERSONAPLEX.bat` — it handles environment, dependencies, and client build.
3. **Follow the prompts** to set your HuggingFace token (required for model access).
4. When installation finishes, **double-click** `START_PERSONAPLEX.bat` to launch.

**Requirements:** Windows 10 or 11, Python 3.10+, Node.js 18+, and an NVIDIA GPU (12GB+ VRAM recommended).

> **Note — First-time installation and first run:**  
> The first time you run the installer and the first time you start PersonaPlex, the app will **download roughly 14GB of model files** from HuggingFace. This can take **30–60 minutes** or more depending on your connection. Please be patient and keep the window open until it completes. After that, models are cached locally and future launches are much faster (~30–60 seconds).

For detailed steps and troubleshooting, see [INSTALL.md](INSTALL.md).

---

## What the installer does

- Checks system requirements (Python, Node.js, GPU, RAM).
- Creates a virtual environment and installs Python dependencies (including `moshi`).
- Builds the web client so you can use the UI in your browser.
- Guides you through HuggingFace token setup.
- Optionally launches PersonaPlex when done.

---

## After installation

| Action              | What to run                          |
|---------------------|--------------------------------------|
| Start PersonaPlex   | `START_PERSONAPLEX.bat`              |
| Low VRAM / OOM      | `START_PERSONAPLEX_CPU_OFFLOAD.bat`  |
| Public share link   | `START_PERSONAPLEX_PUBLIC.bat`       |
| All options / menu  | `LAUNCHER.bat`                       |
| Check setup         | `CHECK_STATUS.bat`                   |
| Set HuggingFace     | `SETUP_HUGGINGFACE.bat`              |

Open the Web UI at **https://localhost:8998** (accept the self-signed certificate warning in the browser if prompted).

---

## HuggingFace setup (required)

1. Create an account at [huggingface.co](https://huggingface.co).
2. Accept the model license: [nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1).
3. Create a **Read** token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
4. Run `SETUP_HUGGINGFACE.bat` and paste your token when asked.

---

## Voices

Pre-packaged voice embeddings:

- **Natural (female):** NATF0, NATF1, NATF2, NATF3  
- **Natural (male):** NATM0, NATM1, NATM2, NATM3  
- **Variety (female):** VARF0–VARF4  
- **Variety (male):** VARM0–VARM4  

---

## Support and license

- **Issues (upstream):** [NVIDIA/personaplex issues](https://github.com/NVIDIA/personaplex/issues)
- **Discord:** [PersonaPlex Discord](https://discord.gg/5jAXrrbwRb)

Code is under the MIT license. Model weights use the NVIDIA Open Model license.

---

## Citation (upstream work)

If you use PersonaPlex in research, please cite:

```bibtex
@article{roy2026personaplex,
  title={PersonaPlex: Voice and Role Control for Full Duplex Conversational Speech Models},
  author={Roy, Rajarshi and Raiman, Jonathan and Lee, Sang-gil and Ene, Teodor-Dumitru and Kirby, Robert and Kim, Sungwon and Kim, Jaehyeon and Catanzaro, Bryan},
  year={2026}
}
```
