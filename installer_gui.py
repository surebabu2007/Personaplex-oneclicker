#!/usr/bin/env python3
"""
PersonaPlex One-Click Installer GUI
A user-friendly graphical installer for PersonaPlex
Created by SurAiverse - https://www.youtube.com/@suraiverse
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
import subprocess
import sys
import os
import shutil
from pathlib import Path
import json
import re

# Version info
INSTALLER_VERSION = "1.0.1"
YOUTUBE_CHANNEL = "https://www.youtube.com/@suraiverse"
HUGGINGFACE_TOKEN_URL = "https://huggingface.co/settings/tokens"
HUGGINGFACE_LICENSE_URL = "https://huggingface.co/nvidia/personaplex-7b-v1"

# Required model files
REQUIRED_MODELS = {
    "model.safetensors": {"size_mb": 15400, "description": "Main Moshi LM model (~15GB)"},
    "tokenizer-e351c8d8-checkpoint125.safetensors": {"size_mb": 385, "description": "Audio encoder/decoder (~385MB)"},
    "tokenizer_spm_32k_3.model": {"size_mb": 0.55, "description": "Text tokenizer (~553KB)"},
}


class SurAiverseTheme:
    """Color theme for SurAiverse branding"""
    # Primary colors
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#16213e"
    BG_LIGHT = "#0f3460"
    
    # Accent colors
    ACCENT_PRIMARY = "#00d4ff"
    ACCENT_SECONDARY = "#e94560"
    ACCENT_SUCCESS = "#00ff88"
    ACCENT_WARNING = "#ffaa00"
    ACCENT_ERROR = "#ff4444"
    
    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_MUTED = "#707070"
    
    # Button colors
    BTN_PRIMARY = "#00d4ff"
    BTN_HOVER = "#00a8cc"
    BTN_TEXT = "#1a1a2e"


class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PersonaPlex Installer - by SurAiverse")
        self.root.geometry("700x750")  # Increased height for better content visibility
        self.root.resizable(False, False)
        self.root.configure(bg=SurAiverseTheme.BG_DARK)
        
        # Try to set icon (if available)
        try:
            # Windows icon
            self.root.iconbitmap(default='')
        except:
            pass
        
        # Center window
        self.center_window()
        
        # Variables
        self.install_mode = tk.StringVar(value="fresh")
        self.hf_token = tk.StringVar()
        self.save_token = tk.BooleanVar(value=True)
        self.model_source = tk.StringVar(value="download")
        self.custom_model_path = tk.StringVar()
        self.current_step = 0
        self.installation_thread = None
        self.cancel_flag = False
        
        # Track which Python to use
        self.python_exe = sys.executable
        self.pip_exe = None
        self.nodejs_available = False
        
        # Frames for each screen
        self.frames = {}
        self.create_frames()
        
        # Show welcome screen
        self.show_frame("welcome")
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_frames(self):
        """Create all installer frames/screens"""
        self.create_welcome_frame()
        self.create_mode_frame()
        self.create_token_frame()
        self.create_models_frame()
        self.create_progress_frame()
        self.create_success_frame()
        self.create_error_frame()
    
    def show_frame(self, frame_name):
        """Show a specific frame and hide others"""
        for name, frame in self.frames.items():
            if name == frame_name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
    
    def create_styled_button(self, parent, text, command, style="primary", width=20):
        """Create a styled button"""
        if style == "primary":
            bg = SurAiverseTheme.BTN_PRIMARY
            fg = SurAiverseTheme.BTN_TEXT
        elif style == "secondary":
            bg = SurAiverseTheme.BG_LIGHT
            fg = SurAiverseTheme.TEXT_PRIMARY
        elif style == "success":
            bg = SurAiverseTheme.ACCENT_SUCCESS
            fg = SurAiverseTheme.BTN_TEXT
        elif style == "danger":
            bg = SurAiverseTheme.ACCENT_ERROR
            fg = SurAiverseTheme.TEXT_PRIMARY
        else:
            bg = SurAiverseTheme.BG_LIGHT
            fg = SurAiverseTheme.TEXT_PRIMARY
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            width=width,
            pady=8
        )
        return btn
    
    def create_header(self, parent, title, subtitle=None):
        """Create a header section with branding"""
        header = tk.Frame(parent, bg=SurAiverseTheme.BG_DARK)
        header.pack(fill="x", pady=(20, 10))
        
        # Logo/Brand text
        brand_frame = tk.Frame(header, bg=SurAiverseTheme.BG_DARK)
        brand_frame.pack()
        
        logo_text = tk.Label(
            brand_frame,
            text="PersonaPlex",
            font=("Segoe UI", 28, "bold"),
            fg=SurAiverseTheme.ACCENT_PRIMARY,
            bg=SurAiverseTheme.BG_DARK
        )
        logo_text.pack()
        
        subtitle_label = tk.Label(
            brand_frame,
            text="by SurAiverse",
            font=("Segoe UI", 12),
            fg=SurAiverseTheme.ACCENT_SECONDARY,
            bg=SurAiverseTheme.BG_DARK
        )
        subtitle_label.pack()
        
        if title:
            title_label = tk.Label(
                header,
                text=title,
                font=("Segoe UI", 16, "bold"),
                fg=SurAiverseTheme.TEXT_PRIMARY,
                bg=SurAiverseTheme.BG_DARK
            )
            title_label.pack(pady=(15, 5))
        
        if subtitle:
            sub_label = tk.Label(
                header,
                text=subtitle,
                font=("Segoe UI", 10),
                fg=SurAiverseTheme.TEXT_SECONDARY,
                bg=SurAiverseTheme.BG_DARK
            )
            sub_label.pack()
        
        return header
    
    def create_footer(self, parent):
        """Create footer with YouTube link"""
        footer = tk.Frame(parent, bg=SurAiverseTheme.BG_MEDIUM)
        footer.pack(side="bottom", fill="x", pady=0)
        
        inner = tk.Frame(footer, bg=SurAiverseTheme.BG_MEDIUM)
        inner.pack(pady=10)
        
        yt_label = tk.Label(
            inner,
            text="Subscribe for AI tutorials: ",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        yt_label.pack(side="left")
        
        yt_link = tk.Label(
            inner,
            text="youtube.com/@suraiverse",
            font=("Segoe UI", 9, "underline"),
            fg=SurAiverseTheme.ACCENT_PRIMARY,
            bg=SurAiverseTheme.BG_MEDIUM,
            cursor="hand2"
        )
        yt_link.pack(side="left")
        yt_link.bind("<Button-1>", lambda e: webbrowser.open(YOUTUBE_CHANNEL))
        
        return footer
    
    # ==================== WELCOME SCREEN ====================
    def create_welcome_frame(self):
        """Create the welcome/landing screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["welcome"] = frame
        
        self.create_header(frame, None, None)
        
        # Welcome message
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        welcome_text = tk.Label(
            content,
            text="Welcome to the One-Click Installer",
            font=("Segoe UI", 18),
            fg=SurAiverseTheme.TEXT_PRIMARY,
            bg=SurAiverseTheme.BG_DARK
        )
        welcome_text.pack(pady=(20, 10))
        
        desc_text = """This installer will guide you through setting up PersonaPlex,
an AI-powered voice conversation system.

What this installer does:
  • Check system requirements (Python, Node.js, NVIDIA GPU)
  • Create a virtual environment
  • Install all dependencies
  • Build the web interface (client)
  • Set up HuggingFace authentication
  • Download or link AI models (~14GB)
  • Configure everything automatically"""
        
        desc_label = tk.Label(
            content,
            text=desc_text,
            font=("Segoe UI", 10),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_DARK,
            justify="left"
        )
        desc_label.pack(pady=20)
        
        # Buttons
        btn_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        btn_frame.pack(pady=20)
        
        start_btn = self.create_styled_button(
            btn_frame,
            "Start Installation",
            lambda: self.show_frame("mode"),
            style="primary",
            width=25
        )
        start_btn.pack(pady=5)
        
        exit_btn = self.create_styled_button(
            btn_frame,
            "Exit",
            self.root.quit,
            style="secondary",
            width=25
        )
        exit_btn.pack(pady=5)
        
        self.create_footer(frame)
    
    # ==================== MODE SELECTION SCREEN ====================
    def create_mode_frame(self):
        """Create installation mode selection screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["mode"] = frame
        
        self.create_header(frame, "Installation Mode", "Choose how you want to install PersonaPlex")
        
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        # Radio button style
        radio_style = {
            "font": ("Segoe UI", 11),
            "fg": SurAiverseTheme.TEXT_PRIMARY,
            "bg": SurAiverseTheme.BG_DARK,
            "selectcolor": SurAiverseTheme.BG_MEDIUM,
            "activebackground": SurAiverseTheme.BG_DARK,
            "activeforeground": SurAiverseTheme.ACCENT_PRIMARY,
            "cursor": "hand2"
        }
        
        # Fresh Install option
        fresh_frame = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=15, pady=10)
        fresh_frame.pack(fill="x", pady=5)
        
        fresh_radio = tk.Radiobutton(
            fresh_frame,
            text="Fresh Install (Recommended)",
            variable=self.install_mode,
            value="fresh",
            **radio_style
        )
        fresh_radio.configure(bg=SurAiverseTheme.BG_MEDIUM)
        fresh_radio.pack(anchor="w")
        
        fresh_desc = tk.Label(
            fresh_frame,
            text="Complete clean installation. Removes any existing setup and starts fresh.",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_MUTED,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        fresh_desc.pack(anchor="w", padx=25)
        
        # Update/Repair option
        update_frame = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=15, pady=10)
        update_frame.pack(fill="x", pady=5)
        
        update_radio = tk.Radiobutton(
            update_frame,
            text="Update / Repair",
            variable=self.install_mode,
            value="update",
            **radio_style
        )
        update_radio.configure(bg=SurAiverseTheme.BG_MEDIUM)
        update_radio.pack(anchor="w")
        
        update_desc = tk.Label(
            update_frame,
            text="Keep existing virtual environment, update dependencies and verify models.",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_MUTED,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        update_desc.pack(anchor="w", padx=25)
        
        # Models Only option
        models_frame = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=15, pady=10)
        models_frame.pack(fill="x", pady=5)
        
        models_radio = tk.Radiobutton(
            models_frame,
            text="Models Only",
            variable=self.install_mode,
            value="models",
            **radio_style
        )
        models_radio.configure(bg=SurAiverseTheme.BG_MEDIUM)
        models_radio.pack(anchor="w")
        
        models_desc = tk.Label(
            models_frame,
            text="Only download/configure models. Use if Python setup is already complete.",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_MUTED,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        models_desc.pack(anchor="w", padx=25)
        
        # Buttons
        btn_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        btn_frame.pack(pady=20)
        
        back_btn = self.create_styled_button(
            btn_frame,
            "Back",
            lambda: self.show_frame("welcome"),
            style="secondary",
            width=12
        )
        back_btn.pack(side="left", padx=10)
        
        next_btn = self.create_styled_button(
            btn_frame,
            "Next",
            lambda: self.show_frame("token"),
            style="primary",
            width=12
        )
        next_btn.pack(side="left", padx=10)
        
        self.create_footer(frame)
    
    # ==================== HUGGINGFACE TOKEN SCREEN ====================
    def create_token_frame(self):
        """Create HuggingFace token entry screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["token"] = frame
        
        self.create_header(frame, "HuggingFace Authentication", 
                          "A token is required to download the AI models")
        
        # Main content area (will grow to fill space)
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        # Instructions - made more compact
        instructions = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=15, pady=10)
        instructions.pack(fill="x", pady=(5, 10))
        
        steps_title = tk.Label(
            instructions,
            text="How to get your HuggingFace token:",
            font=("Segoe UI", 10, "bold"),
            fg=SurAiverseTheme.ACCENT_PRIMARY,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        steps_title.pack(anchor="w")
        
        steps_text = """1. Click the button below to open HuggingFace in your browser
2. Create an account or log in if you haven't already
3. Go to Settings > Access Tokens
4. Create a new token (Read access is sufficient)
5. Copy the token and paste it below

Important: You must also accept the model license at:
huggingface.co/nvidia/personaplex-7b-v1"""
        
        steps_label = tk.Label(
            instructions,
            text=steps_text,
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_MEDIUM,
            justify="left"
        )
        steps_label.pack(anchor="w")
        
        # Buttons to open URLs
        url_frame = tk.Frame(instructions, bg=SurAiverseTheme.BG_MEDIUM)
        url_frame.pack(anchor="w", pady=(8, 0))
        
        token_url_btn = self.create_styled_button(
            url_frame,
            "Get Token",
            lambda: webbrowser.open(HUGGINGFACE_TOKEN_URL),
            style="primary",
            width=15
        )
        token_url_btn.pack(side="left", padx=(0, 10))
        
        license_url_btn = self.create_styled_button(
            url_frame,
            "Accept License",
            lambda: webbrowser.open(HUGGINGFACE_LICENSE_URL),
            style="secondary",
            width=15
        )
        license_url_btn.pack(side="left")
        
        # Token entry
        entry_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        entry_frame.pack(fill="x", pady=(10, 5))
        
        token_label = tk.Label(
            entry_frame,
            text="Enter your HuggingFace token:",
            font=("Segoe UI", 10),
            fg=SurAiverseTheme.TEXT_PRIMARY,
            bg=SurAiverseTheme.BG_DARK
        )
        token_label.pack(anchor="w")
        
        token_entry = tk.Entry(
            entry_frame,
            textvariable=self.hf_token,
            font=("Consolas", 10),
            bg=SurAiverseTheme.BG_MEDIUM,
            fg=SurAiverseTheme.TEXT_PRIMARY,
            insertbackground=SurAiverseTheme.ACCENT_PRIMARY,
            relief="flat",
            width=50,
            show="*"
        )
        token_entry.pack(fill="x", pady=(5, 8), ipady=6)
        
        # Save checkbox
        save_check = tk.Checkbutton(
            entry_frame,
            text="Save token permanently (recommended)",
            variable=self.save_token,
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_DARK,
            selectcolor=SurAiverseTheme.BG_MEDIUM,
            activebackground=SurAiverseTheme.BG_DARK,
            activeforeground=SurAiverseTheme.TEXT_PRIMARY
        )
        save_check.pack(anchor="w")
        
        # Validation message
        self.token_message = tk.Label(
            entry_frame,
            text="",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.ACCENT_WARNING,
            bg=SurAiverseTheme.BG_DARK
        )
        self.token_message.pack(anchor="w", pady=(3, 0))

        if os.environ.get("HF_TOKEN"):
            self.token_message.config(
                text="A token was detected in your environment. Leave blank to use it.",
                fg=SurAiverseTheme.TEXT_SECONDARY
            )
        
        # Navigation buttons - fixed at bottom before footer
        btn_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        btn_frame.pack(side="bottom", pady=(15, 10))
        
        back_btn = self.create_styled_button(
            btn_frame,
            "Back",
            lambda: self.show_frame("mode"),
            style="secondary",
            width=12
        )
        back_btn.pack(side="left", padx=10)
        
        next_btn = self.create_styled_button(
            btn_frame,
            "Next",
            self.validate_token_and_continue,
            style="primary",
            width=12
        )
        next_btn.pack(side="left", padx=10)
        
        self.create_footer(frame)
    
    def validate_token_and_continue(self):
        """Validate the HuggingFace token before proceeding"""
        token = self.hf_token.get().strip()

        if not token:
            if os.environ.get("HF_TOKEN"):
                self.token_message.config(
                    text="Using token from environment.",
                    fg=SurAiverseTheme.ACCENT_SUCCESS
                )
                self.show_frame("models")
                return
            self.token_message.config(
                text="Warning: No token provided. Model downloads may fail.",
                fg=SurAiverseTheme.ACCENT_WARNING
            )
            # Allow continuing without token (models might be cached)
            if messagebox.askyesno("Continue without token?", 
                "No token was provided. Model downloads may fail if you haven't downloaded them before.\n\nContinue anyway?"):
                self.show_frame("models")
            return
        
        if not token.startswith("hf_"):
            self.token_message.config(
                text="Warning: Token doesn't start with 'hf_'. This may not be valid.",
                fg=SurAiverseTheme.ACCENT_WARNING
            )
        else:
            self.token_message.config(
                text="Token format looks valid!",
                fg=SurAiverseTheme.ACCENT_SUCCESS
            )
        
        # Save token if requested
        if self.save_token.get() and token:
            try:
                # Set for current session
                os.environ["HF_TOKEN"] = token
                # Save permanently using setx (Windows)
                subprocess.run(["setx", "HF_TOKEN", token], 
                             capture_output=True, check=False)
            except Exception as e:
                print(f"Could not save token permanently: {e}")
        
        self.show_frame("models")
    
    # ==================== MODEL SELECTION SCREEN ====================
    def create_models_frame(self):
        """Create model source selection screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["models"] = frame
        
        self.create_header(frame, "Model Configuration", 
                          "Choose where to get the AI models (~14GB)")
        
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        radio_style = {
            "font": ("Segoe UI", 11),
            "fg": SurAiverseTheme.TEXT_PRIMARY,
            "bg": SurAiverseTheme.BG_DARK,
            "selectcolor": SurAiverseTheme.BG_MEDIUM,
            "activebackground": SurAiverseTheme.BG_DARK,
            "activeforeground": SurAiverseTheme.ACCENT_PRIMARY,
            "cursor": "hand2"
        }
        
        # Download option
        dl_frame = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=15, pady=10)
        dl_frame.pack(fill="x", pady=5)
        
        dl_radio = tk.Radiobutton(
            dl_frame,
            text="Download from HuggingFace (Recommended)",
            variable=self.model_source,
            value="download",
            command=self.toggle_model_path,
            **radio_style
        )
        dl_radio.configure(bg=SurAiverseTheme.BG_MEDIUM)
        dl_radio.pack(anchor="w")
        
        dl_desc = tk.Label(
            dl_frame,
            text="Automatically download all required models (~14GB). Requires internet connection.",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_MUTED,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        dl_desc.pack(anchor="w", padx=25)
        
        # Use existing option
        existing_frame = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=15, pady=10)
        existing_frame.pack(fill="x", pady=5)
        
        existing_radio = tk.Radiobutton(
            existing_frame,
            text="Use existing models from local folder",
            variable=self.model_source,
            value="existing",
            command=self.toggle_model_path,
            **radio_style
        )
        existing_radio.configure(bg=SurAiverseTheme.BG_MEDIUM)
        existing_radio.pack(anchor="w")
        
        existing_desc = tk.Label(
            existing_frame,
            text="Select a folder containing previously downloaded model files.",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_MUTED,
            bg=SurAiverseTheme.BG_MEDIUM
        )
        existing_desc.pack(anchor="w", padx=25)
        
        # Path selection (initially hidden)
        self.path_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        
        path_label = tk.Label(
            self.path_frame,
            text="Model folder path:",
            font=("Segoe UI", 10),
            fg=SurAiverseTheme.TEXT_PRIMARY,
            bg=SurAiverseTheme.BG_DARK
        )
        path_label.pack(anchor="w")
        
        path_entry_frame = tk.Frame(self.path_frame, bg=SurAiverseTheme.BG_DARK)
        path_entry_frame.pack(fill="x", pady=5)
        
        path_entry = tk.Entry(
            path_entry_frame,
            textvariable=self.custom_model_path,
            font=("Segoe UI", 10),
            bg=SurAiverseTheme.BG_MEDIUM,
            fg=SurAiverseTheme.TEXT_PRIMARY,
            insertbackground=SurAiverseTheme.ACCENT_PRIMARY,
            relief="flat"
        )
        path_entry.pack(side="left", fill="x", expand=True, ipady=6)
        
        browse_btn = self.create_styled_button(
            path_entry_frame,
            "Browse",
            self.browse_model_folder,
            style="secondary",
            width=10
        )
        browse_btn.pack(side="left", padx=(10, 0))
        
        # Model files info
        self.model_info_label = tk.Label(
            self.path_frame,
            text="",
            font=("Segoe UI", 9),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_DARK,
            justify="left"
        )
        self.model_info_label.pack(anchor="w", pady=(10, 0))
        
        # Required files list
        files_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        files_frame.pack(fill="x", pady=15)
        
        files_title = tk.Label(
            files_frame,
            text="Required model files:",
            font=("Segoe UI", 10, "bold"),
            fg=SurAiverseTheme.TEXT_PRIMARY,
            bg=SurAiverseTheme.BG_DARK
        )
        files_title.pack(anchor="w")
        
        for filename, info in REQUIRED_MODELS.items():
            file_label = tk.Label(
                files_frame,
                text=f"  • {filename} - {info['description']}",
                font=("Segoe UI", 9),
                fg=SurAiverseTheme.TEXT_MUTED,
                bg=SurAiverseTheme.BG_DARK
            )
            file_label.pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        btn_frame.pack(pady=20)
        
        back_btn = self.create_styled_button(
            btn_frame,
            "Back",
            lambda: self.show_frame("token"),
            style="secondary",
            width=12
        )
        back_btn.pack(side="left", padx=10)
        
        install_btn = self.create_styled_button(
            btn_frame,
            "Install",
            self.start_installation,
            style="success",
            width=12
        )
        install_btn.pack(side="left", padx=10)
        
        self.create_footer(frame)
    
    def toggle_model_path(self):
        """Show/hide the model path selection based on radio choice"""
        if self.model_source.get() == "existing":
            self.path_frame.pack(fill="x", pady=10)
        else:
            self.path_frame.pack_forget()
    
    def browse_model_folder(self):
        """Open file browser for model folder selection"""
        folder = filedialog.askdirectory(
            title="Select folder containing model files"
        )
        if folder:
            self.custom_model_path.set(folder)
            self.validate_model_folder(folder)
    
    def validate_model_folder(self, folder):
        """Check if the folder contains required model files"""
        found = []
        missing = []
        
        for filename in REQUIRED_MODELS.keys():
            filepath = os.path.join(folder, filename)
            if os.path.exists(filepath):
                found.append(filename)
            else:
                missing.append(filename)
        
        if missing:
            self.model_info_label.config(
                text=f"Found {len(found)}/{len(REQUIRED_MODELS)} files. Missing: {', '.join(missing)}",
                fg=SurAiverseTheme.ACCENT_WARNING
            )
        else:
            self.model_info_label.config(
                text=f"All {len(REQUIRED_MODELS)} required files found!",
                fg=SurAiverseTheme.ACCENT_SUCCESS
            )
    
    # ==================== PROGRESS SCREEN ====================
    def create_progress_frame(self):
        """Create installation progress screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["progress"] = frame
        
        self.create_header(frame, "Installing PersonaPlex", "Please wait while we set up everything...")
        
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        
        progress_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        progress_frame.pack(fill="x", pady=20)
        
        style = ttk.Style()
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=SurAiverseTheme.BG_MEDIUM,
            background=SurAiverseTheme.ACCENT_PRIMARY,
            thickness=20
        )
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            style="Custom.Horizontal.TProgressbar",
            length=500
        )
        self.progress_bar.pack(fill="x")
        
        # Step indicator
        self.step_label = tk.Label(
            content,
            text="Preparing...",
            font=("Segoe UI", 12, "bold"),
            fg=SurAiverseTheme.ACCENT_PRIMARY,
            bg=SurAiverseTheme.BG_DARK
        )
        self.step_label.pack(pady=10)
        
        # Detail log
        log_frame = tk.Frame(content, bg=SurAiverseTheme.BG_MEDIUM, padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, pady=10)
        
        self.log_text = tk.Text(
            log_frame,
            height=12,
            font=("Consolas", 9),
            bg=SurAiverseTheme.BG_MEDIUM,
            fg=SurAiverseTheme.TEXT_SECONDARY,
            relief="flat",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        # Cancel button
        self.cancel_btn = self.create_styled_button(
            content,
            "Cancel",
            self.cancel_installation,
            style="danger",
            width=15
        )
        self.cancel_btn.pack(pady=10)
        
        self.create_footer(frame)
    
    def log(self, message, level="info"):
        """Add a message to the log"""
        prefix = {
            "info": "[INFO] ",
            "success": "[OK] ",
            "warning": "[WARNING] ",
            "error": "[ERROR] "
        }.get(level, "")
        
        self.log_text.insert("end", f"{prefix}{message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def update_progress(self, value, step_text=None):
        """Update the progress bar and step text"""
        self.progress_var.set(value)
        if step_text:
            self.step_label.config(text=step_text)
        self.root.update_idletasks()
    
    # ==================== SUCCESS SCREEN ====================
    def create_success_frame(self):
        """Create installation success screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["success"] = frame
        
        self.create_header(frame, None, None)
        
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        # Success icon (using text)
        success_icon = tk.Label(
            content,
            text="✓",
            font=("Segoe UI", 72),
            fg=SurAiverseTheme.ACCENT_SUCCESS,
            bg=SurAiverseTheme.BG_DARK
        )
        success_icon.pack(pady=20)
        
        success_title = tk.Label(
            content,
            text="Installation Complete!",
            font=("Segoe UI", 20, "bold"),
            fg=SurAiverseTheme.ACCENT_SUCCESS,
            bg=SurAiverseTheme.BG_DARK
        )
        success_title.pack()
        
        self.success_text_var = tk.StringVar()
        self.success_text_var.set("""PersonaPlex has been successfully installed and configured!

You can now launch PersonaPlex by:
  • Double-clicking START_PERSONAPLEX.bat
  • Or using the LAUNCHER.bat menu

The server includes a built-in web interface (no Node.js required).
The first launch will download AI models if needed (~14GB).
Server will be available at: https://localhost:8998""")
        
        success_text = self.success_text_var.get()
        
        self.success_label = tk.Label(
            content,
            textvariable=self.success_text_var,
            font=("Segoe UI", 10),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_DARK,
            justify="left"
        )
        self.success_label.pack(pady=20)
        
        # Buttons
        btn_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        btn_frame.pack(pady=20)
        
        launch_btn = self.create_styled_button(
            btn_frame,
            "Launch PersonaPlex",
            self.launch_personaplex,
            style="success",
            width=20
        )
        launch_btn.pack(pady=5)
        
        close_btn = self.create_styled_button(
            btn_frame,
            "Close Installer",
            self.root.quit,
            style="secondary",
            width=20
        )
        close_btn.pack(pady=5)
        
        self.create_footer(frame)
    
    # ==================== ERROR SCREEN ====================
    def create_error_frame(self):
        """Create installation error screen"""
        frame = tk.Frame(self.root, bg=SurAiverseTheme.BG_DARK)
        self.frames["error"] = frame
        
        self.create_header(frame, None, None)
        
        content = tk.Frame(frame, bg=SurAiverseTheme.BG_DARK)
        content.pack(expand=True, fill="both", padx=40)
        
        # Error icon
        error_icon = tk.Label(
            content,
            text="✗",
            font=("Segoe UI", 72),
            fg=SurAiverseTheme.ACCENT_ERROR,
            bg=SurAiverseTheme.BG_DARK
        )
        error_icon.pack(pady=20)
        
        error_title = tk.Label(
            content,
            text="Installation Failed",
            font=("Segoe UI", 20, "bold"),
            fg=SurAiverseTheme.ACCENT_ERROR,
            bg=SurAiverseTheme.BG_DARK
        )
        error_title.pack()
        
        self.error_message = tk.Label(
            content,
            text="An error occurred during installation.",
            font=("Segoe UI", 10),
            fg=SurAiverseTheme.TEXT_SECONDARY,
            bg=SurAiverseTheme.BG_DARK,
            wraplength=500,
            justify="left"
        )
        self.error_message.pack(pady=20)
        
        # Buttons
        btn_frame = tk.Frame(content, bg=SurAiverseTheme.BG_DARK)
        btn_frame.pack(pady=20)
        
        retry_btn = self.create_styled_button(
            btn_frame,
            "Try Again",
            lambda: self.show_frame("mode"),
            style="primary",
            width=15
        )
        retry_btn.pack(side="left", padx=10)
        
        help_btn = self.create_styled_button(
            btn_frame,
            "Get Help",
            lambda: webbrowser.open(YOUTUBE_CHANNEL),
            style="secondary",
            width=15
        )
        help_btn.pack(side="left", padx=10)
        
        close_btn = self.create_styled_button(
            btn_frame,
            "Close",
            self.root.quit,
            style="danger",
            width=15
        )
        close_btn.pack(side="left", padx=10)
        
        self.create_footer(frame)
    
    def show_error(self, message):
        """Show the error screen with a specific message"""
        self.error_message.config(text=message)
        self.show_frame("error")
    
    # ==================== INSTALLATION LOGIC ====================
    def start_installation(self):
        """Start the installation process in a separate thread"""
        self.cancel_flag = False
        self.show_frame("progress")
        self.log_text.delete("1.0", "end")
        
        self.installation_thread = threading.Thread(target=self.run_installation)
        self.installation_thread.start()
    
    def cancel_installation(self):
        """Cancel the ongoing installation"""
        if messagebox.askyesno("Cancel Installation", 
            "Are you sure you want to cancel the installation?"):
            self.cancel_flag = True
            self.cancel_btn.config(state="disabled")
            self.log("Cancelling installation...", "warning")
    
    def run_installation(self):
        """Main installation routine"""
        try:
            mode = self.install_mode.get()
            
            # Step 1: System checks
            self.update_progress(5, "Checking system requirements...")
            self.log("Checking system requirements...")
            
            if not self.check_python():
                return
            
            if self.cancel_flag:
                self.log("Installation cancelled by user.", "warning")
                return
            
            # Check internet (important for downloads)
            has_internet = self.check_internet_connection()
            if not has_internet and self.model_source.get() == "download":
                self.log("Internet required for model downloads!", "error")
                self.root.after(100, lambda: self.show_error(
                    "No internet connection detected.\n\n"
                    "Internet is required to download models from HuggingFace.\n\n"
                    "Options:\n"
                    "1. Check your network connection and try again\n"
                    "2. Use 'existing models' option if you have them locally\n"
                    "3. Download models on another computer and transfer"
                ))
                return
            
            self.check_gpu()
            self.check_nodejs()
            self.check_disk_space()
            
            if self.cancel_flag:
                return
            
            # Step 2: Clean up if fresh install
            if mode == "fresh":
                self.update_progress(10, "Performing fresh install cleanup...")
                self.log("Removing existing virtual environment...")
                self.cleanup_existing()
            
            if self.cancel_flag:
                return
            
            # Step 3: Create virtual environment (unless models only)
            if mode != "models":
                self.update_progress(20, "Creating virtual environment...")
                if not self.create_venv():
                    return
            
            if self.cancel_flag:
                return
            
            # Step 4: Install dependencies (unless models only)
            if mode != "models":
                self.update_progress(30, "Installing dependencies...")
                if not self.install_dependencies():
                    return
            
            if self.cancel_flag:
                return
            
            # Step 5: Build client (web UI)
            if mode != "models":
                self.update_progress(55, "Building web interface...")
                if not self.build_client():
                    return
            
            if self.cancel_flag:
                return
            
            # Step 6: Handle models
            self.update_progress(65, "Setting up models...")
            if not self.setup_models():
                return
            
            if self.cancel_flag:
                return
            
            # Step 7: Verify installation
            self.update_progress(90, "Verifying installation...")
            if not self.verify_installation():
                return
            
            # Done!
            self.update_progress(100, "Installation complete!")
            self.log("Installation completed successfully!", "success")
            
            # Show success screen
            self.root.after(1000, lambda: self.show_frame("success"))
            
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}", "error")
            self.root.after(100, lambda: self.show_error(
                f"An unexpected error occurred:\n\n{str(e)}\n\n"
                "Please check the log above for details."
            ))
    
    def check_python(self):
        """Check Python version"""
        self.log(f"Python version: {sys.version}")
        
        major = sys.version_info.major
        minor = sys.version_info.minor
        
        if major < 3 or (major == 3 and minor < 10):
            self.log(f"Python 3.10+ required, found {major}.{minor}", "error")
            self.root.after(100, lambda: self.show_error(
                f"Python 3.10 or higher is required.\n\n"
                f"You have Python {major}.{minor} installed.\n\n"
                f"Please download Python 3.10+ from:\n"
                f"https://www.python.org/downloads/\n\n"
                f"IMPORTANT: Check 'Add Python to PATH' during installation!"
            ))
            return False
        
        self.log(f"Python version OK: {major}.{minor}", "success")
        return True
    
    def check_internet_connection(self):
        """Check if internet is available"""
        self.log("Checking internet connection...")
        import socket
        
        test_hosts = [
            ("huggingface.co", 443),
            ("github.com", 443),
            ("google.com", 443),
        ]
        
        for host, port in test_hosts:
            try:
                socket.create_connection((host, port), timeout=5)
                self.log(f"Internet connection OK (reached {host})", "success")
                return True
            except (socket.timeout, socket.error):
                continue
        
        self.log("No internet connection detected", "warning")
        return False
    
    def check_admin_rights(self):
        """Check if running with admin rights (Windows)"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def check_gpu(self):
        """Check for NVIDIA GPU"""
        self.log("Checking for NVIDIA GPU...")
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                gpu_name = result.stdout.strip()
                self.log(f"NVIDIA GPU detected: {gpu_name}", "success")
            else:
                self.log("NVIDIA GPU not detected. CPU mode will be used.", "warning")
        except FileNotFoundError:
            self.log("nvidia-smi not found. GPU may not be available.", "warning")
        except Exception as e:
            self.log(f"GPU check failed: {e}", "warning")
    
    def check_nodejs(self):
        """Node.js is NOT required - skip check entirely"""
        # Server has embedded web client, no Node.js needed
        self.nodejs_available = False
        return True
    
    def check_disk_space(self):
        """Check available disk space"""
        self.log("Checking disk space...")
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            self.log(f"Available disk space: {free_gb:.1f} GB")
            
            if free_gb < 20:
                self.log("Warning: Less than 20GB available. Models need ~14GB.", "warning")
            else:
                self.log("Disk space OK", "success")
        except Exception as e:
            self.log(f"Could not check disk space: {e}", "warning")
    
    def cleanup_existing(self):
        """Clean up existing installation for fresh install"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        venv_path = os.path.join(script_dir, "venv")
        
        if os.path.exists(venv_path):
            self.log("Removing existing virtual environment...")
            try:
                shutil.rmtree(venv_path)
                self.log("Virtual environment removed", "success")
            except Exception as e:
                self.log(f"Could not remove venv: {e}", "warning")
        
        # Clean __pycache__ directories
        for root, dirs, files in os.walk(script_dir):
            for d in dirs:
                if d == "__pycache__":
                    try:
                        shutil.rmtree(os.path.join(root, d))
                    except:
                        pass
        
        self.log("Cleanup complete", "success")
    
    def create_venv(self):
        """Create virtual environment"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        venv_path = os.path.join(script_dir, "venv")
        
        # Check if venv already exists
        venv_python = os.path.join(venv_path, "Scripts", "python.exe")
        if os.path.exists(venv_python):
            self.log("Virtual environment already exists", "success")
            self.python_exe = venv_python
            self.pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
            return True
        
        self.log("Creating virtual environment...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "venv", venv_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                self.log(f"Failed to create venv: {result.stderr}", "error")
                self.root.after(100, lambda: self.show_error(
                    "Failed to create virtual environment.\n\n"
                    "This can happen if:\n"
                    "1. Antivirus software blocked the operation\n"
                    "2. Insufficient disk space\n"
                    "3. Permission issues\n\n"
                    "Try running the installer as Administrator,\n"
                    "or temporarily disable antivirus software."
                ))
                return False
            
            self.log("Virtual environment created", "success")
            self.python_exe = venv_python
            self.pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Virtual environment creation timed out", "error")
            self.root.after(100, lambda: self.show_error(
                "Virtual environment creation timed out.\n\n"
                "This can happen on slower systems.\n"
                "Please try again."
            ))
            return False
        except Exception as e:
            self.log(f"Error creating venv: {e}", "error")
            self.root.after(100, lambda: self.show_error(
                f"Failed to create virtual environment.\n\n"
                f"Error: {str(e)}\n\n"
                "Try running the installer as Administrator."
            ))
            return False
    
    def install_dependencies(self):
        """Install all required dependencies"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use the virtual environment Python
        python_exe = self.python_exe
        if not os.path.exists(python_exe):
            self.log("Virtual environment Python not found", "error")
            self.root.after(100, lambda: self.show_error(
                "Virtual environment was not created properly.\n\n"
                "This can happen if:\n"
                "1. Antivirus software blocked the operation\n"
                "2. Insufficient disk space\n"
                "3. Permission issues\n\n"
                "Try running the installer as Administrator,\n"
                "or temporarily disable antivirus software."
            ))
            return False
        
        # Upgrade pip
        self.log("Upgrading pip...")
        self.update_progress(35, "Upgrading pip...")
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            self.log("Could not upgrade pip, continuing anyway...", "warning")
        
        # Uninstall existing PyTorch to avoid conflicts
        self.log("Removing any existing PyTorch installation...")
        subprocess.run(
            [python_exe, "-m", "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y", "--quiet"],
            capture_output=True,
            timeout=60
        )
        
        # Install PyTorch with CUDA
        self.log("Installing PyTorch with CUDA support...")
        self.log("This may take 5-10 minutes depending on your internet speed.")
        self.update_progress(40, "Installing PyTorch (5-10 min)...")
        
        pytorch_installed = False
        pytorch_errors = []
        
        # Try CUDA 12.4 first
        cuda_versions = [
            ("CUDA 12.4", "https://download.pytorch.org/whl/cu124"),
            ("CUDA 11.8", "https://download.pytorch.org/whl/cu118"),
            ("CPU only", None),
        ]
        
        for cuda_name, index_url in cuda_versions:
            if pytorch_installed:
                break
                
            self.log(f"Trying PyTorch with {cuda_name}...")
            
            pytorch_cmd = [
                python_exe, "-m", "pip", "install",
                "torch>=2.4.0,<2.5",
                "torchvision>=0.19,<0.20", 
                "torchaudio>=2.4,<2.5",
            ]
            
            if index_url:
                pytorch_cmd.extend(["--index-url", index_url])
            
            pytorch_cmd.append("--quiet")
            
            try:
                result = subprocess.run(
                    pytorch_cmd, 
                    capture_output=True, 
                    text=True,
                    timeout=1800  # 30 min timeout
                )
                
                if result.returncode == 0:
                    self.log(f"PyTorch with {cuda_name} installed", "success")
                    pytorch_installed = True
                else:
                    error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                    pytorch_errors.append(f"{cuda_name}: {error_msg}")
                    self.log(f"{cuda_name} failed, trying next option...", "warning")
                    
            except subprocess.TimeoutExpired:
                self.log(f"{cuda_name} installation timed out", "warning")
                pytorch_errors.append(f"{cuda_name}: Timed out")
            except Exception as e:
                self.log(f"{cuda_name} error: {e}", "warning")
                pytorch_errors.append(f"{cuda_name}: {str(e)}")
        
        if not pytorch_installed:
            self.log("PyTorch installation failed!", "error")
            error_details = "\n".join(pytorch_errors[:3])
            self.root.after(100, lambda: self.show_error(
                f"Failed to install PyTorch.\n\n"
                f"Tried versions:\n{error_details}\n\n"
                f"This can happen if:\n"
                f"1. No internet connection or slow connection\n"
                f"2. Firewall blocking PyPI/PyTorch servers\n"
                f"3. Insufficient disk space\n\n"
                f"Try again or install PyTorch manually:\n"
                f"pip install torch torchvision torchaudio"
            ))
            return False
        
        # Install moshi package
        self.log("Installing PersonaPlex (moshi package)...")
        self.update_progress(50, "Installing PersonaPlex...")
        
        moshi_path = os.path.join(script_dir, "moshi")
        
        if not os.path.exists(moshi_path):
            self.log("Moshi package directory not found!", "error")
            self.root.after(100, lambda: self.show_error(
                "The moshi package directory was not found.\n\n"
                "Make sure you extracted all files from the download\n"
                "and the 'moshi' folder exists in the installation directory."
            ))
            return False
        
        try:
            result = subprocess.run(
                [python_exe, "-m", "pip", "install", f"{moshi_path}/.", "--quiet"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                self.log("Retrying moshi installation with verbose output...", "warning")
                result = subprocess.run(
                    [python_exe, "-m", "pip", "install", f"{moshi_path}/."],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                    self.log(f"Moshi installation failed: {error_msg}", "error")
                    self.root.after(100, lambda: self.show_error(
                        f"Failed to install PersonaPlex (moshi) package.\n\n"
                        f"Error: {error_msg[:200]}...\n\n"
                        f"This may be caused by:\n"
                        f"1. Missing Visual C++ Build Tools\n"
                        f"2. Incompatible Python version\n"
                        f"3. Corrupted package files\n\n"
                        f"Try running 'pip install moshi/.' manually for more details."
                    ))
                    return False
                    
        except subprocess.TimeoutExpired:
            self.log("Moshi installation timed out", "error")
            return False
        
        self.log("PersonaPlex (moshi) installed", "success")
        
        # Install accelerate
        self.log("Installing accelerate for CPU offload support...")
        subprocess.run(
            [python_exe, "-m", "pip", "install", "accelerate", "--quiet"], 
            capture_output=True,
            timeout=120
        )
        self.log("Accelerate installed", "success")
        
        # Store the python path for later use
        self.python_exe = python_exe
        
        return True
    
    def build_client(self):
        """Check web interface - Node.js build is NOT required"""
        # The server has an embedded web client, so building is optional
        self.log("Web interface: Server includes embedded client (no build required)", "success")
        self.log("Node.js is NOT required - the server will serve the web UI automatically", "info")
        return True
    
    def setup_models(self):
        """Set up models (download or link existing)"""
        token = self.hf_token.get().strip()
        
        if token:
            os.environ["HF_TOKEN"] = token
        
        if self.model_source.get() == "existing":
            return self.link_existing_models()
        else:
            return self.download_models()
    
    def link_existing_models(self):
        """Link existing model files"""
        model_path = self.custom_model_path.get()
        
        if not model_path or not os.path.exists(model_path):
            self.log("Invalid model path specified", "error")
            return False
        
        self.log(f"Using models from: {model_path}")
        
        # Verify files exist
        missing = []
        for filename in REQUIRED_MODELS.keys():
            filepath = os.path.join(model_path, filename)
            if not os.path.exists(filepath):
                missing.append(filename)
        
        if missing:
            self.log(f"Missing model files: {', '.join(missing)}", "error")
            self.root.after(100, lambda: self.show_error(
                f"The following model files are missing from the specified folder:\n\n"
                f"{chr(10).join(missing)}\n\n"
                f"Please ensure all required files are in the folder."
            ))
            return False
        
        # Save custom path to config
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "model_config.json")
        with open(config_path, "w") as f:
            json.dump({"custom_model_path": model_path}, f)
        
        self.log("Model path configured", "success")
        return True
    
    def download_models(self):
        """Download models from HuggingFace"""
        self.log("Preparing to download models from HuggingFace...")
        self.log("This will download approximately 14GB of model files.")
        self.log("Make sure you have a stable internet connection.")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use the virtual environment Python
        venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
        python_to_use = venv_python if os.path.exists(venv_python) else self.python_exe
        
        # Use the existing verify_and_download_models.py script
        download_script = os.path.join(script_dir, "verify_and_download_models.py")
        
        if os.path.exists(download_script):
            self.log("Running model download script...")
            self.update_progress(75, "Downloading models (this may take a while)...")
            
            env = os.environ.copy()
            if self.hf_token.get():
                env["HF_TOKEN"] = self.hf_token.get()
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    result = subprocess.run(
                        [python_to_use, download_script, "--download-only"],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=7200  # 2 hour timeout for large downloads
                    )
                    
                    # Log output
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            self.log(line)
                    
                    # Check for specific errors
                    if "401" in result.stderr or "Authentication" in result.stderr:
                        self.log("Authentication error! Please check your HuggingFace token.", "error")
                        self.root.after(100, lambda: self.show_error(
                            "HuggingFace authentication failed!\n\n"
                            "Please make sure:\n"
                            "1. Your token is correct (starts with 'hf_')\n"
                            "2. You have accepted the model license at:\n"
                            "   https://huggingface.co/nvidia/personaplex-7b-v1\n\n"
                            "Get your token at: https://huggingface.co/settings/tokens"
                        ))
                        return False
                    
                    if "403" in result.stderr or "license" in result.stderr.lower():
                        self.log("License not accepted!", "error")
                        self.root.after(100, lambda: self.show_error(
                            "Model license not accepted!\n\n"
                            "Please visit the following URL and accept the license:\n"
                            "https://huggingface.co/nvidia/personaplex-7b-v1\n\n"
                            "Then try the installation again."
                        ))
                        webbrowser.open(HUGGINGFACE_LICENSE_URL)
                        return False
                    
                    if "429" in result.stderr or "rate limit" in result.stderr.lower():
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 60 * retry_count  # Exponential backoff
                            self.log(f"Rate limited. Waiting {wait_time}s before retry ({retry_count}/{max_retries})...", "warning")
                            import time
                            time.sleep(wait_time)
                            continue
                        else:
                            self.log("Rate limited too many times", "error")
                            self.root.after(100, lambda: self.show_error(
                                "HuggingFace rate limit exceeded!\n\n"
                                "Too many download requests. Please wait a few minutes\n"
                                "and try again, or try at a different time.\n\n"
                            "You can also download models manually from:\n"
                            "https://huggingface.co/nvidia/personaplex-7b-v1"
                            ))
                            return False
                    
                    if result.returncode != 0:
                        self.log("Model download may have had issues", "warning")
                        # Check stderr for more info
                        if result.stderr:
                            for line in result.stderr.split("\n")[:5]:
                                if line.strip():
                                    self.log(f"  {line}", "warning")
                    else:
                        self.log("Model download/verification complete", "success")
                    
                    break  # Success or non-retryable error
                        
                except subprocess.TimeoutExpired:
                    self.log("Download timed out after 2 hours.", "error")
                    self.log("The download may still be incomplete.", "warning")
                    self.log("You can resume by running the installer again.", "info")
                    break
                except Exception as e:
                    self.log(f"Download script error: {e}", "warning")
                    break
        else:
            self.log("Download script not found, models will download on first run", "warning")
        
        return True
    
    def verify_installation(self):
        """Verify the installation is complete"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use the virtual environment Python
        venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
        python_to_use = venv_python if os.path.exists(venv_python) else self.python_exe
        
        self.log("Verifying installation...")
        self.log(f"Using Python: {python_to_use}")
        
        # Check if moshi can be imported
        try:
            result = subprocess.run(
                [python_to_use, "-c", 
                 "import moshi; import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    self.log(line, "success")
                return True
            else:
                self.log(f"Verification failed: {result.stderr}", "warning")
                return True  # Continue anyway, might work
                
        except Exception as e:
            self.log(f"Verification error: {e}", "warning")
            return True  # Continue anyway
    
    def launch_personaplex(self):
        """Launch PersonaPlex after successful installation"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, "START_PERSONAPLEX.bat")
        venv_path = os.path.join(script_dir, "venv")
        venv_python = os.path.join(venv_path, "Scripts", "python.exe")
        
        # Check if virtual environment exists
        if not os.path.exists(venv_python):
            messagebox.showerror(
                "Virtual Environment Not Found",
                "The virtual environment has not been set up yet.\n\n"
                "Please run the installation first by clicking 'Start Installation' "
                "in the welcome screen.\n\n"
                "The installer will create the virtual environment and install all "
                "required dependencies before you can launch PersonaPlex."
            )
            return
        
        # Check if moshi package is installed
        try:
            result = subprocess.run(
                [venv_python, "-c", "import moshi"],
                capture_output=True,
                timeout=10
            )
            if result.returncode != 0:
                messagebox.showerror(
                    "Installation Incomplete",
                    "The moshi package is not installed in the virtual environment.\n\n"
                    "Please run the installation again to complete the setup."
                )
                return
        except Exception as e:
            self.log(f"Warning: Could not verify moshi installation: {e}", "warning")
        
        if os.path.exists(start_script):
            # Use cmd /k to keep console open if there are errors
            # This helps users see any error messages
            subprocess.Popen(
                ["cmd", "/k", start_script], 
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=script_dir
            )
        else:
            messagebox.showerror(
                "Launcher Not Found",
                f"Could not find START_PERSONAPLEX.bat at:\n{start_script}\n\n"
                "Please ensure all files were extracted correctly."
            )
            return
        
        self.root.quit()


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Try to use a modern theme
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except:
        pass
    
    app = InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
