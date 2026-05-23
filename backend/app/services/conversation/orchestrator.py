"""
Conversation orchestrator.
"""

from app.services.sarvam.llm_service import (
    SarvamLLMService
)

from app.services.sarvam.tts_service import (
    SarvamTTSService
)

from app.services.conversation.memory_manager import (
    MemoryManager
)

from app.services.conversation.intent_detector import (
    IntentDetector
)

from app.services.conversation.prompt_builder import (
    PromptBuilder
)

from app.services.conversation.conversation_messages import (
    goodbye_message,
    welcome_message
)

from app.services.conversation.language_utils import (
    pick_tts_language
)

from app.services.conversation.persistence_service import (
    PersistenceService
)


class ConversationOrchestrator:

    def __init__(
        self,
        persistence_service:
        PersistenceService
    ):
        self.llm_service = (
            SarvamLLMService()
        )

        self.tts_service = (
            SarvamTTSService()
        )

        self.memory_manager = (
            MemoryManager()
        )

        self.persistence_service = (
            persistence_service
        )

    async def generate_welcome_audio(
        self,
        conversation_id: str,
        language_code: str = "en-IN",
    ):

        text = welcome_message(
            language_code
        )

        audio_bytes = (
            await self.tts_service.generate_speech_bytes(
                text=text,
                language_code="en-IN",
            )
        )

        return {
            "assistant_response": text,
            "audio_bytes": audio_bytes
        }

    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        language_code: str = "en-IN",
    ):

        detected_intent = (
            IntentDetector.detect_intent(
                user_message
            )
        )

        self.persistence_service.store_message(
            conversation_id,
            "user",
            user_message
        )

        if (
            detected_intent ==
            "End Conversation"
        ):

            assistant_response = (
                goodbye_message(
                    "en-IN"
                )
            )

        else:

            history = (
                self.memory_manager
                .get_conversation_history(
                    conversation_id
                )
            )

            messages = (
                PromptBuilder
                .build_messages(
                    history,
                    user_message
                )
            )

            llm_response = (
                await self.llm_service
                .generate_response(
                    messages
                )
            )

            assistant_response = (
                llm_response
                ["choices"][0]
                ["message"]
                ["content"]
            )

            if "</think>" in assistant_response:

                assistant_response = (
                    assistant_response
                    .split("</think>")[-1]
                    .strip()
                )

        self.memory_manager.add_message(
            conversation_id,
            "user",
            user_message
        )

        self.memory_manager.add_message(
            conversation_id,
            "assistant",
            assistant_response
        )

        tts_language = (
            pick_tts_language(
                user_message=user_message,
                assistant_text=assistant_response,
                stt_language_code=language_code,
            )
        )

        audio_bytes = (
            await self.tts_service.generate_speech_bytes(
                text=assistant_response,
                language_code=tts_language
            )
        )

        return {
            "assistant_response":
            assistant_response,

            "intent":
            detected_intent,

            "audio_bytes":
            audio_bytes,

            "end_conversation":
            (
                detected_intent
                ==
                "End Conversation"
            )
        }