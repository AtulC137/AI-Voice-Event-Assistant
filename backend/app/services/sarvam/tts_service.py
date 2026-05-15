"""
SARVAM Text-to-Speech service.
Handles speech generation using SARVAM TTS API.
"""

from app.services.sarvam.client import SarvamAPIClient


class SarvamTTSService:
    """
    Service for converting text into speech audio
    using SARVAM AI TTS API.
    """

    def __init__(self):
        """
        Initialize SARVAM API client.
        """

        self.client = SarvamAPIClient()

    async def generate_speech(
    self,
    text: str,
    language_code: str = "language_code",
    output_file: str = "output.wav"
):
        """
        Generate speech audio from input text.
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

        audio_base64 = response_json["audios"][0]

        import base64

        audio_bytes = base64.b64decode(audio_base64)

        with open(output_file, "wb") as audio_file:
            audio_file.write(audio_bytes)

        return output_file