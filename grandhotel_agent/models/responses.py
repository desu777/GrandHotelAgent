"""
Response models for /agent/chat endpoint.
Based on README_pl.md specification.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class AudioOutput(BaseModel):
    """Audio output for voice mode"""
    mimeType: str = Field(..., description="Audio MIME type (audio/mpeg)")
    data: str = Field(..., description="Base64 encoded MP3 data")


class ToolTrace(BaseModel):
    """Trace of tool execution"""
    name: str = Field(..., description="Tool name")
    status: str = Field(..., description="Execution status (OK, ERROR)")
    durationMs: int = Field(..., description="Execution duration in milliseconds")


class ChatResponse(BaseModel):
    """
    POST /agent/chat response body (200 OK).
    """
    sessionId: str = Field(..., description="Session UUID v4")
    language: str = Field(..., description="Detected language (BCP-47)")
    reply: str = Field(..., description="Agent's text response")
    audio: Optional[AudioOutput] = Field(None, description="TTS audio (if voiceMode=true)")
    toolTrace: Optional[List[ToolTrace]] = Field(None, description="Tool execution trace")


class ErrorResponse(BaseModel):
    """Standard error envelope"""
    code: str = Field(..., description="Error code constant")
    message: str = Field(..., description="Human-readable error message")
    status: int = Field(..., description="HTTP status code")
    traceId: Optional[str] = Field(None, description="Trace ID for debugging")
    details: Optional[dict] = Field(None, description="Additional error context")


class HealthResponse(BaseModel):
    """GET /agent/health response"""
    status: str = Field(default="ok", description="Service status")
    version: str = Field(default="1.0.0", description="API version")
