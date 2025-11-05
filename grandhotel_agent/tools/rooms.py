"""
rooms_list tool for Gemini Function Calling.
"""
import httpx
from grandhotel_agent.config import BACKEND_URL


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

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/rooms",
            headers=headers
        )
        response.raise_for_status()
        rooms = response.json()

        return {"result": rooms}


# Tool registry for dispatcher
AVAILABLE_TOOLS = {
    "rooms_list": {
        "declaration": ROOMS_LIST_DECLARATION,
        "execute": execute_rooms_list
    }
}
