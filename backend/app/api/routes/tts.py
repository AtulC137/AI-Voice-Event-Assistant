"""
Welcome audio route.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from pydantic import BaseModel

from app.services.sarvam.tts_service import (
    SarvamTTSService
)


router = APIRouter()

tts_service = SarvamTTSService()


class WelcomeRequest(
    BaseModel
):
    text:str


@router.post(
    "/generate-welcome-audio"
)
async def generate_welcome_audio(
    request:WelcomeRequest
):

    file_path = (
        await tts_service
        .generate_audio(
            text=request.text
        )
    )

    return FileResponse(
        file_path,
        media_type="audio/wav"
    )