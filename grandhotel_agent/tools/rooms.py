"""
rooms_list tool for Gemini Function Calling.
"""
import httpx
from grandhotel_agent.config import BACKEND_URL
from grandhotel_agent.logging_config import get_logger

logger = get_logger(__name__)


# Function declaration for Gemini (matches Google docs format)
ROOMS_LIST_DECLARATION = {
    "name": "rooms_list",
    "description": "Get list of all available hotel rooms with details (type, price, capacity, amenities)",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}


async def execute_rooms_list(args: dict, jwt: str | None = None) -> dict:
    """
    Execute rooms_list tool: GET /api/v1/rooms from backend.

    Args:
        args: Empty dict (no parameters for this tool)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing list of rooms

    Raises:
        httpx.HTTPStatusError: If backend returns error
    """
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/rooms"
    logger.debug(
        "Backend API call: rooms_list",
        extra={"component": "tool", "tool": "rooms_list", "url": url}
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            rooms = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "rooms_list",
                    "response_count": len(rooms) if isinstance(rooms, list) else None
                }
            )

            return {"result": rooms}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "rooms_list",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# Tool registry for dispatcher
AVAILABLE_TOOLS = {
    "rooms_list": {
        "declaration": ROOMS_LIST_DECLARATION,
        "execute": execute_rooms_list
    }
}
