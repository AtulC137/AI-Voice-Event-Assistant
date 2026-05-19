"""
Conversation orchestrator.

Location: backend/app/services/conversation/orchestrator.py

Pipeline:
    User message
    → EventResponder.get_best_match()
        → if FAREWELL  : send farewell TTS, set end_conversation=True
                         (conversation.py will send __END_AFTER_AUDIO__
                          and close the WebSocket)
        → if other rule: send response TTS, continue conversation
    → IntentDetector   (Interested / Maybe / Not Interested tagging)
    → Persist to DB

LLM removed entirely. EventResponder scoring engine handles all replies.
TTS (Sarvam REST) is the only external call in the hot path.

Farewell flow:
    "bye" / "धन्यवाद" / "shukriya" etc.
    → EventResponder scores FAREWELL as winner (3x bonus)
    → orchestrator yields end_conversation=True
    → conversation.py sends __END_AFTER_AUDIO__ to frontend
    → frontend closes WebSocket after audio finishes playing
"""

import uuid
from typing import AsyncGenerator

from app.services.sarvam.tts_service import SarvamTTSService

from app.services.conversation.event_responder import EventResponder
from app.services.conversation.memory_manager import MemoryManager
from app.services.conversation.intent_detector import IntentDetector
from app.services.conversation.persistence_service import PersistenceService


class ConversationOrchestrator:
    """
    Orchestrates the full conversation pipeline.

    Responsibilities:
    - Persist user message to DB
    - Use EventResponder scoring to pick best response
    - Detect farewell and signal WebSocket to close
    - Detect intent (Interested / Maybe / Not Interested)
    - Convert response to speech via TTS
    - Stream audio chunks back to WebSocket
    - Persist assistant response, intent, and log
    - Maintain in-memory conversation history
    """

    def __init__(self, persistence_service: PersistenceService):
        """
        Initialise orchestrator with required services.

        Args:
            persistence_service: Handles DB writes for messages,
                                 intents, and logs.
        """
        self.tts_service         = SarvamTTSService()
        self.memory_manager      = MemoryManager()
        self.persistence_service = persistence_service

    async def stream_response_audio(
        self,
        conversation_id: str,
        user_message: str,
        language_code: str = "en-IN"
    ) -> AsyncGenerator[dict, None]:
        """
        Main streaming pipeline.

        Steps:
            1. Persist user message to DB
            2. Score user message → get best matching rule
            3. If FAREWELL → TTS farewell → yield end_conversation=True
               (caller must close WebSocket after audio plays)
            4. Otherwise → TTS response → yield audio chunks
            5. Detect and persist intent
            6. Persist assistant response and log

        Yields:
            dict:
                audio             (bytes | None)
                end_conversation  (bool)  ← True signals WebSocket close
                done              (bool)
                assistant_response (str | None)
                intent            (str | None)
        """

        # ── 1. Persist user message ──────────────────────────────
        self.persistence_service.store_message(
            conversation_id=conversation_id,
            sender="user",
            message_text=user_message
        )

        # ── 2. Score → best match ────────────────────────────────
        match = EventResponder.get_best_match(user_message)

        response_text = match["response"]
        is_farewell   = match["is_farewell"]
        label         = match["label"]

        print(
            f"[EventResponder] label={label} "
            f"farewell={is_farewell} "
            f"reply={response_text}",
            flush=True
        )

        # ── 3. Farewell path ─────────────────────────────────────
        if is_farewell:

            async for audio_chunk in (
                self.tts_service.generate_speech_bytes_stream(
                    text=response_text,
                    language_code=language_code
                )
            ):
                yield {
                    "audio":              audio_chunk,
                    "end_conversation":   True,   # ← tells conversation.py to close
                    "done":               False,
                    "assistant_response": None,
                    "intent":             "End Conversation"
                }

            self._store_turn(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_response=response_text,
                intent="End Conversation"
            )

            yield {
                "audio":              None,
                "end_conversation":   True,
                "done":               True,
                "assistant_response": response_text,
                "intent":             "End Conversation"
            }
            return

        # ── 4. Normal response path ──────────────────────────────

        # Intent detection (Interested / Maybe / Not Interested)
        detected_intent = IntentDetector.detect_intent(
            user_message=user_message
        )

        async for audio_chunk in (
            self.tts_service.generate_speech_bytes_stream(
                text=response_text,
                language_code=language_code
            )
        ):
            yield {
                "audio":              audio_chunk,
                "end_conversation":   False,
                "done":               False,
                "assistant_response": None,
                "intent":             detected_intent
            }

        # ── 5 & 6. Persist ───────────────────────────────────────
        self._store_turn(
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=response_text,
            intent=detected_intent
        )

        yield {
            "audio":              None,
            "end_conversation":   False,
            "done":               True,
            "assistant_response": response_text,
            "intent":             detected_intent
        }

    # ── Internal helpers ─────────────────────────────────────────

    def _store_turn(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        intent: str
    ):
        """
        Add both sides of the turn to memory and persist to DB.

        Args:
            conversation_id:    Active conversation UUID.
            user_message:       What the user said.
            assistant_response: What the assistant replied.
            intent:             Detected intent label or None.
        """
        self.memory_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )
        self.memory_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_response
        )
        self.persistence_service.store_message(
            conversation_id=conversation_id,
            sender="assistant",
            message_text=assistant_response
        )
        if intent:
            self.persistence_service.update_intent(
                conversation_id=conversation_id,
                intent=intent
            )
        self.persistence_service.store_log(
            conversation_id=conversation_id,
            event_type="conversation_response",
            log_message=assistant_response
        )

    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        language_code: str = "en-IN"
    ):
        """
        Non-streaming fallback. Kept for compatibility.

        Collects all audio chunks, writes to file, returns summary.

        Args:
            conversation_id: Active conversation UUID.
            user_message:    User's transcribed text.
            language_code:   BCP-47 language tag.

        Returns:
            dict: assistant_response, intent, audio_file, end_conversation.
        """
        audio_parts = []
        result      = {}

        async for chunk in self.stream_response_audio(
            conversation_id=conversation_id,
            user_message=user_message,
            language_code=language_code
        ):
            if chunk["audio"]:
                audio_parts.append(chunk["audio"])
            if chunk["done"]:
                result = chunk

        output_audio_file = (
            f"storage/output_audio/response_{uuid.uuid4()}.wav"
        )
        with open(output_audio_file, "wb") as f:
            f.write(b"".join(audio_parts))

        return {
            "assistant_response": result.get("assistant_response", ""),
            "intent":             result.get("intent"),
            "audio_file":         output_audio_file,
            "end_conversation":   result.get("end_conversation", False)
        }