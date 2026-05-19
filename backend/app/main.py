"""
Main FastAPI application entry point.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.conversation import router as conversation_router
from app.api.routes.tts import router as tts_router
from app.api.routes.health import router as health_router


os.makedirs("storage/input_audio", exist_ok=True)
os.makedirs("storage/output_audio", exist_ok=True)

app = FastAPI(
    title="AI Voice Event Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tts_router)
app.include_router(health_router)
app.include_router(conversation_router)
