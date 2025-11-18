"""
Logging context middleware helpers.
Provides utilities to set sessionId and traceId in ContextVar for automatic log enrichment.
"""
from typing import Optional

# Import context variables from logging_config
from .logging_config import session_id_ctx, trace_id_ctx


def set_logging_context(session_id: Optional[str] = None, trace_id: Optional[str] = None) -> None:
    """
    Set sessionId and traceId in ContextVar for current async context.
    This enriches all logs within the current request with session tracking info.

    Should be called at the beginning of request handlers (e.g., in routers).

    Args:
        session_id: Session UUID from ChatRequest.sessionId
        trace_id: Client trace ID from ChatRequest.client.traceId

    Usage:
        @router.post("/chat")
        async def chat(request: ChatRequest):
            set_logging_context(request.sessionId, request.client.traceId if request.client else None)
            # ... rest of handler
    """
    if session_id:
        session_id_ctx.set(session_id)
    if trace_id:
        trace_id_ctx.set(trace_id)


def clear_logging_context() -> None:
    """
    Clear logging context variables.
    Not strictly necessary as each request creates a new async context,
    but provided for explicit cleanup if needed.
    """
    session_id_ctx.set(None)
    trace_id_ctx.set(None)
