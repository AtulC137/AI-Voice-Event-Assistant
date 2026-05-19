"""
Welcome audio HTTP route (optional; WebSocket welcome is primary).
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.conversation.conversation_messages import welcome_message
from app.services.sarvam.tts_service import SarvamTTSService


router = APIRouter()
tts_service = SarvamTTSService()


class WelcomeRequest(BaseModel):
    text: str | None = None
    language_code: str = "en-IN"


@router.post("/generate-welcome-audio")
async def generate_welcome_audio(request: WelcomeRequest):
    text = request.text or welcome_message(request.language_code)
    file_path = await tts_service.generate_speech(
        text=text,
        language_code=request.language_code,
    )
    return FileResponse(file_path, media_type="audio/wav")
