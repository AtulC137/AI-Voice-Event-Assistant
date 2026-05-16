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
from app.services.conversation.persistence_service import (
    PersistenceService
)

class ConversationOrchestrator:
    """
    Central orchestration engine for AI conversations.
    """

    def __init__(
        self,
        persistence_service: PersistenceService
    ):
        """
        Initialize conversation services.
        """

        self.llm_service = SarvamLLMService()

        self.tts_service = SarvamTTSService()

        self.memory_manager = MemoryManager()

        self.persistence_service = (
        persistence_service
        )

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
        self.persistence_service.store_message(
            conversation_id=conversation_id,
            sender="user",
            message_text=user_message
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
            self.persistence_service.store_message(
                conversation_id=conversation_id,
                sender="assistant",
                message_text=assistant_response
            )

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
        
        if detected_intent == "End Conversation":
            assistant_response = (
                "Thank you for your time. "
                "It was nice talking with you. "
                "Have a great day."
            )

        if detected_intent:
            self.persistence_service.update_intent(
                conversation_id=conversation_id,
                intent=detected_intent
            )

        output_audio_file = (
            f"storage/output_audio/"
            f"response_{uuid.uuid4()}.wav"
        )
        await self.tts_service.generate_speech(
            text=assistant_response,
            language_code=language_code,
            output_file=output_audio_file
        )
        self.persistence_service.store_log(
            conversation_id=conversation_id,
            event_type="conversation_response",
            log_message=assistant_response
        )
        return {
            "assistant_response": assistant_response,
            "intent": detected_intent,
            "audio_file": output_audio_file,
            "end_conversation":
                detected_intent ==
                "End Conversation"
        }