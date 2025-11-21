"""
Reservation-related tools for Gemini Function Calling.
"""
import httpx
from grandhotel_agent.config import BACKEND_URL
from grandhotel_agent.logging_config import get_logger

logger = get_logger(__name__)


# reservations_list declaration and executor
RESERVATIONS_LIST_DECLARATION = {
    "name": "reservations_list",
    "description": (
        "Get list of all reservations. Depending on the user's role (guest vs admin), "
        "backend will return either their own reservations or all reservations."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}


async def execute_reservations_list(args: dict, jwt: str | None = None) -> dict:
    """
    Execute reservations_list tool: GET /api/v1/reservations from backend.

    Args:
        args: Empty dict (no parameters for this tool)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing list of reservations

    Raises:
        httpx.HTTPStatusError: If backend returns error
    """
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/reservations"
    logger.debug(
        "Backend API call: reservations_list",
        extra={"component": "tool", "tool": "reservations_list", "url": url}
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
                    "tool": "reservations_list",
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
                "tool": "reservations_list",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# reservations_get declaration and executor
RESERVATIONS_GET_DECLARATION = {
    "name": "reservations_get",
    "description": (
        "Get detailed information about a specific reservation by its ID. "
        "Returns reservation status, dates, number of guests, room ID, and total price."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Reservation ID to retrieve details for"
            }
        },
        "required": ["id"]
    }
}


async def execute_reservations_get(args: dict, jwt: str | None = None) -> dict:
    """
    Execute reservations_get tool: GET /api/v1/reservations/{id} from backend.

    Args:
        args: Dict with key "id" (integer)
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing reservation details

    Raises:
        httpx.HTTPStatusError: If backend returns error (e.g., reservation not found)
    """
    reservation_id = args.get("id")
    headers = {}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/reservations/{reservation_id}"
    logger.debug(
        "Backend API call: reservations_get",
        extra={
            "component": "tool",
            "tool": "reservations_get",
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
                    "tool": "reservations_get",
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
                "tool": "reservations_get",
                "status_code": e.response.status_code,
                "url": url,
                "reservation_id": reservation_id
            }
        )
        raise


# reservations_create declaration and executor
RESERVATIONS_CREATE_DECLARATION = {
    "name": "reservations_create",
    "description": (
        "Create a new room reservation for a guest. Requires room ID, check-in/out dates, "
        "and number of guests. Returns created reservation with ID, status, and total price."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "roomId": {
                "type": "integer",
                "description": "ID of the room to reserve"
            },
            "checkInDate": {
                "type": "string",
                "description": "Check-in date in YYYY-MM-DD format"
            },
            "checkOutDate": {
                "type": "string",
                "description": "Check-out date in YYYY-MM-DD format"
            },
            "numberOfAdults": {
                "type": "integer",
                "description": "Number of adult guests"
            },
            "numberOfChildren": {
                "type": "integer",
                "description": "Number of children"
            }
        },
        "required": ["roomId", "checkInDate", "checkOutDate", "numberOfAdults", "numberOfChildren"]
    }
}


async def execute_reservations_create(args: dict, jwt: str | None = None) -> dict:
    """
    Execute reservations_create tool: POST /api/v1/reservations to backend.

    Args:
        args: Dict with keys: roomId, checkInDate, checkOutDate, numberOfAdults, numberOfChildren
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing created reservation details

    Raises:
        httpx.HTTPStatusError: If backend returns error (room unavailable, invalid dates, etc.)
    """
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    url = f"{BACKEND_URL}/api/v1/reservations"
    logger.debug(
        "Backend API call: reservations_create",
        extra={
            "component": "tool",
            "tool": "reservations_create",
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
                    "tool": "reservations_create",
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
                "tool": "reservations_create",
                "status_code": e.response.status_code,
                "url": url
            }
        )
        raise


# reservations_update declaration and executor
RESERVATIONS_UPDATE_DECLARATION = {
    "name": "reservations_update",
    "description": (
        "Update an existing reservation. Can modify check-in/out dates, number of guests, "
        "or reservation status. All fields except ID are optional (partial update)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Reservation ID to update"
            },
            "checkInDate": {
                "type": "string",
                "description": "New check-in date in YYYY-MM-DD format (optional)"
            },
            "checkOutDate": {
                "type": "string",
                "description": "New check-out date in YYYY-MM-DD format (optional)"
            },
            "numberOfAdults": {
                "type": "integer",
                "description": "New number of adult guests (optional)"
            },
            "numberOfChildren": {
                "type": "integer",
                "description": "New number of children (optional)"
            },
            "status": {
                "type": "string",
                "description": "New reservation status: PENDING, CONFIRMED, CANCELED (optional)"
            }
        },
        "required": ["id"]
    }
}


async def execute_reservations_update(args: dict, jwt: str | None = None) -> dict:
    """
    Execute reservations_update tool: PUT /api/v1/reservations/{id} to backend.

    Args:
        args: Dict with required key "id" and optional keys: checkInDate, checkOutDate,
              numberOfAdults, numberOfChildren, status
        jwt: Optional JWT token for authorization

    Returns:
        dict with "result" key containing updated reservation details

    Raises:
        httpx.HTTPStatusError: If backend returns error (not found, validation error, etc.)
    """
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    # Extract ID and prepare update body
    reservation_id = args.pop("id")
    url = f"{BACKEND_URL}/api/v1/reservations/{reservation_id}"

    logger.debug(
        "Backend API call: reservations_update",
        extra={
            "component": "tool",
            "tool": "reservations_update",
            "url": url,
            "reservation_id": reservation_id,
            "update_data": args
        }
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(url, headers=headers, json=args)  # args now contains only update fields
            response.raise_for_status()
            reservation = response.json()

            logger.debug(
                "Backend API call: success",
                extra={
                    "component": "tool",
                    "tool": "reservations_update",
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
                "tool": "reservations_update",
                "status_code": e.response.status_code,
                "url": url,
                "reservation_id": reservation_id
            }
        )
        raise
    finally:
        # Restore id to args in case of retry logic
        args["id"] = reservation_id


# reservations_cancel declaration and executor
RESERVATIONS_CANCEL_DECLARATION = {
    "name": "reservations_cancel",
    "description": (
        "Cancel an existing reservation by its ID. This permanently cancels the reservation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Reservation ID to cancel"
            }
        },
        "required": ["id"]
    }
}


async def execute_reservations_cancel(args: dict, jwt: str | None = None) -> dict:
    """
    Execute reservations_cancel tool: DELETE /api/v1/reservations/{id} to backend.

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

    url = f"{BACKEND_URL}/api/v1/reservations/{reservation_id}"
    logger.debug(
        "Backend API call: reservations_cancel",
        extra={
            "component": "tool",
            "tool": "reservations_cancel",
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
                    "tool": "reservations_cancel",
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
                "tool": "reservations_cancel",
                "status_code": e.response.status_code,
                "url": url,
                "reservation_id": reservation_id
            }
        )
        raise


# Tool registry for reservation-related tools
RESERVATIONS_TOOLS = {
    "reservations_list": {
        "declaration": RESERVATIONS_LIST_DECLARATION,
        "execute": execute_reservations_list
    },
    "reservations_get": {
        "declaration": RESERVATIONS_GET_DECLARATION,
        "execute": execute_reservations_get
    },
    "reservations_create": {
        "declaration": RESERVATIONS_CREATE_DECLARATION,
        "execute": execute_reservations_create
    },
    "reservations_update": {
        "declaration": RESERVATIONS_UPDATE_DECLARATION,
        "execute": execute_reservations_update
    },
    "reservations_cancel": {
        "declaration": RESERVATIONS_CANCEL_DECLARATION,
        "execute": execute_reservations_cancel
    }
}