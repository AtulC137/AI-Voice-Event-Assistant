"""
Main FastAPI application entry point.
Handles:
- FastAPI initialization
- Router registration
- Application configuration
"""

from fastapi import FastAPI
from app.api.routes.conversation import (
    router as conversation_router
)

from app.api.routes.health import router as health_router


app = FastAPI(
    title="AI Voice Event Assistant",
    version="1.0.0"
)


app.include_router(health_router)
app.include_router(conversation_router)