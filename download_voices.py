
import urllib.request
import urllib.error
import os
from pathlib import Path

# URL for NVIDIA repo which likely has the file but requires auth
# Also keep Kyutai just in case
URLS = [
    "https://huggingface.co/nvidia/personaplex-7b-v1/resolve/main/voices.tgz",
    "https://huggingface.co/kyutai/moshiko-pytorch-bf16/resolve/main/voices.tgz"
]

TARGET = "voices.tgz"

def get_token():
    token = os.getenv("HF_TOKEN")
    if token:
        print("Found HF_TOKEN in environment")
        return token
    
    # Try common cache locations
    home = Path.home()
    token_path = home / ".cache" / "huggingface" / "token"
    if token_path.exists():
        try:
            token = token_path.read_text().strip()
            if token:
                print(f"Found token in {token_path}")
                return token
        except Exception as e:
            print(f"Error reading token file: {e}")
            
    return None

def download():
    token = get_token()
    headers = {'User-Agent': 'Mozilla/5.0'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    else:
        print("WARNING: No HF token found. Downloads may fail if repo is private/gated.")

    for url in URLS:
        print(f"Trying to download from: {url}")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response, open(TARGET, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            
            print(f"Successfully downloaded {TARGET} ({os.path.getsize(TARGET)} bytes)")
            return True
        except urllib.error.HTTPError as e:
            print(f"Failed with {e.code}: {e.reason}")
        except Exception as e:
            print(f"Error: {e}")
            
    return False

if __name__ == "__main__":
    if download():
        print("Download complete.")
        exit(0)
    else:
        print("All downloads failed.")
        exit(1)
