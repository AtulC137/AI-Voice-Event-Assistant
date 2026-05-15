"""
Conversation orchestrator.

Responsible for:
- managing complete conversation flow
- memory handling
- prompt generation
- LLM response generation
- intent detection
- TTS generation
"""

import uuid

from app.services.sarvam.llm_service import SarvamLLMService
from app.services.sarvam.tts_service import SarvamTTSService

from app.services.conversation.memory_manager import MemoryManager
from app.services.conversation.intent_detector import IntentDetector
from app.services.conversation.prompt_builder import PromptBuilder


class ConversationOrchestrator:
    """
    Central orchestration engine for AI conversations.
    """

    def __init__(self):
        """
        Initialize conversation services.
        """

        self.llm_service = SarvamLLMService()

        self.tts_service = SarvamTTSService()

        self.memory_manager = MemoryManager()

    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        language_code: str = "en-IN"
    ):
        """
        Process complete conversational pipeline.
        """

        conversation_history = (
            self.memory_manager.get_conversation_history(
                conversation_id
            )
        )

        messages = PromptBuilder.build_messages(
            conversation_history=conversation_history,
            user_message=user_message
        )

        llm_response = await self.llm_service.generate_response(
            messages=messages
        )

        assistant_response = (
            llm_response["choices"][0]["message"]["content"]
        )

        self.memory_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )

        if "</think>" in assistant_response:

            assistant_response = (
                assistant_response
                .split("</think>")[-1]
                .strip()
            )

        self.memory_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_response
        )

        detected_intent = IntentDetector.detect_intent(
            user_message=user_message
        )

        output_audio_file = (
            f"response_{uuid.uuid4()}.wav"
        )

        await self.tts_service.generate_speech(
            text=assistant_response,
            language_code=language_code,
            output_file=output_audio_file
        )

        return {
            "assistant_response": assistant_response,
            "intent": detected_intent,
            "audio_file": output_audio_file
        }