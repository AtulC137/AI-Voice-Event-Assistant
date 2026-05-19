"""
SARVAM Speech-to-Text service.

Location: backend/app/services/sarvam/stt_service.py

Methods:
- transcribe_stream  → accepts PCM chunks list, wraps to WAV
                       in-memory, POSTs to Sarvam STT REST API.
                       Used by conversation.py hot path (no disk I/O).
- transcribe_audio   → file-based fallback (kept for compatibility).
- close_stream       → closes WebSocket preview connection if open.
"""

import io
import wave
import json
import websockets

from app.core.config import settings
from app.services.sarvam.client import SarvamAPIClient


class SarvamSTTService:
    """
    Speech-to-text service using the Sarvam AI API.

    Hot path uses transcribe_stream (in-memory, no file I/O).
    File-based transcribe_audio is kept for compatibility only.
    """

    def __init__(self):
        """Initialise Sarvam API client."""
        self.client    = SarvamAPIClient()
        self.websocket = None

    async def transcribe_stream(
        self,
        audio_chunks: list
    ) -> dict:
        """
        Transcribe audio from a list of raw PCM Int16 chunks.

        Combines chunks into one buffer, wraps in WAV container
        in-memory, and POSTs to the Sarvam STT REST API.
        No files are written to disk.

        Args:
            audio_chunks: List of raw PCM bytes from the frontend.

        Returns:
            dict: { "transcript": str, "language_code": str }
        """
        try:
            # Combine all PCM chunks
            raw_pcm = b"".join(audio_chunks)

            # Wrap in WAV container in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)      # mono
                wav_file.setsampwidth(2)       # Int16 = 2 bytes
                wav_file.setframerate(16000)   # 16 kHz
                wav_file.writeframes(raw_pcm)
            wav_buffer.seek(0)
            wav_bytes = wav_buffer.read()

            # POST to Sarvam STT REST API
            files = {
                "file": ("audio.wav", wav_bytes, "audio/wav")
            }
            data = {
                "model": "saaras:v3"
            }

            response = await self.client.post(
                endpoint="/speech-to-text",
                data=data,
                files=files
            )

            result = response.json()
            print(f"STT result: {result}", flush=True)

            return {
                "transcript":    result.get("transcript", ""),
                "language_code": result.get("language_code", "en-IN")
            }

        except Exception as error:
            print(f"STT error: {error}", flush=True)
            return {
                "transcript":    "",
                "language_code": "en-IN"
            }

    async def connect_stream(self):
        """
        Connect to Sarvam streaming WebSocket (preview only).
        Not used in the main transcription flow.
        """
        if self.websocket:
            return

        websocket_url = (
            "wss://api.sarvam.ai/speech-to-text/ws"
            "?language-code=unknown&model=saaras:v3"
        )

        self.websocket = await websockets.connect(
            websocket_url,
            additional_headers={
                "Api-Subscription-Key": settings.SARVAM_API_KEY
            }
        )
        print("Streaming STT connected.", flush=True)

    async def stream_transcript_preview(
        self,
        audio_chunk: bytes
    ):
        """
        Send a chunk to the streaming STT WebSocket for preview.
        Not used in the main flow — preview only.

        Args:
            audio_chunk: Raw PCM bytes.
        """
        try:
            await self.connect_stream()
            await self.websocket.send(audio_chunk)
            response = await self.websocket.recv()
            print("Partial STT:", response, flush=True)
        except Exception as error:
            print(f"Preview Error: {error}", flush=True)

    async def close_stream(self):
        """Close the streaming WebSocket connection if open."""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
            self.websocket = None

    async def transcribe_audio(
        self,
        file_path: str
    ) -> dict:
        """
        File-based transcription. Kept for compatibility.

        Args:
            file_path: Path to a WAV file on disk.

        Returns:
            dict: Raw Sarvam STT API response.
        """
        with open(file_path, "rb") as audio_file:
            files = {"file": audio_file}
            data  = {"model": "saaras:v3"}
            response = await self.client.post(
                endpoint="/speech-to-text",
                data=data,
                files=files
            )
            return response.json()