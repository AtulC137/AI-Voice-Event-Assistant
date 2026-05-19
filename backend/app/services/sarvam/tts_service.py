"""
SARVAM Text-to-Speech service.
"""

import base64
import uuid

from app.services.conversation.conversation_messages import (
    normalize_language_code,
)
from app.services.sarvam.client import SarvamAPIClient


class SarvamTTSService:
    def __init__(self):
        self.client = SarvamAPIClient()

    async def generate_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        output_file: str | None = None,
    ) -> str:
        target_language = normalize_language_code(language_code)

        payload = {
            "inputs": [text],
            "target_language_code": target_language,
            "speaker": "anushka",
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.0,
            "speech_sample_rate": 22050,
            "enable_preprocessing": False,
            "model": "bulbul:v2",
        }

        response = await self.client.post(
            endpoint="/text-to-speech",
            json=payload,
        )

        audio_base64 = response.json()["audios"][0]
        audio_bytes = base64.b64decode(audio_base64)

        if not output_file:
            output_file = (
                f"storage/output_audio/response_{uuid.uuid4()}.wav"
            )

        with open(output_file, "wb") as audio_file:
            audio_file.write(audio_bytes)

        return output_file

    async def generate_speech_bytes(
        self,
        text: str,
        language_code: str = "en-IN",
    ) -> bytes:
        path = await self.generate_speech(
            text=text,
            language_code=language_code,
        )
        with open(path, "rb") as audio_file:
            return audio_file.read()
