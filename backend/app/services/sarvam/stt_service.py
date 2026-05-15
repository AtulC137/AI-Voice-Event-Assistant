"""
SARVAM Speech-to-Text service.
Handles audio transcription using SARVAM STT API.
"""

from app.services.sarvam.client import SarvamAPIClient


class SarvamSTTService:
    """
    Service for converting speech audio into text
    using SARVAM AI Speech-to-Text API.
    """

    def __init__(self):
        """
        Initialize SARVAM API client.
        """

        self.client = SarvamAPIClient()

    async def transcribe_audio(
        self,
        file_path: str
    ):
        """
        Transcribe audio file into text.
        """

        with open(file_path, "rb") as audio_file:

            files = {
                "file": audio_file
            }

            data = {
                "model": "saaras:v3"
            }

            response = await self.client.post(
                endpoint="/speech-to-text",
                data=data,
                files=files
            )

            return response.json()