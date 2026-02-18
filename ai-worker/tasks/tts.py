
from celery import shared_task
import os
import logging
import base64
import tempfile
import soundfile as sf
import numpy as np
import re

# Configure logging
logger = logging.getLogger("TTS-Task")

class SupertonicWrapper:
    def __init__(self):
        self.tts = None
        try:
            # Import supertonic directly with native class
            from supertonic import TTS
            
            # Using auto_download=True to handle model management internally.
            # This is robust because it checks the cache first, not needing redundant downloads.
            self.tts = TTS(auto_download=True)
            logger.info("Supertonic TTS engine initialized via Library.")
            
        except ImportError:
            logger.error("supertonic package not installed. Please install it via pip install supertonic.")
            self.tts = None
        except Exception as e:
            logger.error(f"Failed to initialize Supertonic TTS: {e}")
            self.tts = None

    def synthesize(self, text, output_file, speed=1.0):
        if not self.tts:
            logger.error("TTS Engine not loaded")
            return False
            
        try:
            # Assuming 'synthesize' or similar method exists on the TTS instance.
            # The exact method might vary, but 'synthesize' is standard.
            # If the library returns audio data (numpy array), handle it.
            
            # Note: Some libraries use generate() or speak().
            # Based on common usage patterns and similar libs:
            audio_data = self.tts.synthesize(text, speed=speed)
            
            if isinstance(audio_data, (np.ndarray, list)):
                # Default sample rate for Supertonic is typically 24000
                # But let's check if the tts object exposes fs or sample_rate
                fs = getattr(self.tts, 'sample_rate', 24000) 
                sf.write(output_file, audio_data, fs)
            elif isinstance(audio_data, str) and os.path.exists(audio_data):
                import shutil
                shutil.move(audio_data, output_file)
            else:
                # If audio_data is something else, log it.
                logger.warning(f"Unexpected return type from synthesis: {type(audio_data)}")
                return False

            return True

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return False

# Global instance
tts_engine = None

def load_tts_engine():
    global tts_engine
    if tts_engine is None:
        tts_engine = SupertonicWrapper()

# Initialize on module load
load_tts_engine()

@shared_task(name="tasks.tts.synthesize")
def synthesize_task(text: str, language="ko", speed=1.0):
    """
    Synthesize text to speech returning base64 encoded audio.
    """
    global tts_engine
    
    if tts_engine is None or tts_engine.tts is None:
        load_tts_engine()
        if tts_engine is None or tts_engine.tts is None:
             return {"status": "error", "message": "TTS Engine initialization failed"}

    temp_path = None
    try:
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
            
        # [추가] [...] 형태의 태그 제거 (음성으로 읽지 않음)
        clean_text = re.sub(r'\[.*?\]', '', text).strip()
        
        success = tts_engine.synthesize(clean_text, temp_path, speed=speed)
        
        if not success:
             return {"status": "error", "message": "Synthesis failed"}

        # Read back and encode
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
        return {"status": "success", "audio_base64": audio_b64}

    except Exception as e:
        logger.error(f"TTS Task Error: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
