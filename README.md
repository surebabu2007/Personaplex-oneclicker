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

## Credits & Acknowledgements

This repository is a **Windows-focused one-click installer and launcher** built on top of the original PersonaPlex project.

**Original research & core implementation**  
The PersonaPlex model, architecture, and main codebase are created and maintained by the **NVIDIA PersonaPlex research team**. All credit for the core AI, speech model, and research innovation belongs to the original authors and contributors.

**Windows one-click installer & packaging**  
The Windows one-click setup, automation scripts, and launchers in this repo were created by **Suresh Pydikondala**, with the goal of making PersonaPlex easier to install, test, and run on Windows without complex manual setup.

This repository does not modify the fundamental model or research logic—it focuses on **accessibility, automation, and practical usability** on Windows.

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

## Hardware testing & environment

This setup has been personally tested by the maintainer on:

| Component | Tested configuration |
|-----------|------------------------|
| **OS**    | Windows 10/11          |
| **GPU**   | NVIDIA RTX 4090        |
| **VRAM**  | 24 GB                  |

Performance, stability, and behavior may vary on your system (GPU model, VRAM, CPU, RAM, drivers, OS). Please test and tune parameters according to your own hardware.

---

## Known issues & observations

Based on personal testing, the following are known and originate from the **upstream** codebase (not from this Windows installer):

- **Optimization:** Some parts of the pipeline are not fully optimized yet, which may lead to higher GPU usage or occasional inefficiencies.
- **Voice response looping:** In certain scenarios, the AI voice may enter a loop and repeat replies. When it does not loop, responses are often accurate and natural.

These are shared as practical observations to set expectations. For core model issues or research discussions, please refer to the [original PersonaPlex repository](https://github.com/NVIDIA/personaplex).

---

## Disclaimer

This project is provided as a **community convenience wrapper** around the original PersonaPlex work. For core model issues, research discussions, or fundamental behavior, please refer to the [original PersonaPlex repository and authors](https://github.com/NVIDIA/personaplex).

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
