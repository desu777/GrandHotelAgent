"""
Agent endpoints: POST /agent/chat + GET /agent/health
Based on README.md specification.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException
from grandhotel_agent.models.requests import ChatRequest
from grandhotel_agent.models.responses import ChatResponse, HealthResponse, ErrorResponse
from grandhotel_agent.services.agent_service import AgentService
from grandhotel_agent.services.lang_service import detect_language_bcp47
from grandhotel_agent.services.redis_store import get_session_store
from grandhotel_agent.config import SESSION_MAX_MESSAGES
from grandhotel_agent.logging_config import get_logger
from grandhotel_agent.middleware import set_logging_context

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

    # Process with agent service
    try:
        agent = AgentService()

        # Use text message (audio not implemented yet - TODO)
        user_message = request.message or "[Audio input - transcription TODO]"

        # Detect language only if not in session
        if not language_code:
            language_code = await detect_language_bcp47(request.message) if request.message else "en-US"
            # Save detected language to session
            if session is not None:
                session["language"] = language_code

        # FC loop with conversation history
        reply, tool_traces = await agent.chat(user_message, jwt, language_code, history=history)

        # Update session with new messages
        if store and session is not None:
            try:
                now_iso = datetime.now(timezone.utc).isoformat()

                # Append new messages to history
                new_messages = [
                    {"role": "user", "content": user_message, "ts": now_iso},
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
                "has_tool_trace": bool(tool_traces)
            }
        )

        return ChatResponse(
            sessionId=request.sessionId,
            language=language_code,
            reply=reply,
            audio=None,  # TODO: TTS when voiceMode=true
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
