"""
WebSocket conversation routes.
"""

import uuid

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect
)

from app.db.session import (
    SessionLocal
)

from app.services.sarvam.stt_service import (
    SarvamSTTService
)

from app.services.conversation.orchestrator import (
    ConversationOrchestrator
)

from app.services.conversation.intent_detector import (
    IntentDetector
)

from app.services.conversation.persistence_service import (
    PersistenceService
)

from app.repositories.conversation_repository import (
    ConversationRepository
)


router = APIRouter()

stt_service = SarvamSTTService()

MSG_START="__START_CONVERSATION__"
MSG_END_AUDIO="__END_AUDIO__"
MSG_INTERRUPT="__INTERRUPT__"
MSG_READY="__READY__"
MSG_END_AFTER_AUDIO="__END_AFTER_AUDIO__"


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

    conversation_id = str(
        conversation.id
    )

    orchestrator = (
        ConversationOrchestrator(
            persistence_service
        )
    )

    conversation_started=False
    last_language_code="en-IN"

    try:

        while True:

            audio_buffer=bytearray()

            while True:

                message=await websocket.receive()

                if (
                    message.get(
                        "type"
                    )
                    ==
                    "websocket.disconnect"
                ):
                    raise (
                        WebSocketDisconnect()
                    )

                text=message.get(
                    "text"
                )

                if text:

                    if (
                        text==MSG_START
                        and
                        not conversation_started
                    ):

                        conversation_started=True

                        welcome=(
                            await orchestrator
                            .generate_welcome_audio(
                                conversation_id,
                                last_language_code
                            )
                        )

                        await websocket.send_bytes(
                            welcome["audio_bytes"]
                        )

                        await websocket.send_text(
                            MSG_READY
                        )

                        break


                    if text==MSG_INTERRUPT:
                        audio_buffer.clear()
                        continue


                    if text==MSG_END_AUDIO:
                        break


                    continue


                chunk=message.get(
                    "bytes"
                )

                if chunk:
                    audio_buffer.extend(
                        chunk
                    )


            if (
                not conversation_started
                or
                not audio_buffer
            ):
                continue


            input_audio_path=(
                f"storage/input_audio/"
                f"{uuid.uuid4()}.webm"
            )

            with open(
                input_audio_path,
                "wb"
            ) as audio_file:

                audio_file.write(
                    bytes(
                        audio_buffer
                    )
                )


            stt_response=(
                await stt_service
                .transcribe_audio(
                    input_audio_path
                )
            )

            user_text=(
                stt_response.get(
                    "transcript",
                    ""
                ).strip()
            )


            if not user_text:

                await websocket.send_text(
                    MSG_READY
                )

                continue


            language_code=(
                stt_response.get(
                    "language_code",
                    "en-IN"
                )
            )

            last_language_code=(
                language_code
            )

            print(
                f"Transcribed Text: {user_text}",
                flush=True
            )


            intent_preview=(
                IntentDetector
                .detect_intent(
                    user_text
                )
            )

            if intent_preview:

                print(
                    f"Detected Intent: {intent_preview}",
                    flush=True
                )


            result=(
                await orchestrator
                .process_user_message(
                    conversation_id=
                    conversation_id,

                    user_message=
                    user_text,

                    language_code=
                    language_code
                )
            )


            await websocket.send_bytes(
                result["audio_bytes"]
            )


            if (
                result[
                    "end_conversation"
                ]
            ):

                print(
                    "End conversation — closing WebSocket.",
                    flush=True
                )

                await websocket.send_text(
                    MSG_END_AFTER_AUDIO
                )

                break


            await websocket.send_text(
                MSG_READY
            )

            print(
                "AI response sent.",
                flush=True
            )


    except WebSocketDisconnect:

        print(
            "WebSocket disconnected.",
            flush=True
        )

    finally:

        db.close()