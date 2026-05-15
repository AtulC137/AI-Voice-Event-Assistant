"""
Health check routes.
Used for:
- Backend status verification
- Docker testing
- Deployment health checks
"""

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    Returns backend running status.
    """

    return {
        "status": "ok"
    }