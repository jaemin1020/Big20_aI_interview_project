
import os
import sys
from huggingface_hub import hf_hub_download

# Configuration
REPO_ID = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
FILENAME = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

def download_model():
    print(f"Downloading {FILENAME} from {REPO_ID}...")

    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"Created directory: {MODELS_DIR}")

    try:
        file_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False
        )
        print(f"✅ Model downloaded successfully to: {file_path}")
    except Exception as e:
        print(f"❌ Failed to download model: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
