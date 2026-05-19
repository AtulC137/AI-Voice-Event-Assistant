"""
Conversation orchestrator.
"""

import uuid

from app.services.sarvam.llm_service import SarvamLLMService
from app.services.sarvam.tts_service import SarvamTTSService
from app.services.conversation.memory_manager import MemoryManager
from app.services.conversation.intent_detector import IntentDetector
from app.services.conversation.prompt_builder import PromptBuilder
from app.services.conversation.conversation_messages import goodbye_message
from app.services.conversation.language_utils import pick_tts_language
from app.services.conversation.persistence_service import PersistenceService


class ConversationOrchestrator:
    def __init__(self, persistence_service: PersistenceService):
        self.llm_service = SarvamLLMService()
        self.tts_service = SarvamTTSService()
        self.memory_manager = MemoryManager()
        self.persistence_service = persistence_service

    async def generate_welcome_audio(
        self,
        conversation_id: str,
        language_code: str = "en-IN",
    ) -> dict:
        from app.services.conversation.conversation_messages import (
            welcome_message,
        )

        text = welcome_message(language_code)
        output_file = (
            f"storage/output_audio/welcome_{uuid.uuid4()}.wav"
        )
        await self.tts_service.generate_speech(
            text=text,
            language_code="en-IN",
            output_file=output_file,
        )
        self.persistence_service.store_log(
            conversation_id=conversation_id,
            event_type="welcome",
            log_message=text,
        )
        print(f"Assistant Response [welcome]: {text}", flush=True)
        return {"assistant_response": text, "audio_file": output_file}

    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        language_code: str = "en-IN",
    ):
        detected_intent = IntentDetector.detect_intent(
            user_message=user_message
        )

        self.persistence_service.store_message(
            conversation_id=conversation_id,
            sender="user",
            message_text=user_message,
        )

        if detected_intent == "End Conversation":
            assistant_response = goodbye_message("en-IN")
        else:
            conversation_history = (
                self.memory_manager.get_conversation_history(
                    conversation_id
                )
            )
            messages = PromptBuilder.build_messages(
                conversation_history=conversation_history,
                user_message=user_message,
            )
            llm_response = await self.llm_service.generate_response(
                messages=messages
            )
            assistant_response = (
                llm_response["choices"][0]["message"]["content"]
            )

            if "</think>" in assistant_response:
                assistant_response = (
                    assistant_response.split("</think>")[-1]
                    .strip()
                )

        self.memory_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )
        self.memory_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_response,
        )
        self.persistence_service.store_message(
            conversation_id=conversation_id,
            sender="assistant",
            message_text=assistant_response,
        )

        if detected_intent:
            self.persistence_service.update_intent(
                conversation_id=conversation_id,
                intent=detected_intent,
            )

        output_audio_file = (
            f"storage/output_audio/response_{uuid.uuid4()}.wav"
        )
        tts_language = pick_tts_language(
            user_message=user_message,
            assistant_text=assistant_response,
            stt_language_code=language_code,
        )
        if detected_intent == "End Conversation":
            tts_language = "en-IN"

        print(
            f"Assistant Response [tts={tts_language}]: "
            f"{assistant_response}",
            flush=True,
        )

        await self.tts_service.generate_speech(
            text=assistant_response,
            language_code=tts_language,
            output_file=output_audio_file,
        )
        self.persistence_service.store_log(
            conversation_id=conversation_id,
            event_type="conversation_response",
            log_message=assistant_response,
        )

        return {
            "assistant_response": assistant_response,
            "intent": detected_intent,
            "audio_file": output_audio_file,
            "end_conversation": detected_intent == "End Conversation",
        }
