"""
Reusable async HTTP client for SARVAM AI APIs.
Handles:
- authentication headers
- async API requests
- centralized HTTP configuration
"""

import httpx

from app.core.config import settings


class SarvamAPIClient:
    """
    Centralized async client for communicating
    with SARVAM AI services.
    """

    BASE_URL = "https://api.sarvam.ai"

    def __init__(self):
        """
        Initialize reusable async HTTP client.
        """

        self.headers = {
            "api-subscription-key": settings.SARVAM_API_KEY
        }

    async def post(
        self,
        endpoint: str,
        data=None,
        json=None,
        files=None
    ):
        """
        Send async POST request to SARVAM API.
        """

        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.post(
                url=f"{self.BASE_URL}{endpoint}",
                headers=self.headers,
                data=data,
                json=json,
                files=files
            )

            response.raise_for_status()

            return response