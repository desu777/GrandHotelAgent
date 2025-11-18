"""
Centralized logging configuration for GrandHotel Agent.
Supports different formats for development (human-readable text) and production (JSON).
Uses ContextVar for automatic sessionId/traceId propagation across async contexts.
"""
import logging
import sys
from datetime import datetime, timezone
from typing import Any
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

from .config import APP_ENV, LOG_LEVEL


# Context variables for session tracking (set by middleware)
session_id_ctx: ContextVar[str | None] = ContextVar("session_id", default=None)
trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    JSON formatter that automatically includes sessionId and traceId from ContextVar.
    Also adds service metadata for structured logging in production.
    """

    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO8601 UTC
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add service metadata
        log_record["service"] = "grandhotel-agent"
        log_record["level"] = record.levelname

        # Extract component from logger name (e.g., "grandhotel_agent.services.agent_service" -> "agent")
        logger_parts = record.name.split(".")
        if len(logger_parts) >= 3:
            component = logger_parts[2]  # services, routers, tools
        elif len(logger_parts) == 2:
            component = logger_parts[1]  # server, config, etc.
        else:
            component = record.name
        log_record["component"] = component

        # Add sessionId and traceId from ContextVar (if available)
        session_id = session_id_ctx.get()
        trace_id = trace_id_ctx.get()

        if session_id:
            log_record["sessionId"] = session_id
        if trace_id:
            log_record["traceId"] = trace_id

        # Ensure message is always present
        if "message" not in log_record:
            log_record["message"] = record.getMessage()


class ContextAwareTextFormatter(logging.Formatter):
    """
    Text formatter that includes sessionId and traceId from ContextVar.
    Used for development mode for better readability.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Get context vars
        session_id = session_id_ctx.get()
        trace_id = trace_id_ctx.get()

        # Build context suffix
        context_parts = []
        if session_id:
            context_parts.append(f"session={session_id[:8]}")  # Shortened for readability
        if trace_id:
            context_parts.append(f"trace={trace_id[:8]}")

        context_suffix = f" | {' '.join(context_parts)}" if context_parts else ""

        # Format the base message
        base_formatted = super().format(record)

        return f"{base_formatted}{context_suffix}"


def setup_logging() -> None:
    """
    Configure global logging for the application.
    Called once at application startup.

    - Development: Human-readable text format with DEBUG level
    - Production: JSON format with INFO level
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Parse log level from config
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers (avoid duplicates)
    root_logger.handlers.clear()

    # Create stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    # Choose formatter based on environment
    if APP_ENV == "production":
        # JSON formatter for production (log aggregation friendly)
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(service)s %(component)s %(message)s",
            rename_fields={"levelname": "level", "name": "logger"}
        )
    else:
        # Text formatter for development (human-readable)
        formatter = ContextAwareTextFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Optionally adjust third-party logger levels to reduce noise
    # (uvicorn, httpx, redis logs are useful but verbose in DEBUG)
    if APP_ENV == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    # Log the logging configuration itself (meta!)
    logger = get_logger(__name__)
    logger.debug(
        "Logging configured",
        extra={
            "component": "logging",
            "app_env": APP_ENV,
            "log_level": LOG_LEVEL,
            "format": "json" if APP_ENV == "production" else "text"
        }
    )


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened", extra={"key": "value"})
    """
    return logging.getLogger(name)
