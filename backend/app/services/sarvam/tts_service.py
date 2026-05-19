"""
SARVAM Text-to-Speech service.

Location: backend/app/services/sarvam/tts_service.py

Handles speech generation using the SARVAM TTS REST API.

Methods:
- generate_speech_bytes        → returns raw audio bytes (no file I/O)
- generate_speech_bytes_stream → async generator yielding audio bytes
                                  (used by orchestrator hot path)
- generate_speech              → file-based (kept for compatibility)
"""

import base64
from typing import AsyncGenerator

from app.services.sarvam.client import SarvamAPIClient


class SarvamTTSService:
    """
    Service for converting text into speech audio
    using the SARVAM AI TTS API.

    In the hot path, generate_speech_bytes_stream is used
    so the orchestrator can yield audio to the WebSocket
    as soon as it is available — no disk I/O involved.
    """

    def __init__(self):
        """
        Initialise the SARVAM API client.
        """
        self.client = SarvamAPIClient()

    async def generate_speech_bytes(
        self,
        text: str,
        language_code: str = "en-IN"
    ) -> bytes:
        """
        Call SARVAM TTS REST API and return raw audio bytes.

        No file is written to disk.

        Args:
            text:          Text to convert to speech.
            language_code: BCP-47 language tag (default en-IN).

        Returns:
            Raw WAV audio as bytes.
        """

        payload = {
            "inputs": [text],
            "target_language_code": "en-IN",
            "speaker": "anushka",
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.0,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v2"
        }

        response = await self.client.post(
            endpoint="/text-to-speech",
            json=payload
        )

        response_json = response.json()
        audio_base64  = response_json["audios"][0]

        return base64.b64decode(audio_base64)

    async def generate_speech_bytes_stream(
        self,
        text: str,
        language_code: str = "en-IN"
    ) -> AsyncGenerator[bytes, None]:
        """
        Async generator that yields audio bytes for a given text.

        Named 'stream' for interface compatibility with the orchestrator.
        Currently yields a single chunk (one REST call per sentence).

        Args:
            text:          Text to convert to speech.
            language_code: BCP-47 language tag (default en-IN).

        Yields:
            Raw WAV audio bytes.
        """

        audio_bytes = await self.generate_speech_bytes(
            text=text,
            language_code=language_code
        )

        yield audio_bytes

    async def generate_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        output_file: str = "output.wav"
    ) -> str:
        """
        Generate speech and save to a file.

        Kept for compatibility with non-streaming callers.

        Args:
            text:          Text to convert to speech.
            language_code: BCP-47 language tag (default en-IN).
            output_file:   Path to write the WAV file.

        Returns:
            Path to the saved audio file.
        """

        audio_bytes = await self.generate_speech_bytes(
            text=text,
            language_code=language_code
        )

        with open(output_file, "wb") as audio_file:
            audio_file.write(audio_bytes)

        return output_file