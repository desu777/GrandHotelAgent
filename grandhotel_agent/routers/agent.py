"""
Agent endpoints: POST /agent/chat + GET /agent/health
Based on README.md specification.
"""
from fastapi import APIRouter, Header, HTTPException
from grandhotel_agent.models.requests import ChatRequest
from grandhotel_agent.models.responses import ChatResponse, HealthResponse, ErrorResponse
from grandhotel_agent.services.agent_service import AgentService
from grandhotel_agent.services.lang_service import detect_language_bcp47
from grandhotel_agent.services.redis_store import get_session_store


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

    # Touch Redis session 
    try:
        store = await get_session_store()
        await store.touch(request.sessionId)
    except Exception as e:
        print(f"[Redis] Error touching session: {e}")
        # Continue without Redis (non-blocking)

    # Process with agent service
    try:
        agent = AgentService()

        # Use text message (audio not implemented yet - TODO)
        user_message = request.message or "[Audio input - transcription TODO]"

        # Pre-flight LLM language detection (BCP-47) using lite model
        # If message is missing (voice only path not yet implemented), use safe default.
        language_code = await detect_language_bcp47(request.message) if request.message else "en-US"

        # FC loop
        reply, tool_traces = await agent.chat(user_message, jwt, language_code)

        return ChatResponse(
            sessionId=request.sessionId,
            language=language_code,
            reply=reply,
            audio=None,  # TODO: TTS when voiceMode=true
            toolTrace=tool_traces if tool_traces else None
        )

    except Exception as e:
        print(f"[Agent] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "status": 500
            }
        )
