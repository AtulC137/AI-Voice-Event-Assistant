"""
Standalone test script for complete conversation orchestration pipeline.

Tests:
- memory handling
- prompt building
- LLM response generation
- intent detection
- TTS generation
"""

import asyncio
import uuid

from app.services.conversation.orchestrator import (
    ConversationOrchestrator
)


async def main():
    """
    Run complete conversation orchestration test.
    """

    orchestrator = ConversationOrchestrator()

    conversation_id = str(uuid.uuid4())

    user_message = (
        "Mujhe event ke timing aur venue ke baare mein batao."
    )

    response = await orchestrator.process_user_message(
        conversation_id=conversation_id,
        user_message=user_message,
        language_code="hi-IN"
    )

    print("\nORCHESTRATOR RESPONSE:\n")

    print(f"Assistant Response: {response['assistant_response']}")

    print(f"\nDetected Intent: {response['intent']}")

    print(f"\nGenerated Audio File: {response['audio_file']}")


if __name__ == "__main__":
    asyncio.run(main())