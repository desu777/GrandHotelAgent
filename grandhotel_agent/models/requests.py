"""
Request models for /agent/chat endpoint.
Based on README_pl.md specification.
"""
from typing import Optional
from pydantic import BaseModel, Field


class AudioInput(BaseModel):
    """Audio input for voice mode"""
    mimeType: str = Field(..., description="Audio MIME type (audio/wav, audio/mp3, etc.)")
    data: str = Field(..., description="Base64 encoded audio data")


class ClientMeta(BaseModel):
    """Optional client metadata"""
    traceId: Optional[str] = Field(None, max_length=64, description="Client trace ID")


class ChatRequest(BaseModel):
    """
    POST /agent/chat request body.

    At least one of 'message' or 'audio' must be provided.
    """
    sessionId: str = Field(..., description="Session UUID v4")
    message: Optional[str] = Field(None, description="Text message from user")
    audio: Optional[AudioInput] = Field(None, description="Audio input (voice mode)")
    voiceMode: bool = Field(False, description="Enable TTS response")
    client: Optional[ClientMeta] = Field(None, description="Client metadata")
