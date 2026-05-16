"""
Sarvam realtime streaming STT service.
"""

import json
import websockets

from app.core.config import settings


class SarvamStreamingSTTService:
    """
    Handles realtime STT websocket.
    """

    def __init__(self):

        self.websocket = None


    async def connect(self):
        """
        Open websocket connection.
        """

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


    async def send_audio_chunk(
        self,
        audio_data: bytes
    ):
        """
        Send audio chunk.
        """

        await self.websocket.send(
            audio_data
        )


    async def flush(self):
        """
        Finalize transcription.
        """

        await self.websocket.send(
            json.dumps(
                {
                    "type":"flush"
                }
            )
        )


    async def receive_transcript(self):
        """
        Receive transcript.
        """

        response = (
            await self.websocket.recv()
        )

        return json.loads(
            response
        )


    async def close(self):

        if self.websocket:

            await self.websocket.close()