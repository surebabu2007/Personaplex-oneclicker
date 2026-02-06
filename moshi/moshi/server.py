# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# Copyright (c) Kyutai, all rights reserved.
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import asyncio
from dataclasses import dataclass
import random
import os
from pathlib import Path
import tarfile
import time
import secrets
import sys
from typing import Literal, Optional

import aiohttp
from aiohttp import web
from huggingface_hub import hf_hub_download
import numpy as np
import sentencepiece
import sphn
import torch
import random

from .client_utils import make_log, colorize
from .models import loaders, MimiModel, LMModel, LMGen
from .utils.connection import create_ssl_context, get_lan_ip
from .utils.logging import setup_logger, ColorizedLog


logger = setup_logger(__name__)
DeviceString = Literal["cuda"] | Literal["cpu"] #| Literal["mps"]

def torch_auto_device(requested: Optional[DeviceString] = None) -> torch.device:
    """Return a torch.device based on the requested string or availability."""
    if requested is not None:
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    #elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    #    return torch.device("mps")
    return torch.device("cpu")


def seed_all(seed):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # for multi-GPU setups
    random.seed(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = True  # Enable cuDNN auto-tuning for better performance


def wrap_with_system_tags(text: str) -> str:
    """Add system tags as the model expects if they are missing.
    Example: "<system> You enjoy having a good conversation. Have a deep conversation about technology. Your name is Jane. <system>"
    """
    cleaned = text.strip()
    if cleaned.startswith("<system>") and cleaned.endswith("<system>"):
        return cleaned
    return f"<system> {cleaned} <system>"


@dataclass
class ServerState:
    mimi: MimiModel
    other_mimi: MimiModel
    text_tokenizer: sentencepiece.SentencePieceProcessor
    lm_gen: LMGen
    lock: asyncio.Lock

    def __init__(self, mimi: MimiModel, other_mimi: MimiModel, text_tokenizer: sentencepiece.SentencePieceProcessor,
                 lm: LMModel, device: str | torch.device, voice_prompt_dir: str | None = None,
                 save_voice_prompt_embeddings: bool = False):
        self.mimi = mimi
        self.other_mimi = other_mimi
        self.text_tokenizer = text_tokenizer
        self.device = device
        self.voice_prompt_dir = voice_prompt_dir
        self.frame_size = int(self.mimi.sample_rate / self.mimi.frame_rate)
        self.lm_gen = LMGen(lm,
                            audio_silence_frame_cnt=int(0.5 * self.mimi.frame_rate),
                            sample_rate=self.mimi.sample_rate,
                            device=device,
                            frame_rate=self.mimi.frame_rate,
                            save_voice_prompt_embeddings=save_voice_prompt_embeddings,
        )
        
        self.lock = asyncio.Lock()
        self.mimi.streaming_forever(1)
        self.other_mimi.streaming_forever(1)
        self.lm_gen.streaming_forever(1)
    
    def warmup(self):
        # More warmup iterations for CUDA graphs to stabilize
        for _ in range(8):
            chunk = torch.zeros(1, 1, self.frame_size, dtype=torch.float32, device=self.device)
            codes = self.mimi.encode(chunk)
            for c in range(codes.shape[-1]):
                tokens = self.lm_gen.step(codes[:, :, c: c + 1])
                if tokens is None:
                    continue
                _ = self.mimi.decode(tokens[:, 1:9])

        if self.device.type == 'cuda':
            torch.cuda.synchronize()
            # Clear CUDA cache after warmup to free any fragmented memory
            torch.cuda.empty_cache()


    async def handle_chat(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        clog = ColorizedLog.randomize()
        peer = request.remote  # IP
        peer_port = request.transport.get_extra_info("peername")[1]  # Port
        clog.log("info", f"Incoming connection from {peer}:{peer_port}")

        # self.lm_gen.temp = float(request.query["audio_temperature"])
        # self.lm_gen.temp_text = float(request.query["text_temperature"])
        # self.lm_gen.top_k_text = max(1, int(request.query["text_topk"]))
        # self.lm_gen.top_k = max(1, int(request.query["audio_topk"]))
        
        # Construct full voice prompt path
        requested_voice_prompt_path = None
        voice_prompt_path = None
        if self.voice_prompt_dir is not None:
            voice_prompt_filename = request.query["voice_prompt"]
            requested_voice_prompt_path = None
            if voice_prompt_filename is not None:
                requested_voice_prompt_path = os.path.join(self.voice_prompt_dir, voice_prompt_filename)
            # If the voice prompt file does not exist, find a valid (s0) voiceprompt file in the directory
            if requested_voice_prompt_path is None or not os.path.exists(requested_voice_prompt_path):
                raise FileNotFoundError(
                    f"Requested voice prompt '{voice_prompt_filename}' not found in '{self.voice_prompt_dir}'"
                )
            else:
                voice_prompt_path = requested_voice_prompt_path
                
        if self.lm_gen.voice_prompt != voice_prompt_path:
            if voice_prompt_path.endswith('.pt'):
                # Load pre-saved voice prompt embeddings
                self.lm_gen.load_voice_prompt_embeddings(voice_prompt_path)
            else:
                self.lm_gen.load_voice_prompt(voice_prompt_path)
        self.lm_gen.text_prompt_tokens = self.text_tokenizer.encode(wrap_with_system_tags(request.query["text_prompt"])) if len(request.query["text_prompt"]) > 0 else None
        seed = int(request["seed"]) if "seed" in request.query else None

        async def recv_loop():
            nonlocal close
            try:
                async for message in ws:
                    if message.type == aiohttp.WSMsgType.ERROR:
                        clog.log("error", f"{ws.exception()}")
                        break
                    elif message.type == aiohttp.WSMsgType.CLOSED:
                        break
                    elif message.type == aiohttp.WSMsgType.CLOSE:
                        break
                    elif message.type != aiohttp.WSMsgType.BINARY:
                        clog.log("error", f"unexpected message type {message.type}")
                        continue
                    message = message.data
                    if not isinstance(message, bytes):
                        clog.log("error", f"unsupported message type {type(message)}")
                        continue
                    if len(message) == 0:
                        clog.log("warning", "empty message")
                        continue
                    kind = message[0]
                    if kind == 1:  # audio
                        payload = message[1:]
                        opus_reader.append_bytes(payload)
                    else:
                        clog.log("warning", f"unknown message kind {kind}")
            finally:
                close = True
                clog.log("info", "connection closed")

        async def opus_loop():
            all_pcm_data = None

            while True:
                if close:
                    return
                await asyncio.sleep(0.001)
                pcm = opus_reader.read_pcm()
                if pcm.shape[-1] == 0:
                    continue
                if all_pcm_data is None:
                    all_pcm_data = pcm
                else:
                    all_pcm_data = np.concatenate((all_pcm_data, pcm))
                while all_pcm_data.shape[-1] >= self.frame_size:
                    chunk = all_pcm_data[: self.frame_size]
                    all_pcm_data = all_pcm_data[self.frame_size:]
                    chunk = torch.from_numpy(chunk)
                    chunk = chunk.to(device=self.device)[None, None]
                    codes = self.mimi.encode(chunk)
                    for c in range(codes.shape[-1]):
                        tokens = self.lm_gen.step(codes[:, :, c: c + 1])
                        if tokens is None:
                            continue
                        assert tokens.shape[1] == self.lm_gen.lm_model.dep_q + 1
                        main_pcm = self.mimi.decode(tokens[:, 1:9])
                        main_pcm = main_pcm.cpu()
                        opus_writer.append_pcm(main_pcm[0, 0].numpy())
                        text_token = tokens[0, 0, 0].item()
                        if text_token not in (0, 3):
                            _text = self.text_tokenizer.id_to_piece(text_token)  # type: ignore
                            _text = _text.replace("▁", " ")
                            msg = b"\x02" + bytes(_text, encoding="utf8")
                            await ws.send_bytes(msg)
                    # Yield control to keep event loop responsive
                    await asyncio.sleep(0)

        async def send_loop():
            while True:
                if close:
                    return
                await asyncio.sleep(0.001)  # Fast polling for smooth audio
                msg = opus_writer.read_bytes()
                if len(msg) > 0:
                    await ws.send_bytes(b"\x01" + msg)

        clog.log("info", "accepted connection")
        if len(request.query["text_prompt"]) > 0:
            clog.log("info", f"text prompt: {request.query['text_prompt']}")
        if len(request.query["voice_prompt"]) > 0:
            clog.log("info", f"voice prompt: {voice_prompt_path} (requested: {requested_voice_prompt_path})")
        close = False
        async with self.lock:
            if seed is not None and seed != -1:
                seed_all(seed)

            opus_writer = sphn.OpusStreamWriter(self.mimi.sample_rate)
            opus_reader = sphn.OpusStreamReader(self.mimi.sample_rate)
            self.mimi.reset_streaming()
            self.other_mimi.reset_streaming()
            self.lm_gen.reset_streaming()
            async def is_alive():
                if close or ws.closed:
                    return False
                try:
                    # Check for disconnect without waiting too long
                    msg = await asyncio.wait_for(ws.receive(), timeout=0.01)
                    if msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        return False
                except asyncio.TimeoutError:
                    # No messages → client probably still alive
                    return True
                except aiohttp.ClientConnectionError:
                    return False
                return True
            # Reuse mimi for encoding voice prompt and then reset it before conversation starts
            await self.lm_gen.step_system_prompts_async(self.mimi, is_alive=is_alive)
            self.mimi.reset_streaming()
            clog.log("info", "done with system prompts")
            # Send the handshake.
            if await is_alive():
                await ws.send_bytes(b"\x00")
                clog.log("info", "sent handshake bytes")
                # Clean cancellation manager
                tasks = [
                    asyncio.create_task(recv_loop()),
                    asyncio.create_task(opus_loop()),
                    asyncio.create_task(send_loop()),
                ]

                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                # Force-kill remaining tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                await ws.close()
                clog.log("info", "session closed")
                # await asyncio.gather(opus_loop(), recv_loop(), send_loop())
        clog.log("info", "done with connection")
        return ws


def _get_voice_prompt_dir(voice_prompt_dir: Optional[str], hf_repo: str) -> Optional[str]:
    """
    If voice_prompt_dir is None:
      - try to download voices.tgz from HF
      - extract it once
      - return extracted directory (or None if not available)
    If voice_prompt_dir is provided:
      - just return it
    """
    def _resolve_voice_dir(candidate: Path) -> Optional[Path]:
        if any(candidate.glob("*.pt")):
            return candidate
        nested = candidate / "voices"
        if any(nested.glob("*.pt")):
            logger.info(f"Found nested voices directory: {nested}")
            return nested
        return None

    if voice_prompt_dir is not None:
        resolved_dir = _resolve_voice_dir(Path(voice_prompt_dir))
        return str(resolved_dir) if resolved_dir is not None else voice_prompt_dir

    logger.info("retrieving voice prompts")

    # Get HF_TOKEN from environment or cache
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        try:
            from huggingface_hub.utils import HfFolder
            hf_token = HfFolder.get_token()
        except Exception:
            pass

    # Try to download voices.tgz, but it's optional
    try:
        voices_tgz = hf_hub_download(hf_repo, "voices.tgz", token=hf_token)
        voices_tgz = Path(voices_tgz)
        voices_dir = voices_tgz.parent / "voices"

        if not voices_dir.exists():
            logger.info(f"extracting {voices_tgz} to {voices_tgz.parent}")
            with tarfile.open(voices_tgz, "r:gz") as tar:
                tar.extractall(path=voices_tgz.parent)

        resolved_dir = _resolve_voice_dir(voices_dir)
        if resolved_dir is None:
            logger.info("voices directory exists but no .pt files found; re-extracting")
            with tarfile.open(voices_tgz, "r:gz") as tar:
                tar.extractall(path=voices_tgz.parent)
            resolved_dir = _resolve_voice_dir(voices_dir)

        if resolved_dir is None:
            logger.warning("voices.tgz did not contain a usable voices directory")
            return None

        return str(resolved_dir)
    except Exception as e:
        logger.info(f"Voice prompts not available from repository (this is normal): {e}")
        logger.info("Server will run without custom voice prompts")
        return None


def _get_static_path(static: Optional[str], hf_repo: str) -> Optional[str]:
    if static is None:
        logger.info("retrieving the static content")
        # Get HF_TOKEN from environment or cache
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            try:
                from huggingface_hub.utils import HfFolder
                hf_token = HfFolder.get_token()
            except Exception:
                pass
        
        # Try to download dist.tgz from HuggingFace
        try:
            dist_tgz = hf_hub_download(hf_repo, "dist.tgz", token=hf_token)
            dist_tgz = Path(dist_tgz)
            dist = dist_tgz.parent / "dist"
            if not dist.exists():
                with tarfile.open(dist_tgz, "r:gz") as tar:
                    tar.extractall(path=dist_tgz.parent)
            return str(dist)
        except Exception as e:
            logger.warning(f"Could not download static content from HuggingFace: {e}")
            # Try to find local client/dist folder
            script_dir = Path(__file__).parent.parent.parent
            local_dist = script_dir / "client" / "dist"
            if local_dist.exists():
                logger.info(f"Using local client dist: {local_dist}")
                return str(local_dist)
            logger.warning("No static content available. Web UI will not be served.")
            logger.warning("To build the client, run: cd client && npm install && npm run build")
            return None
    elif static != "none":
        # When set to the "none" string, we don't serve any static content.
        return static
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", type=str)
    parser.add_argument("--port", default=8998, type=int)
    parser.add_argument("--static", type=str)
    parser.add_argument("--gradio-tunnel", action='store_true', help='Activate a gradio tunnel.')
    parser.add_argument("--gradio-tunnel-token",
                        help='Provide a custom (secret) token here to keep getting the same URL.')

    parser.add_argument("--tokenizer", type=str, help="Path to a local tokenizer file.")
    parser.add_argument("--moshi-weight", type=str, help="Path to a local checkpoint file for Moshi.")
    parser.add_argument("--mimi-weight", type=str, help="Path to a local checkpoint file for Mimi.")
    parser.add_argument("--hf-repo", type=str, default=loaders.DEFAULT_REPO,
                        help="HF repo to look into, defaults PersonaPlex. "
                             "Use this to select a different pre-trained model.")
    parser.add_argument("--device", type=str, default="cuda", help="Device on which to run, defaults to 'cuda'.")
    parser.add_argument("--cpu-offload", action="store_true",
                        help="Offload LM model layers to CPU when GPU memory is insufficient. "
                             "Requires 'accelerate' package.")
    parser.add_argument(
        "--voice-prompt-dir",
        type=str,
        help=(
            "Directory containing voice prompt files. "
            "If omitted, voices.tgz is downloaded from HF and extracted."
            "Voice prompt filenames from client requests will be joined with this directory path."
        )
    )
    parser.add_argument(
        "--ssl",
        type=str,
        help=(
            "use https instead of http, this flag should point to a directory "
            "that contains valid key.pem and cert.pem files"
        )
    )

    args = parser.parse_args()
    args.voice_prompt_dir = _get_voice_prompt_dir(
        args.voice_prompt_dir,
        args.hf_repo,
    )
    if args.voice_prompt_dir is not None:
        assert os.path.exists(args.voice_prompt_dir), \
            f"Directory missing: {args.voice_prompt_dir}"
    logger.info(f"voice_prompt_dir = {args.voice_prompt_dir}")

    static_path: None | str = _get_static_path(args.static, args.hf_repo)
    assert static_path is None or os.path.exists(static_path), \
        f"Static path does not exist: {static_path}."
    logger.info(f"static_path = {static_path}")
    args.device = torch_auto_device(args.device)

    seed_all(42424242)

    setup_tunnel = None
    tunnel_token = ''
    if args.gradio_tunnel:
        try:
            from gradio import networking  # type: ignore
        except ImportError:
            logger.error("Cannot find gradio which is required to activate a tunnel. "
                         "Please install with `pip install gradio`.")
            sys.exit(1)
        setup_tunnel = networking.setup_tunnel
        if args.gradio_tunnel_token is None:
            tunnel_token = secrets.token_urlsafe(32)
        else:
            tunnel_token = args.gradio_tunnel_token

    # Get HF_TOKEN from environment
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        logger.info("HF_TOKEN found in environment")
    else:
        logger.warning("HF_TOKEN not found in environment. Downloads may fail if authentication is required.")
        # Try to get token from huggingface_hub cache
        try:
            from huggingface_hub.utils import HfFolder
            cached_token = HfFolder.get_token()
            if cached_token:
                hf_token = cached_token
                logger.info("Using token from HuggingFace cache")
        except Exception:
            pass
    
    logger.info("loading mimi")
    if args.mimi_weight is None:
        args.mimi_weight = hf_hub_download(args.hf_repo, loaders.MIMI_NAME, token=hf_token)
    mimi = loaders.get_mimi(args.mimi_weight, args.device)
    other_mimi = loaders.get_mimi(args.mimi_weight, args.device)
    logger.info("mimi loaded")

    if args.tokenizer is None:
        args.tokenizer = hf_hub_download(args.hf_repo, loaders.TEXT_TOKENIZER_NAME, token=hf_token)
    text_tokenizer = sentencepiece.SentencePieceProcessor(args.tokenizer)  # type: ignore

    logger.info("loading moshi")
    if args.moshi_weight is None:
        args.moshi_weight = hf_hub_download(args.hf_repo, loaders.MOSHI_NAME, token=hf_token)
    lm = loaders.get_moshi_lm(args.moshi_weight, device=args.device, cpu_offload=args.cpu_offload)
    lm.eval()
    logger.info("moshi loaded")
    state = ServerState(
        mimi=mimi,
        other_mimi=other_mimi,
        text_tokenizer=text_tokenizer,
        lm=lm,
        device=args.device,
        voice_prompt_dir=args.voice_prompt_dir,
        save_voice_prompt_embeddings=False,
    )
    logger.info("warming up the model")
    state.warmup()
    app = web.Application()
    app.router.add_get("/api/chat", state.handle_chat)
    if static_path is not None:
        async def handle_root(_):
            return web.FileResponse(os.path.join(static_path, "index.html"))

        logger.info(f"serving static content from {static_path}")
        app.router.add_get("/", handle_root)
        app.router.add_static(
            "/", path=static_path, follow_symlinks=True, name="static"
        )
    else:
        # Serve embedded web client when no built static content is available
        async def handle_embedded_client(_):
            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PersonaPlex - SurAiverse Edition</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..700&family=Source+Serif+4:opsz,wght@8..60,300..700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Source Serif 4', serif;
            background:
                radial-gradient(1200px 600px at 10% -10%, rgba(198, 161, 91, 0.22), transparent 60%),
                radial-gradient(900px 500px at 90% 10%, rgba(47, 93, 80, 0.18), transparent 55%),
                linear-gradient(180deg, #f7f2ea 0%, #efe7d8 45%, #e8dcc8 100%);
            color: #1c1a17; min-height: 100vh; display: flex; flex-direction: column;
        }
        .header { padding: 24px 20px; text-align: center; border-bottom: 1px solid rgba(154, 122, 58, 0.35); background: rgba(244, 239, 230, 0.85); }
        .header h1 { color: #1c1a17; font-size: 2.4em; margin-bottom: 6px; font-family: 'Fraunces', serif; letter-spacing: 0.03em; }
        .header .brand-tagline { color: #3a3329; font-size: 0.95em; }
        .header .brand-subtag { color: #9a7a3a; font-size: 0.75em; text-transform: uppercase; letter-spacing: 0.2em; margin-top: 6px; }
        .main { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 26px 20px; }
        .chat-container { width: 100%; max-width: 700px; }

        .status-strip { background: rgba(255, 255, 255, 0.7); border: 1px solid rgba(154, 122, 58, 0.35); 
                        border-radius: 14px; padding: 12px 16px; margin: 20px 0 24px; box-shadow: 0 6px 18px rgba(26, 20, 12, 0.12); }
        .status-row { display: flex; justify-content: space-between; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.18em; color: #3a3329; margin-bottom: 8px; }
        .progress-track { height: 8px; border-radius: 999px; background: rgba(47, 93, 80, 0.15); overflow: hidden; }
        .progress-bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #c6a15b 0%, #e1c48a 55%, #9a7a3a 100%); transition: width 0.3s ease; }
        .progress-steps { display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.7em; color: rgba(58, 51, 41, 0.6); }
        .progress-steps span.active { color: #2f5d50; font-weight: 600; }
        
        /* Homepage / Setup View */
        .setup-view { display: block; }
        .conversation-view { display: none; }
        .setup-view.hidden { display: none; }
        .conversation-view.active { display: block; }
        
        /* Form styling for light theme */
        .form-section { background: rgba(250, 246, 239, 0.92); border-radius: 16px; padding: 24px; margin-bottom: 20px; 
                        border: 1px solid rgba(156, 131, 84, 0.3); box-shadow: 0 6px 18px rgba(26, 20, 12, 0.12); }
        .form-section-title { font-size: 0.95em; font-weight: 600; color: #3a3329; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.16em; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; font-size: 0.9em; font-weight: 500; color: #555; margin-bottom: 8px; }
        .form-group textarea, .form-group select { 
            width: 100%; padding: 12px; border-radius: 12px; border: 1px solid rgba(156, 131, 84, 0.4);
            background: rgba(255, 255, 255, 0.9); color: #1c1a17; font-size: 0.95em; transition: border-color 0.2s; }
        .form-group textarea:focus, .form-group select:focus { 
            outline: none; border-color: #9a7a3a; box-shadow: 0 0 0 3px rgba(198,161,91,0.2); }
        .form-group textarea { min-height: 100px; resize: vertical; }
        .char-count { text-align: right; font-size: 0.8em; color: #888; margin-top: 4px; }
        
        /* Preset buttons */
        .presets-container { background: rgba(255, 255, 255, 0.6); border-radius: 12px; padding: 12px; margin-bottom: 12px; border: 1px solid rgba(156, 131, 84, 0.2); }
        .presets-label { font-size: 0.75em; font-weight: 500; color: #8a7a5a; margin-bottom: 8px; display: block; text-transform: uppercase; letter-spacing: 0.18em; }
        .presets { display: flex; flex-wrap: wrap; gap: 8px; }
        .preset-btn { padding: 6px 14px; font-size: 0.82em; background: rgba(255,255,255,0.9); color: #5f5136; 
                      border: 1px solid rgba(156, 131, 84, 0.4); border-radius: 20px; cursor: pointer; transition: all 0.2s; }
        .preset-btn:hover { background: #2f5d50; color: #f7f1e6; border-color: #2f5d50; }
        
        /* Status badge */
        .status-badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; 
                        border-radius: 20px; background: rgba(255,255,255,0.8); box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; }
        .status-dot.connected { background: #76b900; box-shadow: 0 0 10px rgba(118,185,0,0.5); }
        .status-dot.connecting { background: #f0ad4e; animation: pulse 1s infinite; }
        .status-dot.disconnected { background: #dc3545; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        /* Buttons */
        .btn { padding: 14px 32px; border-radius: 30px; border: none; font-size: 0.95em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;
               cursor: pointer; transition: all 0.3s; display: inline-flex; align-items: center; gap: 8px; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-primary { background: #2f5d50; color: #f7f1e6; }
        .btn-primary:hover:not(:disabled) { background: #24463b; transform: translateY(-2px); 
                                            box-shadow: 0 5px 20px rgba(47,93,80,0.35); }
        .btn-danger { background: #9a3b3b; color: #fff; }
        .btn-danger:hover:not(:disabled) { background: #7f2f2f; transform: translateY(-2px); }
        .btn-container { text-align: center; margin-top: 24px; }
        
        /* Conversation view */
        .visualizer-container { display: flex; gap: 30px; justify-content: center; margin: 30px 0; }
        .visualizer { width: 140px; height: 140px; border-radius: 50%; display: flex; align-items: center; 
                      justify-content: center; position: relative; background: rgba(255,255,255,0.85); 
                      box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .visualizer.ai { border: 3px solid #00a8cc; }
        .visualizer.user { border: 3px solid #76b900; }
        .visualizer-label { position: absolute; bottom: -30px; font-size: 0.9em; color: #666; font-weight: 500; }
        .visualizer-ring { position: absolute; width: 100%; height: 100%; border-radius: 50%; 
                          border: 3px solid transparent; }
        .visualizer.active .visualizer-ring { animation: ring-pulse 0.5s infinite; }
        .visualizer.ai.active .visualizer-ring { border-color: #00a8cc; }
        .visualizer.user.active .visualizer-ring { border-color: #76b900; }
        @keyframes ring-pulse { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(1.3); opacity: 0; } }
        
        .transcript { background: rgba(255,255,255,0.9); border-radius: 12px; padding: 20px; min-height: 100px; 
                      max-height: 200px; overflow-y: auto; margin-bottom: 24px; 
                      box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .transcript-label { font-size: 0.85em; color: #888; margin-bottom: 10px; font-weight: 500; }
        .transcript-text { font-size: 1.05em; line-height: 1.7; color: #333; }
        
        .controls { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; }

        .download-row { display: none; align-items: center; justify-content: space-between; gap: 12px;
                        background: rgba(255,255,255,0.85); border: 1px solid rgba(156, 131, 84, 0.35);
                        border-radius: 14px; padding: 14px 16px; margin-top: 18px; }
        .download-title { font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.18em; color: #6e5d3b; }
        .download-sub { font-size: 0.8em; color: #7b6a4a; }
        
        .footer { padding: 20px; text-align: center; border-top: 1px solid rgba(154, 122, 58, 0.35); background: rgba(244, 239, 230, 0.85); }
        .footer a { color: #2f5d50; text-decoration: none; }
        .footer a:hover { text-decoration: underline; }
        
        .error-msg { background: #fff5f5; border: 1px solid #dc3545; color: #dc3545; padding: 15px; 
                     border-radius: 8px; margin-bottom: 20px; display: none; }
        .mic-icon { width: 24px; height: 24px; }
        
        /* Responsive */
        @media (max-width: 600px) {
            .chat-container { padding: 0 10px; }
            .form-section { padding: 16px; }
            .visualizer { width: 100px; height: 100px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>PersonaPlex</h1>
        <div class="brand-tagline">Simplified &amp; one-click install by SurAiverse</div>
        <div class="brand-subtag">Based on NVIDIA PersonaPlex 7B</div>
    </div>
    
    <div class="main">
        <div class="chat-container">
            <div class="status-strip">
                <div class="status-row">
                    <span>Session</span>
                    <span id="progressLabel">Ready</span>
                </div>
                <div class="progress-track">
                    <div class="progress-bar" id="progressBar" style="width: 20%;"></div>
                </div>
                <div class="progress-steps">
                    <span id="stepReady" class="active">Ready</span>
                    <span id="stepConnecting">Connecting</span>
                    <span id="stepLive">Live</span>
                    <span id="stepComplete">Complete</span>
                </div>
            </div>
            <!-- Setup View (Homepage) -->
            <div class="setup-view" id="setupView">
                <div class="form-section">
                    <div class="form-section-title">Text Prompt</div>
                    <div class="presets-container">
                        <span class="presets-label">Examples:</span>
                        <div class="presets">
                            <button class="preset-btn" onclick="setPreset('assistant')">Assistant (default)</button>
                            <button class="preset-btn" onclick="setPreset('medical')">Medical office (service)</button>
                            <button class="preset-btn" onclick="setPreset('bank')">Bank (service)</button>
                            <button class="preset-btn" onclick="setPreset('astronaut')">Astronaut (fun)</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <textarea id="textPrompt" maxlength="1000" placeholder="Enter your text prompt...">You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.</textarea>
                        <div class="char-count"><span id="charCount">0</span>/1000</div>
                    </div>
                </div>
                
                <div class="form-section">
                    <div class="form-section-title">Voice</div>
                    <div class="form-group">
                        <select id="voicePrompt">
                            <option value="NATF0.pt">NATURAL_F0</option>
                            <option value="NATF1.pt">NATURAL_F1</option>
                            <option value="NATF2.pt">NATURAL_F2</option>
                            <option value="NATF3.pt">NATURAL_F3</option>
                            <option value="NATM0.pt">NATURAL_M0</option>
                            <option value="NATM1.pt">NATURAL_M1</option>
                            <option value="NATM2.pt">NATURAL_M2</option>
                            <option value="NATM3.pt">NATURAL_M3</option>
                            <option value="VARF0.pt">VARIETY_F0</option>
                            <option value="VARF1.pt">VARIETY_F1</option>
                            <option value="VARF2.pt">VARIETY_F2</option>
                            <option value="VARF3.pt">VARIETY_F3</option>
                            <option value="VARF4.pt">VARIETY_F4</option>
                            <option value="VARM0.pt">VARIETY_M0</option>
                            <option value="VARM1.pt">VARIETY_M1</option>
                            <option value="VARM2.pt">VARIETY_M2</option>
                            <option value="VARM3.pt">VARIETY_M3</option>
                            <option value="VARM4.pt">VARIETY_M4</option>
                        </select>
                    </div>
                </div>
                
                <div class="error-msg" id="errorMsg"></div>
                
                <div class="btn-container">
                    <button class="btn btn-primary" id="connectBtn" onclick="startConversation()">
                        <svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>
                        </svg>
                        Connect
                    </button>
                </div>
            </div>
            
            <!-- Conversation View -->
            <div class="conversation-view" id="conversationView">
                <div style="text-align: center;">
                    <div class="status-badge">
                        <span class="status-dot disconnected" id="statusDot"></span>
                        <span id="statusText">Disconnected</span>
                    </div>
                </div>
            
            <div class="error-msg" id="convErrorMsg"></div>
            
            <div class="visualizer-container">
                <div class="visualizer ai" id="aiVisualizer">
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#00a8cc" stroke-width="2">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>
                    </svg>
                    <div class="visualizer-ring"></div>
                    <span class="visualizer-label">AI</span>
                </div>
                <div class="visualizer user" id="userVisualizer">
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#76b900" stroke-width="2">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>
                    </svg>
                    <div class="visualizer-ring"></div>
                    <span class="visualizer-label">You</span>
                </div>
            </div>
            
            <div class="transcript">
                <div class="transcript-label">AI Response</div>
                <div class="transcript-text" id="transcript">Speak into your microphone...</div>
            </div>
            
            <div class="controls">
                <button class="btn btn-danger" id="stopBtn" onclick="stopConversation()">
                    Disconnect
                </button>
                <button class="btn btn-primary" id="newConvBtn" onclick="newConversation()" style="display:none;">
                    New Conversation
                </button>
            </div>
            <div class="download-row" id="downloadRow">
                <div>
                    <div class="download-title">Session Complete</div>
                    <div class="download-sub">Download your conversation audio</div>
                </div>
                <a class="btn btn-primary" id="downloadLink" download="personaplex_conversation.webm">Download Audio</a>
            </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>Created by <a href="https://www.youtube.com/@suraiverse" target="_blank">Suresh Pydikondala (SurAiverse)</a> | 
           <a href="https://huggingface.co/nvidia/personaplex-7b-v1" target="_blank">NVIDIA PersonaPlex</a></p>
    </div>

    <!-- Opus Recorder from CDN -->
    <script src="https://cdn.jsdelivr.net/npm/opus-recorder@8.0.5/dist/recorder.min.js"></script>
    <script>
        // Text prompt presets
        const PRESETS = {
            assistant: "You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.",
            medical: "You work for Dr. Jones's medical office, and you are receiving calls to record information for new patients. Information: Record full name, date of birth, any medication allergies, tobacco smoking history, alcohol consumption history, and any prior medical conditions. Assure the patient that this information will be confidential, if they ask.",
            bank: "You work for First Neuron Bank which is a bank and your name is Alexis Kim. Information: The customer's transaction for $1,200 at Home Depot was declined. Verify customer identity. The transaction was flagged due to unusual location (transaction attempted in Miami, FL; customer normally transacts in Seattle, WA).",
            astronaut: "You enjoy having a good conversation. Have a technical discussion about fixing a reactor core on a spaceship to Mars. You are an astronaut on a Mars mission. Your name is Alex. You are already dealing with a reactor core meltdown on a Mars mission. Several ship systems are failing, and continued instability will lead to catastrophic failure. You explain what is happening and you urgently ask for help thinking through how to stabilize the reactor."
        };
        
        let socket = null;
        let recorder = null;
        let audioContext = null;
        let decoderWorker = null;
        let nextPlayTime = 0;
        let recordingDestination = null;
        let mediaRecorder = null;
        let recordedChunks = [];
        let micStream = null;
        let micSource = null;
        let shouldShowDownload = false;
        const SAMPLE_RATE = 24000;
        
        // View elements
        const setupView = document.getElementById('setupView');
        const conversationView = document.getElementById('conversationView');
        const textPromptInput = document.getElementById('textPrompt');
        const voicePromptSelect = document.getElementById('voicePrompt');
        const charCount = document.getElementById('charCount');
        const connectBtn = document.getElementById('connectBtn');
        const errorMsg = document.getElementById('errorMsg');
        const downloadRow = document.getElementById('downloadRow');
        const downloadLink = document.getElementById('downloadLink');
        const progressBar = document.getElementById('progressBar');
        const progressLabel = document.getElementById('progressLabel');
        const stepReady = document.getElementById('stepReady');
        const stepConnecting = document.getElementById('stepConnecting');
        const stepLive = document.getElementById('stepLive');
        const stepComplete = document.getElementById('stepComplete');
        
        // Conversation view elements
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const stopBtn = document.getElementById('stopBtn');
        const newConvBtn = document.getElementById('newConvBtn');
        const transcript = document.getElementById('transcript');
        const convErrorMsg = document.getElementById('convErrorMsg');
        const aiVisualizer = document.getElementById('aiVisualizer');
        const userVisualizer = document.getElementById('userVisualizer');
        
        // Initialize character count
        function updateCharCount() {
            charCount.textContent = textPromptInput.value.length;
        }
        textPromptInput.addEventListener('input', updateCharCount);
        updateCharCount();
        
        // Set preset text
        function setPreset(presetName) {
            if (PRESETS[presetName]) {
                textPromptInput.value = PRESETS[presetName];
                updateCharCount();
            }
        }
        
        function showSetupView() {
            setupView.classList.remove('hidden');
            conversationView.classList.remove('active');
        }
        
        function showConversationView() {
            setupView.classList.add('hidden');
            conversationView.classList.add('active');
        }

        function setProgress(value, label, complete = false) {
            progressBar.style.width = value + '%';
            progressLabel.textContent = label;
            stepReady.classList.add('active');
            stepConnecting.classList.toggle('active', value >= 60);
            stepLive.classList.toggle('active', value >= 100 && !complete);
            stepComplete.classList.toggle('active', complete);
        }
        
        function setStatus(status, text) {
            statusDot.className = 'status-dot ' + status;
            statusText.textContent = text;
            if (status === 'connecting') {
                setProgress(60, 'Connecting');
            } else if (status === 'connected') {
                setProgress(100, 'Live');
            } else {
                setProgress(20, 'Ready');
            }
        }
        
        function showError(msg, inConversation = false) {
            const el = inConversation ? convErrorMsg : errorMsg;
            el.textContent = msg;
            el.style.display = 'block';
            setTimeout(() => { el.style.display = 'none'; }, 8000);
        }
        
        async function initAudio() {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: SAMPLE_RATE });
            }
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }
            nextPlayTime = audioContext.currentTime;
        }

        async function startSessionRecording() {
            try {
                shouldShowDownload = false;
                recordedChunks = [];
                downloadRow.style.display = 'none';
                if (!audioContext) {
                    return;
                }
                if (!recordingDestination) {
                    recordingDestination = audioContext.createMediaStreamDestination();
                }
                try {
                    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    micSource = audioContext.createMediaStreamSource(micStream);
                    micSource.connect(recordingDestination);
                } catch (err) {
                    console.warn('Could not attach mic stream to recording:', err);
                }

                mediaRecorder = new MediaRecorder(recordingDestination.stream);
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data && event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };
                mediaRecorder.onstop = () => {
                    if (!shouldShowDownload || recordedChunks.length === 0) {
                        return;
                    }
                    const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                    const url = URL.createObjectURL(blob);
                    downloadLink.href = url;
                    downloadRow.style.display = 'flex';
                };
                mediaRecorder.start();
            } catch (err) {
                console.warn('Session recording unavailable:', err);
            }
        }

        function stopSessionRecording(showDownload = null) {
            if (showDownload !== null) {
                shouldShowDownload = showDownload;
            }
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                try { mediaRecorder.stop(); } catch (err) {}
            }
            if (micSource) {
                try { micSource.disconnect(); } catch (err) {}
                micSource = null;
            }
            if (micStream) {
                micStream.getTracks().forEach(track => track.stop());
                micStream = null;
            }
        }
        
        function createWarmupBosPage() {
            const opusHead = new Uint8Array([
                0x4F, 0x70, 0x75, 0x73, 0x48, 0x65, 0x61, 0x64,
                0x01, 0x01, 0x38, 0x01, 0x80, 0xBB, 0x00, 0x00,
                0x00, 0x00, 0x00
            ]);
            const pageHeader = new Uint8Array([
                0x4F, 0x67, 0x67, 0x53, 0x00, 0x02,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x01, 0x13
            ]);
            const bosPage = new Uint8Array(pageHeader.length + opusHead.length);
            bosPage.set(pageHeader, 0);
            bosPage.set(opusHead, pageHeader.length);
            return bosPage;
        }
        
        async function initDecoder() {
            return new Promise((resolve, reject) => {
                try {
                    decoderWorker = new Worker('/assets/decoderWorker.min.js');
                } catch (e) {
                    console.warn('Could not load local decoder, trying CDN...');
                    decoderWorker = new Worker('https://cdn.jsdelivr.net/npm/opus-recorder@8.0.5/dist/decoderWorker.min.js');
                }
                
                decoderWorker.onmessage = (e) => {
                    if (e.data && e.data[0]) {
                        playDecodedAudio(e.data[0]);
                    }
                };
                
                decoderWorker.onerror = (err) => {
                    console.error('Decoder worker error:', err);
                };
                
                const bufferLength = Math.round(960 * audioContext.sampleRate / SAMPLE_RATE);
                decoderWorker.postMessage({
                    command: 'init',
                    bufferLength: bufferLength,
                    decoderSampleRate: SAMPLE_RATE,
                    outputBufferSampleRate: audioContext.sampleRate,
                    resampleQuality: 0
                });
                
                setTimeout(() => {
                    const bosPage = createWarmupBosPage();
                    decoderWorker.postMessage({ command: 'decode', pages: bosPage });
                    console.log('Decoder initialized');
                    resolve();
                }, 200);
            });
        }
        
        function playDecodedAudio(pcmData) {
            if (!audioContext || !pcmData || pcmData.length === 0) return;
            
            const buffer = audioContext.createBuffer(1, pcmData.length, audioContext.sampleRate);
            buffer.getChannelData(0).set(pcmData);
            
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            if (recordingDestination) {
                source.connect(recordingDestination);
            }
            
            const now = audioContext.currentTime;
            if (nextPlayTime < now) {
                nextPlayTime = now + 0.05;
            }
            
            source.start(nextPlayTime);
            nextPlayTime += buffer.duration;
            
            aiVisualizer.classList.add('active');
            setTimeout(() => aiVisualizer.classList.remove('active'), 100);
        }
        
        function decodeAudio(opusData) {
            if (decoderWorker && opusData.length > 0) {
                decoderWorker.postMessage({ command: 'decode', pages: opusData }, [opusData.buffer]);
            }
        }
        
        async function startConversation() {
            try {
                connectBtn.disabled = true;
                connectBtn.textContent = 'Connecting...';
                downloadRow.style.display = 'none';
                downloadLink.removeAttribute('href');
                
                await initAudio();
                await initDecoder();
                
                // Check microphone permission
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop());
                
                // Switch to conversation view
                showConversationView();
                setStatus('connecting', 'Connecting...');
                transcript.textContent = 'Connecting to server...';
                
                // Build WebSocket URL
                const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
                const wsUrl = new URL(wsProtocol + '://' + window.location.host + '/api/chat');
                wsUrl.searchParams.set('text_prompt', textPromptInput.value || '');
                wsUrl.searchParams.set('voice_prompt', voicePromptSelect.value || '');
                wsUrl.searchParams.set('text_temperature', '0.7');
                wsUrl.searchParams.set('text_topk', '100');
                wsUrl.searchParams.set('audio_temperature', '0.7');
                wsUrl.searchParams.set('audio_topk', '250');
                wsUrl.searchParams.set('pad_mult', '0');
                wsUrl.searchParams.set('repetition_penalty_context', '64');
                wsUrl.searchParams.set('repetition_penalty', '1.1');
                
                socket = new WebSocket(wsUrl.toString());
                socket.binaryType = 'arraybuffer';
                
                socket.onopen = () => {
                    console.log('WebSocket connected, waiting for handshake...');
                    setStatus('connecting', 'Loading AI model (this may take a moment)...');
                };
                
                socket.onmessage = (event) => {
                    const data = new Uint8Array(event.data);
                    const msgType = data[0];
                    const payload = data.slice(1);
                    
                    if (msgType === 0x00) {
                        console.log('Handshake received, starting recording...');
                        setStatus('connected', 'Connected - Speak now!');
                        stopBtn.disabled = false;
                        transcript.textContent = '';
                        startMicRecording();
                        startSessionRecording();
                    } else if (msgType === 0x01) {
                        decodeAudio(payload);
                    } else if (msgType === 0x02) {
                        const text = new TextDecoder().decode(payload);
                        transcript.textContent += text;
                        transcript.scrollTop = transcript.scrollHeight;
                    }
                };
                
                socket.onerror = (err) => {
                    console.error('WebSocket error:', err);
                    showError('Connection error. Make sure you accepted the security certificate.', true);
                    cleanup();
                };
                
                socket.onclose = (event) => {
                    console.log('WebSocket closed:', event.code, event.reason);
                    if (event.code !== 1000) {
                        showError('Connection closed unexpectedly. The server may still be loading the model.', true);
                    }
                    setStatus('disconnected', 'Disconnected');
                    cleanup();
                };
                
            } catch (err) {
                console.error('Error:', err);
                if (err.name === 'NotAllowedError') {
                    showError('Microphone access denied. Please allow microphone access and try again.');
                } else {
                    showError(err.message || 'Failed to start conversation');
                }
                connectBtn.disabled = false;
                connectBtn.innerHTML = '<svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Connect';
                showSetupView();
            }
        }
        
        async function startMicRecording() {
            try {
                const encoderPath = 'https://cdn.jsdelivr.net/npm/opus-recorder@8.0.5/dist/encoderWorker.min.js';
                
                recorder = new Recorder({
                    encoderPath: encoderPath,
                    encoderSampleRate: SAMPLE_RATE,
                    encoderFrameSize: 20,
                    maxFramesPerPage: 2,
                    numberOfChannels: 1,
                    streamPages: true,
                    encoderApplication: 2049,
                });
                
                recorder.ondataavailable = (data) => {
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        userVisualizer.classList.add('active');
                        setTimeout(() => userVisualizer.classList.remove('active'), 100);
                        const msg = new Uint8Array(1 + data.length);
                        msg[0] = 0x01;
                        msg.set(data, 1);
                        socket.send(msg);
                    }
                };
                
                recorder.onstart = () => {
                    console.log('Microphone recording started');
                };
                
                await recorder.start();
            } catch (err) {
                console.error('Microphone error:', err);
                showError('Microphone error: ' + (err.message || 'Could not start recording'), true);
            }
        }
        
        function stopConversation() {
            stopSessionRecording(true);
            cleanup();
            setStatus('disconnected', 'Disconnected');
            setProgress(100, 'Complete', true);
            transcript.textContent += '\\n\\n[Conversation ended]';
            stopBtn.style.display = 'none';
            newConvBtn.style.display = 'inline-flex';
        }
        
        function newConversation() {
            showSetupView();
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Connect';
            stopBtn.style.display = 'inline-flex';
            newConvBtn.style.display = 'none';
            setProgress(20, 'Ready');
            downloadRow.style.display = 'none';
            downloadLink.removeAttribute('href');
        }
        
        function cleanup() {
            stopSessionRecording(null);
            if (recorder) {
                try { recorder.stop(); } catch(e) {}
                recorder = null;
            }
            if (socket) {
                try { socket.close(); } catch(e) {}
                socket = null;
            }
            if (decoderWorker) {
                try { decoderWorker.terminate(); } catch(e) {}
                decoderWorker = null;
            }
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Connect';
            aiVisualizer.classList.remove('active');
            userVisualizer.classList.remove('active');
            nextPlayTime = 0;
        }
        
        // Handle page unload
        window.addEventListener('beforeunload', cleanup);
    </script>
</body>
</html>"""
            return web.Response(text=html, content_type='text/html')
        
        logger.info("Serving embedded web client (no build required)")
        app.router.add_get("/", handle_embedded_client)
        
        # Serve decoder files from client/public/assets if they exist
        script_dir = Path(__file__).parent.parent.parent
        decoder_path = script_dir / "client" / "public" / "assets"
        if decoder_path.exists():
            async def serve_decoder_js(_):
                file_path = decoder_path / "decoderWorker.min.js"
                if file_path.exists():
                    return web.FileResponse(file_path)
                return web.Response(status=404)
            
            async def serve_decoder_wasm(_):
                file_path = decoder_path / "decoderWorker.min.wasm"
                if file_path.exists():
                    return web.FileResponse(file_path, headers={'Content-Type': 'application/wasm'})
                return web.Response(status=404)
            
            app.router.add_get("/assets/decoderWorker.min.js", serve_decoder_js)
            app.router.add_get("/assets/decoderWorker.min.wasm", serve_decoder_wasm)
            logger.info(f"Serving decoder files from {decoder_path}")
    protocol = "http"
    ssl_context = None
    if args.ssl is not None:
        ssl_context, protocol = create_ssl_context(args.ssl)
    host_ip = args.host if args.host not in ("0.0.0.0", "::", "localhost") else get_lan_ip()
    logger.info(f"Access the Web UI directly at {protocol}://{host_ip}:{args.port}")
    if setup_tunnel is not None:
        tunnel = setup_tunnel('localhost', args.port, tunnel_token, None)
        logger.info(f"Tunnel started, if executing on a remote GPU, you can use {tunnel}.")
    web.run_app(app, port=args.port, ssl_context=ssl_context)


with torch.no_grad():
    main()
