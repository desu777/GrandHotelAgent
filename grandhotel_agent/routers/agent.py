"""
Agent endpoints: POST /agent/chat + GET /agent/health
Based on README.md specification.
"""
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException
from grandhotel_agent.models.requests import ChatRequest
from grandhotel_agent.models.responses import ChatResponse, HealthResponse, AudioOutput
from grandhotel_agent.services.agent_service import AgentService
from grandhotel_agent.services.lang_service import detect_language_bcp47
from grandhotel_agent.services.redis_store import get_session_store
from grandhotel_agent.config import SESSION_MAX_MESSAGES
from grandhotel_agent.logging_config import get_logger
from grandhotel_agent.middleware import set_logging_context

# Whitelist of supported audio MIME types
ALLOWED_AUDIO_MIMES = {
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/wav",
    "audio/mp3",
    "audio/mpeg",
    "audio/ogg",
}

# Max audio size (Gemini limit ~20MB, we use 15MB for safety)
MAX_AUDIO_SIZE_BYTES = 15 * 1024 * 1024

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    GET /agent/health - Service health check (public endpoint).

    Returns:
        HealthResponse with status and version
    """
    return HealthResponse(status="ok", version="1.0.0")


# Removed static heuristics; language detection handled by LLM pre-flight


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: str | None = Header(None)
):
    """
    POST /agent/chat - Main chat endpoint with Gemini FC loop.

    Workflow:
    1. Validate request (message or audio required)
    2. Extract JWT from Authorization header (minimal auth)
    3. Touch Redis session (sliding TTL 60 min)
    4. Call agent service with FC loop
    5. Return response with reply + tool traces

    Args:
        request: ChatRequest body
        authorization: Bearer JWT token (optional for now)

    Returns:
        ChatResponse with agent reply

    Raises:
        HTTPException 400: Invalid request
        HTTPException 500: Internal error
    """
    # Set logging context for all logs in this request
    set_logging_context(
        session_id=request.sessionId,
        trace_id=request.client.traceId if request.client else None
    )

    # Log incoming request
    logger.info(
        "Request: POST /agent/chat",
        extra={
            "component": "router",
            "endpoint": "/agent/chat",
            "voice_mode": request.voiceMode,
            "has_message": bool(request.message),
            "has_audio": bool(request.audio)
        }
    )

    # Validate: at least message or audio required
    if not request.message and not request.audio:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "BAD_REQUEST",
                "message": "Either 'message' or 'audio' must be provided",
                "status": 400
            }
        )

    # Extract JWT (minimal parsing - no verification yet)
    jwt = None
    if authorization and authorization.startswith("Bearer "):
        jwt = authorization[7:]  

    # Load session from Redis (conversation history + language)
    store = None
    session = None
    history = []
    language_code = None

    try:
        store = await get_session_store()
        session = await store.get(request.sessionId)

        if session:
            # Extract history (defensive)
            history = session.get("messages", [])
            if not isinstance(history, list):
                history = []

            # Reuse language from session if available
            language_code = session.get("language")
        else:
            # New session - will be created on first save
            session = {
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "language": None
            }

    except Exception as e:
        logger.warning(
            "Redis session load failed, degrading gracefully",
            exc_info=True,
            extra={"component": "redis", "operation": "load_session"}
        )
        # Continue without Redis (graceful degradation)
        store = None
        session = None
        history = []
        language_code = None

    # Parse audio input if provided
    audio_bytes = None
    audio_mime_type = None

    if request.audio:
        # Validate MIME type
        mime_base = request.audio.mimeType.split(";")[0]
        if mime_base not in ALLOWED_AUDIO_MIMES and request.audio.mimeType not in ALLOWED_AUDIO_MIMES:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "UNSUPPORTED_AUDIO_FORMAT",
                    "message": f"Unsupported audio format: {request.audio.mimeType}. Supported: {', '.join(ALLOWED_AUDIO_MIMES)}",
                    "status": 400
                }
            )

        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(request.audio.data)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_AUDIO_DATA",
                    "message": "Invalid base64 audio data",
                    "status": 400
                }
            )

        # Size check
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Audio too large ({len(audio_bytes)} bytes). Max: {MAX_AUDIO_SIZE_BYTES} bytes",
                    "status": 413
                }
            )

        audio_mime_type = request.audio.mimeType
        logger.debug(
            "Audio input parsed",
            extra={
                "component": "router",
                "audio_size_bytes": len(audio_bytes),
                "mime_type": audio_mime_type,
            }
        )

    # Process with agent service
    try:
        agent = AgentService()

        # Detect language from text message if available and not in session
        # For audio-only requests, we'll detect language from transcription after agent call
        language_detected_before_chat = False
        if not language_code and request.message:
            language_code = await detect_language_bcp47(request.message)
            language_detected_before_chat = True
            if session is not None:
                session["language"] = language_code

        # FC loop with conversation history (now supports audio)
        # For audio-only without prior language, use pl-PL as initial fallback
        reply, tool_traces, transcription = await agent.chat(
            user_message=request.message,
            jwt=jwt,
            language_code=language_code or "pl-PL",
            history=history,
            audio_bytes=audio_bytes,
            audio_mime_type=audio_mime_type,
        )

        # For audio-only requests: detect language from transcription and update session
        if not language_detected_before_chat and transcription:
            language_code = await detect_language_bcp47(transcription)
            if session is not None:
                session["language"] = language_code
            logger.debug(
                "Language detected from transcription",
                extra={"component": "router", "language": language_code}
            )

        # TTS synthesis if voiceMode=true
        audio_output = None
        if request.voiceMode and reply:
            try:
                from grandhotel_agent.services.tts_service import synthesize_speech, TTSError, TTSUnavailableError

                mp3_bytes = await synthesize_speech(reply)
                audio_output = AudioOutput(
                    mimeType="audio/mpeg",
                    data=base64.b64encode(mp3_bytes).decode("ascii"),
                )
                logger.info(
                    "TTS synthesis successful",
                    extra={
                        "component": "router",
                        "audio_output_bytes": len(mp3_bytes),
                    }
                )
            except TTSUnavailableError:
                logger.warning(
                    "TTS unavailable (API key not configured)",
                    extra={"component": "tts"}
                )
            except TTSError as e:
                logger.warning(
                    "TTS synthesis failed",
                    exc_info=True,
                    extra={"component": "tts"}
                )
            except Exception as e:
                logger.warning(
                    "TTS unexpected error",
                    exc_info=True,
                    extra={"component": "tts"}
                )
            # Graceful degradation - continue without audio

        # Determine user content for history
        # Priority: transcription from Gemini > text message > placeholder
        user_content = transcription or request.message or "[Voice input]"

        # Update session with new messages
        if store and session is not None:
            try:
                now_iso = datetime.now(timezone.utc).isoformat()

                # Append new messages to history
                new_messages = [
                    {"role": "user", "content": user_content, "ts": now_iso},
                    {"role": "assistant", "content": reply, "ts": now_iso}
                ]

                # Get current history and append
                current_messages = session.get("messages", [])
                if not isinstance(current_messages, list):
                    current_messages = []

                updated_messages = current_messages + new_messages

                # Trim to SESSION_MAX_MESSAGES
                if len(updated_messages) > SESSION_MAX_MESSAGES:
                    updated_messages = updated_messages[-SESSION_MAX_MESSAGES:]

                # Update session
                session["messages"] = updated_messages
                session["language"] = language_code

                # Save to Redis
                await store.set(request.sessionId, session)

            except Exception as e:
                logger.warning(
                    "Redis session save failed",
                    exc_info=True,
                    extra={"component": "redis", "operation": "save_session"}
                )
                # Non-blocking - continue with response

        # Log successful response
        logger.info(
            "Response: POST /agent/chat success",
            extra={
                "component": "router",
                "language": language_code,
                "has_tool_trace": bool(tool_traces),
                "has_audio_output": bool(audio_output),
                "voice_mode": request.voiceMode,
            }
        )

        return ChatResponse(
            sessionId=request.sessionId,
            language=language_code,
            reply=reply,
            audio=audio_output,
            toolTrace=tool_traces if tool_traces else None
        )

    except Exception as e:
        logger.error(
            "Agent error",
            exc_info=True,
            extra={"component": "router", "endpoint": "/agent/chat"}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "status": 500
            }
        )
