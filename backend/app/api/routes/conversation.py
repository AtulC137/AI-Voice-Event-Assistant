"""
WebSocket conversation routes.
"""

import uuid

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.db.session import SessionLocal

from app.services.sarvam.stt_service import (
    SarvamSTTService
)

from app.services.conversation.orchestrator import (
    ConversationOrchestrator
)

from app.services.conversation.persistence_service import (
    PersistenceService
)

from app.repositories.conversation_repository import (
    ConversationRepository
)


router = APIRouter()

stt_service = SarvamSTTService()


@router.websocket("/ws/conversation")
async def conversation_websocket(
    websocket: WebSocket
):

    await websocket.accept()

    print(
        "WebSocket client connected.",
        flush=True
    )

    db = SessionLocal()

    persistence_service = (
        PersistenceService(
            db=db
        )
    )

    conversation = (
        ConversationRepository
        .create_conversation(
            db=db,
            user_id=None
        )
    )

    conversation_id = (
        str(
            conversation.id
        )
    )

    conversation_orchestrator = (
        ConversationOrchestrator(
            persistence_service=
            persistence_service
        )
    )

    try:

        while True:

            audio_buffer = bytearray()

            while True:

                message = (
                    await websocket.receive()
                )

                if (
                    "text" in message
                    and
                    message["text"]
                    ==
                    "__END_AUDIO__"
                ):
                    break


                if (
                    "bytes" in message
                    and
                    message["bytes"]
                ):

                    chunk = (
                        message["bytes"]
                    )

                    audio_buffer.extend(
                        chunk
                    )

                    try:

                        await (
                            stt_service
                            .stream_transcript_preview(
                                chunk
                            )
                        )

                    except:

                        pass


            if not audio_buffer:

                continue


            audio_bytes = bytes(
                audio_buffer
            )


            input_audio_path = (
                f"storage/input_audio/"
                f"{uuid.uuid4()}.wav"
            )


            with open(
                input_audio_path,
                "wb"
            ) as audio_file:

                audio_file.write(
                    audio_bytes
                )


            stt_response = (
                await stt_service
                .transcribe_audio(
                    file_path=
                    input_audio_path
                )
            )


            user_text = (
                stt_response[
                    "transcript"
                ]
            )


            if (
                not user_text.strip()
            ):
                continue


            language_code = (
                stt_response[
                    "language_code"
                ]
            )


            print(
                f"Transcribed Text: "
                f"{user_text}",
                flush=True
            )


            orchestrator_response = (
                await
                conversation_orchestrator
                .process_user_message(
                    conversation_id=
                    conversation_id,

                    user_message=
                    user_text,

                    language_code=
                    language_code
                )
            )


            with open(
                orchestrator_response[
                    "audio_file"
                ],
                "rb"
            ) as audio_file:

                response_audio_bytes = (
                    audio_file.read()
                )


            await websocket.send_bytes(
                response_audio_bytes
            )


            if (
                orchestrator_response[
                    "end_conversation"
                ]
            ):

                await websocket.send_text(
                    "__END_AFTER_AUDIO__"
                )

                break


            print(
                "AI response audio sent.",
                flush=True
            )

    except WebSocketDisconnect:

        print(
            "WebSocket disconnected.",
            flush=True
        )

    finally:

        await stt_service.close_stream()

        db.close()