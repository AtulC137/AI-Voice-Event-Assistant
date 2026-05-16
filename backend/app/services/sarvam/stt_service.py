"""
SARVAM Speech-to-Text service.

Supports:
- file transcription
- transcript preview
"""

import json
import websockets

from app.core.config import settings

from app.services.sarvam.client import (
    SarvamAPIClient
)


class SarvamSTTService:

    def __init__(self):

        self.client = (
            SarvamAPIClient()
        )

        self.websocket = None


    async def connect_stream(
        self
    ):

        if self.websocket:

            return


        websocket_url = (
            "wss://api.sarvam.ai/"
            "speech-to-text/ws"
            "?language-code=unknown"
            "&model=saaras:v3"
        )


        self.websocket = (
            await websockets.connect(
                websocket_url,
                additional_headers={
                    "Api-Subscription-Key":
                    settings.SARVAM_API_KEY
                }
            )
        )

        print(
            "Streaming STT connected.",
            flush=True
        )


    async def stream_transcript_preview(
        self,
        audio_chunk: bytes
    ):
        """
        Preview only.
        Does not affect main flow.
        """

        try:

            await self.connect_stream()

            await self.websocket.send(
                audio_chunk
            )

            response = (
                await self.websocket.recv()
            )

            print(
                "Partial STT:",
                response,
                flush=True
            )

        except Exception as error:

            print(
                f"Preview Error: {error}",
                flush=True
            )


    async def close_stream(
        self
    ):

        if self.websocket:

            await self.websocket.close()

            self.websocket=None


    async def transcribe_audio(
        self,
        file_path: str
    ):

        with open(
            file_path,
            "rb"
        ) as audio_file:

            files = {
                "file":audio_file
            }

            data = {
                "model":"saaras:v3"
            }

            response = (
                await self.client.post(
                    endpoint=
                    "/speech-to-text",

                    data=data,

                    files=files
                )
            )

            return response.json()