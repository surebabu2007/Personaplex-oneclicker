
import os
import sys
from pathlib import Path
import tarfile
from huggingface_hub import hf_hub_download
import glob

# Mock logger
class Logger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

logger = Logger()

def _get_voice_prompt_dir(voice_prompt_dir, hf_repo):
    """
    Copy of the function from moshi/server.py for debugging
    """
    if voice_prompt_dir is not None:
        logger.info(f"Using provided voice_prompt_dir: {voice_prompt_dir}")
        return voice_prompt_dir

    logger.info("retrieving voice prompts")

    # Get HF_TOKEN from environment or cache
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        try:
            from huggingface_hub.utils import HfFolder
            hf_token = HfFolder.get_token()
            if hf_token:
                logger.info("Found token in cache")
        except Exception:
            logger.warning("No HF token found")
            pass
    else:
        logger.info("Found HF_TOKEN env var")
    
    def _resolve_voice_dir(candidate: Path):
        if any(candidate.glob("*.pt")):
            return candidate
        nested = candidate / "voices"
        if any(nested.glob("*.pt")):
            logger.info(f"Found nested voices directory: {nested}")
            return nested
        return None

    # Try to download voices.tgz, but it's optional
    try:
        logger.info(f"Downloading/checking voices.tgz from {hf_repo}")
        voices_tgz = hf_hub_download(hf_repo, "voices.tgz", token=hf_token)
        logger.info(f"voices.tgz path: {voices_tgz}")
        voices_tgz = Path(voices_tgz)
        voices_dir = voices_tgz.parent / "voices"
        logger.info(f"Extracted voices dir should be: {voices_dir}")

        if not voices_dir.exists():
            logger.info(f"extracting {voices_tgz} to {voices_tgz.parent}")
            with tarfile.open(voices_tgz, "r:gz") as tar:
                tar.extractall(path=voices_tgz.parent)
        else:
            logger.info("voices dir already exists")

        resolved_dir = _resolve_voice_dir(voices_dir)
        if resolved_dir is None:
            logger.info("voices directory exists but no .pt files found; re-extracting")
            with tarfile.open(voices_tgz, "r:gz") as tar:
                tar.extractall(path=voices_tgz.parent)
            resolved_dir = _resolve_voice_dir(voices_dir)

        if resolved_dir is None:
            logger.warning("voices.tgz did not contain a usable voices directory")
            return None

        files = list(resolved_dir.glob("*.pt"))
        logger.info(f"Found {len(files)} .pt files in {resolved_dir}")
        if files:
            logger.info(f"Sample files: {[f.name for f in files[:5]]}")

        return str(resolved_dir)
    except Exception as e:
        logger.info(f"Voice prompts not available from repository (this is normal): {e}")
        logger.info("Server will run without custom voice prompts")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Running voice prompt diagnostic...")
    repo = "PersonaPlex" 
    # Note: server.py uses loaders.DEFAULT_REPO which might be "nvidia/personaplex-7b-v1" or similar
    # In server.py:
    # parser.add_argument("--hf-repo", type=str, default=loaders.DEFAULT_REPO, ...)
    # checking imports in server.py: from .models import loaders
    # I don't have access to loaders.py source easily but I can guess or check.
    # The user scripts use "nvidia/personaplex-7b-v1" or similar?
    # START_PERSONAPLEX.bat calls moshi.server
    
    # Let's try to import loaders to get the real default
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "moshi"))
        from moshi.models import loaders
        repo = loaders.DEFAULT_REPO
        print(f"Default repo from loaders: {repo}")
    except Exception as e:
        print(f"Could not import loaders: {e}")
        repo = "nvidia/personaplex-7b-v1" # Fallback guess
        print(f"Using fallback repo: {repo}")

    
    
    result = _get_voice_prompt_dir(None, repo)
    print(f"\nResult: {result}")
