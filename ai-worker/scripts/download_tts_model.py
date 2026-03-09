
import os
import logging
import soundfile as sf
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model():
    """설명:
        Forces the download of the Supertonic model by initializing the TTS engine

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    print("Initializing Supertonic TTS to trigger auto-download...")
    try:
        from supertonic import TTS
        # Initialize to trigger download
        # We don't need to keep the instance, just ensure assets are present.
        tts = TTS(auto_download=True)
        print("Supertonic model download/verification complete.")
    except ImportError:
        print("Error: 'supertonic' library not found. Please run 'pip install supertonic'.")
    except Exception as e:
        print(f"Error during model download: {e}")

if __name__ == "__main__":
    download_model()
