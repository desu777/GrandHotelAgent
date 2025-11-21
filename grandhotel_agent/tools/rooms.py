"""
Room-related tools for Gemini Function Calling.
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


# rooms_get declaration and executor
ROOMS_GET_DECLARATION = {
    "name": "rooms_get",
    "description": (
        "Get detailed information about a specific hotel room by its ID. "
        "Returns room type, price per night, capacity, and amenities."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Room ID to retrieve details for"
            }
        },
        "required": ["id"]
    }
}


async def execute_rooms_get(args: dict, jwt: str | None = None) -> dict:
    """
    Execute rooms_get tool: GET /api/v1/rooms/{id} from backend.

    Args:
        args: Dict with key "id" (integer)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing room details

    Raises:
        httpx.HTTPStatusError: If backend returns error (e.g., room not found)
    """
    room_id = args.get("id")
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/rooms/{room_id}"
    logger.debug(
        "Backend API call: rooms_get",
        extra={
            "component": "tool",
            "tool": "rooms_get",
            "url": url,
            "room_id": room_id
        }
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            room = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "rooms_get",
                    "room_id": room_id
                }
            )

            return {"result": room}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "rooms_get",
                "status_code": e.response.status_code,
                "url": url,
                "room_id": room_id
            }
        )
        raise


# rooms_filter declaration and executor
ROOMS_FILTER_DECLARATION = {
    "name": "rooms_filter",
    "description": (
        "Get available hotel rooms matching specific criteria (check-in/out dates, "
        "number of adults and children). Returns list of rooms that are available "
        "for the specified period and can accommodate the requested number of guests."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "checkInDate": {
                "type": "string",
                "description": "Check-in date in YYYY-MM-DD format (e.g. 2025-10-15)"
            },
            "checkOutDate": {
                "type": "string",
                "description": "Check-out date in YYYY-MM-DD format (e.g. 2025-10-18)"
            },
            "numberOfAdults": {
                "type": "integer",
                "description": "Number of adult guests (minimum 1)"
            },
            "numberOfChildren": {
                "type": "integer",
                "description": "Number of children (0 or more)"
            }
        },
        "required": ["checkInDate", "checkOutDate", "numberOfAdults", "numberOfChildren"]
    }
}


async def execute_rooms_filter(args: dict, jwt: str | None = None) -> dict:
    """
    Execute rooms_filter tool: POST /api/v1/rooms/filter to backend.

    Args:
        args: Dict with keys: checkInDate, checkOutDate, numberOfAdults, numberOfChildren
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing list of available rooms

    Raises:
        httpx.HTTPStatusError: If backend returns error (e.g., invalid dates)
    """
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/rooms/filter"
    logger.debug(
        "Backend API call: rooms_filter",
        extra={
            "component": "tool",
            "tool": "rooms_filter",
            "url": url,
            "filter_params": args
        }
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=args)
            response.raise_for_status()
            rooms = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "rooms_filter",
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
                "tool": "rooms_filter",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# Tool registry for room-related tools
ROOMS_TOOLS = {
    "rooms_list": {
        "declaration": ROOMS_LIST_DECLARATION,
        "execute": execute_rooms_list
    },
    "rooms_get": {
        "declaration": ROOMS_GET_DECLARATION,
        "execute": execute_rooms_get
    },
    "rooms_filter": {
        "declaration": ROOMS_FILTER_DECLARATION,
        "execute": execute_rooms_filter
    }
}
