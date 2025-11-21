"""
Restaurant-related tools for Gemini Function Calling.
"""
import httpx
from grandhotel_agent.config import BACKEND_URL
from grandhotel_agent.logging_config import get_logger

logger = get_logger(__name__)


# restaurant_menu declaration and executor
RESTAURANT_MENU_DECLARATION = {
    "name": "restaurant_menu",
    "description": (
        "Get the full restaurant menu with dishes, descriptions and prices. "
        "Returns list of available dishes in the hotel restaurant."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}


async def execute_restaurant_menu(args: dict, jwt: str | None = None) -> dict:
    """
    Execute restaurant_menu tool: GET /api/v1/restaurant/menu from backend.

    Args:
        args: Empty dict (no parameters for this tool)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing menu items list

    Raises:
        httpx.HTTPStatusError: If backend returns error
    """
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/restaurant/menu"
    logger.debug(
        "Backend API call: restaurant_menu",
        extra={"component": "tool", "tool": "restaurant_menu", "url": url}
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            menu = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "restaurant_menu",
                    "response_count": len(menu) if isinstance(menu, list) else None
                }
            )

            return {"result": menu}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "restaurant_menu",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# restaurant_table_list declaration and executor
RESTAURANT_TABLE_LIST_DECLARATION = {
    "name": "restaurant_table_list",
    "description": (
        "Get list of all table reservations in the restaurant. "
        "Depending on the user's role, backend will return either their own reservations or all reservations."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}


async def execute_restaurant_table_list(args: dict, jwt: str | None = None) -> dict:
    """
    Execute restaurant_table_list tool: GET /api/v1/restaurant/reservations from backend.

    Args:
        args: Empty dict (no parameters for this tool)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing list of table reservations

    Raises:
        httpx.HTTPStatusError: If backend returns error
    """
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/restaurant/reservations"
    logger.debug(
        "Backend API call: restaurant_table_list",
        extra={"component": "tool", "tool": "restaurant_table_list", "url": url}
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            reservations = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "restaurant_table_list",
                    "response_count": len(reservations) if isinstance(reservations, list) else None
                }
            )

            return {"result": reservations}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "restaurant_table_list",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# restaurant_table_get declaration and executor
RESTAURANT_TABLE_GET_DECLARATION = {
    "name": "restaurant_table_get",
    "description": (
        "Get detailed information about a specific table reservation by its ID. "
        "Returns reservation date, time, number of guests, and status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Table reservation ID to retrieve details for"
            }
        },
        "required": ["id"]
    }
}


async def execute_restaurant_table_get(args: dict, jwt: str | None = None) -> dict:
    """
    Execute restaurant_table_get tool: GET /api/v1/restaurant/reservations/{id} from backend.

    Args:
        args: Dict with key "id" (integer)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing table reservation details

    Raises:
        httpx.HTTPStatusError: If backend returns error (e.g., reservation not found)
    """
    reservation_id = args.get("id")
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/restaurant/reservations/{reservation_id}"
    logger.debug(
        "Backend API call: restaurant_table_get",
        extra={
            "component": "tool",
            "tool": "restaurant_table_get",
            "url": url,
            "reservation_id": reservation_id
        }
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            reservation = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "restaurant_table_get",
                    "reservation_id": reservation_id
                }
            )

            return {"result": reservation}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "restaurant_table_get",
                "status_code": e.response.status_code,
                "url": url,
                "reservation_id": reservation_id
            }
        )
        raise


# restaurant_table_create declaration and executor
RESTAURANT_TABLE_CREATE_DECLARATION = {
    "name": "restaurant_table_create",
    "description": (
        "Reserve a table in the hotel restaurant. Requires date, time, and number of guests. "
        "Returns confirmation with reservation ID and status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Reservation date in YYYY-MM-DD format"
            },
            "time": {
                "type": "string",
                "description": "Reservation time in HH:MM format (e.g. 19:30)"
            },
            "guests": {
                "type": "integer",
                "description": "Number of guests for the table"
            }
        },
        "required": ["date", "time", "guests"]
    }
}


async def execute_restaurant_table_create(args: dict, jwt: str | None = None) -> dict:
    """
    Execute restaurant_table_create tool: POST /api/v1/restaurant/reservations to backend.

    Args:
        args: Dict with keys: date, time, guests
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing created table reservation details

    Raises:
        httpx.HTTPStatusError: If backend returns error (no availability, invalid time, etc.)
    """
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/restaurant/reservations"
    logger.debug(
        "Backend API call: restaurant_table_create",
        extra={
            "component": "tool",
            "tool": "restaurant_table_create",
            "url": url,
            "reservation_data": args
        }
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=args)
            response.raise_for_status()
            reservation = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "restaurant_table_create",
                    "reservation_id": reservation.get("id")
                }
            )

            return {"result": reservation}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "restaurant_table_create",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# restaurant_table_cancel declaration and executor
RESTAURANT_TABLE_CANCEL_DECLARATION = {
    "name": "restaurant_table_cancel",
    "description": (
        "Cancel an existing table reservation in the restaurant by its ID. "
        "This permanently cancels the table reservation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Table reservation ID to cancel"
            }
        },
        "required": ["id"]
    }
}


async def execute_restaurant_table_cancel(args: dict, jwt: str | None = None) -> dict:
    """
    Execute restaurant_table_cancel tool: DELETE /api/v1/restaurant/reservations/{id} to backend.

    Args:
        args: Dict with key "id" (integer)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result": "success" on successful cancellation

    Raises:
        httpx.HTTPStatusError: If backend returns error (e.g., reservation not found)
    """
    reservation_id = args.get("id")
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/restaurant/reservations/{reservation_id}"
    logger.debug(
        "Backend API call: restaurant_table_cancel",
        extra={
            "component": "tool",
            "tool": "restaurant_table_cancel",
            "url": url,
            "reservation_id": reservation_id
        }
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()

            # Backend returns 204 No Content on success
            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "restaurant_table_cancel",
                    "reservation_id": reservation_id
                }
            )

            # Return success message since 204 has no content
            return {"result": "success"}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Backend API call: HTTP error",
            exc_info=True,
            extra={
                "component": "tool",
                "tool": "restaurant_table_cancel",
                "status_code": e.response.status_code,
                "url": url,
                "reservation_id": reservation_id
            }
        )
        raise


# Tool registry for restaurant-related tools
RESTAURANT_TOOLS = {
    "restaurant_menu": {
        "declaration": RESTAURANT_MENU_DECLARATION,
        "execute": execute_restaurant_menu
    },
    "restaurant_table_list": {
        "declaration": RESTAURANT_TABLE_LIST_DECLARATION,
        "execute": execute_restaurant_table_list
    },
    "restaurant_table_get": {
        "declaration": RESTAURANT_TABLE_GET_DECLARATION,
        "execute": execute_restaurant_table_get
    },
    "restaurant_table_create": {
        "declaration": RESTAURANT_TABLE_CREATE_DECLARATION,
        "execute": execute_restaurant_table_create
    },
    "restaurant_table_cancel": {
        "declaration": RESTAURANT_TABLE_CANCEL_DECLARATION,
        "execute": execute_restaurant_table_cancel
    }
}