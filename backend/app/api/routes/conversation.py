"""
WebSocket conversation routes.

Handles:
- realtime voice conversations
- audio reception
- STT processing
- conversation orchestration
- TTS response generation
"""

import uuid

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.services.sarvam.stt_service import (
    SarvamSTTService
)

from app.services.conversation.orchestrator import (
    ConversationOrchestrator
)


router = APIRouter()


stt_service = SarvamSTTService()

conversation_orchestrator = (
    ConversationOrchestrator()
)


@router.websocket("/ws/conversation")
async def conversation_websocket(
    websocket: WebSocket
):
    """
    Main realtime conversation websocket endpoint.
    """

    await websocket.accept()

    print(
        "WebSocket client connected.",
        flush=True
    )

    conversation_id = str(uuid.uuid4())

    try:

        while True:

            audio_bytes = (
                await websocket.receive_bytes()
            )

            input_audio_path = (
                f"tests/audio_samples/"
                f"{uuid.uuid4()}.wav"
            )

            with open(
                input_audio_path,
                "wb"
            ) as audio_file:

                audio_file.write(audio_bytes)

            print(
                f"Saved Input Audio: "
                f"{input_audio_path}",
                flush=True
            )

            stt_response = (
                await stt_service.transcribe_audio(
                    file_path=input_audio_path
                )
            )

            user_text = (
                stt_response["transcript"]
            )

            language_code = (
                stt_response["language_code"]
            )

            print(
                f"Transcribed Text: "
                f"{user_text}",
                flush=True
            )

            orchestrator_response = (
                await conversation_orchestrator
                .process_user_message(
                    conversation_id=conversation_id,
                    user_message=user_text,
                    language_code=language_code
                )
            )

            response_audio_path = (
                orchestrator_response["audio_file"]
            )

            with open(
                response_audio_path,
                "rb"
            ) as audio_file:

                response_audio_bytes = (
                    audio_file.read()
                )

            await websocket.send_bytes(
                response_audio_bytes
            )

            print(
                "AI response audio sent.",
                flush=True
            )

    except WebSocketDisconnect:

        print(
            "WebSocket client disconnected.",
            flush=True
        )

    except Exception as error:

        print(
            f"WebSocket Error: {error}",
            flush=True
        )