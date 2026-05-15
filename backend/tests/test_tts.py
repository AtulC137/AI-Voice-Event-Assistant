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
    text="नमस्ते, Adobe Exclusive Roundtable event में आपका स्वागत है।",
    language_code="hi-IN",
    output_file="tests/generated_audio/output.wav"
    )

    print("\nTTS GENERATED:\n")
    print(f"Audio saved as: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())