"""
SARVAM LLM service.

Handles:
- conversational AI responses
- contextual chat completion
- multilingual interaction
"""

from typing import List

from app.services.sarvam.client import SarvamAPIClient


class SarvamLLMService:
    """
    Service for generating conversational AI responses
    using SARVAM LLM API.
    """

    def __init__(self):
        """
        Initialize SARVAM API client.
        """

        self.client = SarvamAPIClient()

    async def generate_response(
        self,
        messages: List[dict]
    ):
        """
        Generate AI response using conversation messages.
        """

        payload = {
            "model": "sarvam-m",
            "messages": messages,
            "temperature": 0.7
        }

        response = await self.client.post(
            endpoint="/v1/chat/completions",
            json=payload
        )

        return response.json()