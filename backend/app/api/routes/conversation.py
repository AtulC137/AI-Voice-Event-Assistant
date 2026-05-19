"""
WebSocket conversation routes.

Location: backend/app/api/routes/conversation.py

Flow:
    1. Frontend connects via WebSocket
    2. Raw PCM Int16 chunks received from AudioContext until __END_AUDIO__
    3. PCM chunks passed to SarvamSTTService.transcribe_stream()
       which wraps them in WAV in-memory and POSTs to Sarvam STT REST API
    4. Transcript → ConversationOrchestrator (EventResponder, no LLM)
    5. Response text → Sarvam TTS → audio bytes streamed back
    6. If farewell detected → send __END_AFTER_AUDIO__ → close WebSocket

No files are written to disk in the hot path.

Frontend sends:
    - Binary frames: raw PCM Int16 mono 16kHz (from AudioContext ScriptProcessor)
    - Text frame "__END_AUDIO__": signals end of user's speech turn

Backend sends:
    - Binary frames: WAV audio bytes (TTS output)
    - Text frame "__END_AFTER_AUDIO__": signals conversation is over
"""

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.db.session import SessionLocal

from app.services.sarvam.stt_service import SarvamSTTService
from app.services.conversation.orchestrator import ConversationOrchestrator
from app.services.conversation.persistence_service import PersistenceService
from app.repositories.conversation_repository import ConversationRepository


router = APIRouter()


@router.websocket("/ws/conversation")
async def conversation_websocket(websocket: WebSocket):
    """
    Main WebSocket endpoint for voice conversation.

    Accepts binary PCM Int16 audio frames from the frontend AudioContext,
    transcribes via Sarvam STT, generates a rule-based response via
    EventResponder, converts to speech via Sarvam TTS, and streams
    audio bytes back to the frontend.

    Sends __END_AFTER_AUDIO__ text frame when the conversation ends
    so the frontend can close the WebSocket after the farewell audio plays.
    """

    await websocket.accept()
    print("WebSocket client connected.", flush=True)

    db                  = SessionLocal()
    persistence_service = PersistenceService(db=db)
    stt_service         = SarvamSTTService()

    conversation = ConversationRepository.create_conversation(
        db=db, user_id=None
    )
    conversation_id = str(conversation.id)

    orchestrator = ConversationOrchestrator(
        persistence_service=persistence_service
    )

    try:

        while True:

            # ── Collect PCM Int16 chunks until __END_AUDIO__ ─────────
            audio_chunks = []
            disconnected = False

            while True:

                try:
                    message = await websocket.receive()

                except WebSocketDisconnect:
                    disconnected = True
                    break

                # End-of-turn signal from frontend
                if (
                    "text" in message
                    and message["text"] == "__END_AUDIO__"
                ):
                    break

                # Raw PCM binary chunk from AudioContext ScriptProcessor
                if "bytes" in message and message["bytes"]:
                    audio_chunks.append(message["bytes"])

            if disconnected:
                break

            if not audio_chunks:
                print("No audio received, skipping.", flush=True)
                continue

            # ── STT: PCM chunks → transcript (WAV wrapping done inside) ──
            print("Sending audio to STT...", flush=True)

            stt_response = await stt_service.transcribe_stream(
                audio_chunks=audio_chunks
            )

            user_text     = stt_response.get("transcript", "").strip()
            language_code = stt_response.get("language_code", "en-IN")

            if not user_text:
                print("Empty transcript, skipping.", flush=True)
                continue

            print(f"Transcribed: {user_text}", flush=True)

            # ── Orchestrator: text → EventResponder → TTS → audio ────
            end_conversation = False

            async for chunk in orchestrator.stream_response_audio(
                conversation_id=conversation_id,
                user_message=user_text,
                language_code=language_code
            ):
                if chunk["audio"]:
                    await websocket.send_bytes(chunk["audio"])
                    print("Audio chunk sent to frontend.", flush=True)

                if chunk["end_conversation"]:
                    end_conversation = True

                if chunk["done"]:
                    print(
                        f"Response done: {chunk['assistant_response']}",
                        flush=True
                    )

            # ── Farewell → close WebSocket ────────────────────────────
            if end_conversation:
                await websocket.send_text("__END_AFTER_AUDIO__")
                print(
                    "Conversation ended. Sent __END_AFTER_AUDIO__.",
                    flush=True
                )
                break

    except WebSocketDisconnect:
        print("WebSocket disconnected by client.", flush=True)

    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)
        import traceback
        traceback.print_exc()

    finally:
        await stt_service.close_stream()
        db.close()
        print("Cleanup done.", flush=True)