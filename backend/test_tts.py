"""
Standalone test script for SARVAM Text-to-Speech API.
Used to verify speech generation independently.
"""

import asyncio

from app.services.sarvam.tts_service import SarvamTTSService


async def main():
    """
    Run TTS generation test.
    """

    tts_service = SarvamTTSService()

    output_file = await tts_service.generate_speech(
        text="Hello, welcome to the Adobe Exclusive Roundtable event in Pune."
    )

    print("\nTTS GENERATED:\n")
    print(f"Audio saved as: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())