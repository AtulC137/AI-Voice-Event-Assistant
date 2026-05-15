"""
Standalone test script for SARVAM Speech-to-Text API.
Used to verify audio transcription independently.
"""

import asyncio

from app.services.sarvam.stt_service import SarvamSTTService

async def main():
    """
    Run STT transcription test.
    """

    stt_service = SarvamSTTService()

    response = await stt_service.transcribe_audio(
        file_path="tests/audio_samples/sample_audio.wav"
    )

    print("\nSTT RESPONSE:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())