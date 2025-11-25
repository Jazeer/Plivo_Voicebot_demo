# backend/tts_stream.py
"""
TTS helper for Plivo Stream (bidirectional):

- Uses macOS `say` with Samantha voice to synthesize speech to an AIFF file.
- Uses ffmpeg to convert that AIFF into raw 16-bit linear PCM (L16) at 8000 Hz mono.
- Returns raw PCM bytes which app.py will cut into chunks and send over WebSocket.

On the WebSocket, we MUST send (when bidirectional=true):

{
  "event": "playAudio",
  "media": {
    "contentType": "audio/x-l16",
    "sampleRate": 8000,
    "payload": "<base64 of raw L16 PCM>"
  }
}
"""

import os
import tempfile
import subprocess
import base64
from typing import Optional

from backend.utils import logger


def _synthesize_to_aiff_mac_say(text: str, out_path: str, voice: str = "Samantha") -> None:
    """
    Use macOS `say` to synthesize TTS into an AIFF file.
    We let `say` choose a reasonable format and rely on ffmpeg to resample later.
    """
    cmd = [
        "say",
        "-v",
        voice,
        text,
        "-o",
        out_path,
    ]
    logger.info(f"[TTS] macOS say → voice={voice}, text='{text[:60]}...'")
    subprocess.run(cmd, check=True)


def synthesize_to_pcm16_8k(text: str, voice: Optional[str] = None) -> bytes:
    """
    Main helper: given text, return 16-bit linear PCM (L16) 8000 Hz mono bytes.

    Steps:
      1) Use macOS `say` to create an AIFF file.
      2) Use ffmpeg to convert to raw s16le 8k mono (L16).
      3) Read raw bytes and return.
    """
    if voice is None:
        voice = "Samantha"

    with tempfile.TemporaryDirectory() as tmp:
        aiff_path = os.path.join(tmp, "tts.aiff")
        raw_path = os.path.join(tmp, "tts.raw")

        # 1) Synthesize speech to AIFF
        _synthesize_to_aiff_mac_say(text, aiff_path, voice)

        # 2) Convert AIFF → raw L16 @ 8kHz mono
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            aiff_path,
            "-ar",
            "8000",        # sample rate
            "-ac",
            "1",           # mono
            "-f",
            "s16le",       # raw 16-bit PCM, little endian
            "-c:a",
            "pcm_s16le",
            raw_path,
        ]

        logger.info("[TTS] ffmpeg converting to 8kHz L16…")
        subprocess.run(
            ffmpeg_cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 3) Read raw bytes
        with open(raw_path, "rb") as f:
            pcm = f.read()

        logger.info(f"[TTS] generated {len(pcm)} bytes (L16@8k)")
        return pcm


def pcm16_to_playAudio_payload(pcm_chunk: bytes, sample_rate: int = 8000) -> dict:
    """
    Turn a raw PCM16 chunk into the JSON Plivo expects when bidirectional=true.

    Plivo docs:
      event: "playAudio"
      media: {
        contentType: "audio/x-l16" or "audio/x-mulaw"
        sampleRate: 8000 or 16000
        payload: "<base64 raw audio>"
      }
    """
    b64 = base64.b64encode(pcm_chunk).decode("ascii")
    return {
        "event": "playAudio",
        "media": {
            "contentType": "audio/x-l16",  # NOTE: no ;rate here
            "sampleRate": sample_rate,
            "payload": b64,
        },
    }
