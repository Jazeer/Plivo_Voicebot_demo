# backend/stt.py

"""
Streaming Vosk Speech-to-Text
Stable + identical to your earlier working version
"""

import os
from vosk import Model, KaldiRecognizer, SetLogLevel
from backend.utils import logger

SetLogLevel(0)


class StreamingVosk:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.recognizers = {}

        if not model_path or not os.path.exists(model_path):
            logger.error(f"[VOSK] Model path invalid: {model_path}")
        else:
            logger.info(f"[VOSK] Loading model at {model_path}")
            self.model = Model(model_path)

    # -------------------------------------------------------------
    # Create a recognizer per session
    # -------------------------------------------------------------
    def new_recognizer(self, session_id: str, sample_rate: int = 8000):
        if not self.model:
            logger.error("Vosk model not initialized")
            return

        rec = KaldiRecognizer(self.model, sample_rate)
        rec.SetWords(True)
        self.recognizers[session_id] = rec

        logger.info(f"[VOSK] New recognizer: sr={sample_rate}")

    # -------------------------------------------------------------
    # Process an audio chunk
    # -------------------------------------------------------------
    def accept_audio_chunk(self, session_id: str, audio: bytes) -> dict:
        rec = self.recognizers.get(session_id)
        if not rec:
            return {}

        try:
            if rec.AcceptWaveform(audio):
                result = rec.Result()
            else:
                result = rec.PartialResult()

            return eval(result)  # Vosk returns JSON strings

        except Exception as e:
            logger.error(f"[VOSK] Error: {e}")
            return {}

    # -------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------
    def end_session(self, session_id: str):
        self.recognizers.pop(session_id, None)
