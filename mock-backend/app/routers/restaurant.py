"""
Restaurant router - 6 endpoints for menu and table reservations.
"""

import json
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from app.models import (
    RestaurantMenuItem,
    RestaurantTableReservation,
    RestaurantTableCreateRequest,
    RestaurantTableUpdateRequest
)
from app.utils.errors import error_response
from app.utils.ids import restaurant_table_id_gen


router = APIRouter(prefix="/api/v1/restaurant", tags=["restaurant"])

# Load menu fixtures at startup
MENU_FILE = Path(__file__).parent.parent / "data" / "menu.json"
with open(MENU_FILE, "r") as f:
    MENU_DATA: List[RestaurantMenuItem] = [
        RestaurantMenuItem(**item) for item in json.load(f)
    ]

# In-memory storage for table reservations (dict[id, RestaurantTableReservation])
TABLE_RESERVATIONS_STORE: Dict[int, RestaurantTableReservation] = {}


# ============================================================================
# MENU ENDPOINTS
# ============================================================================

@router.get("/menu", response_model=List[RestaurantMenuItem])
async def get_menu():
    """
    GET /api/v1/restaurant/menu - Menu restauracji.

    Returns:
        Lista pozycji menu z fixtures
    """
    return MENU_DATA


# ============================================================================
# TABLE RESERVATIONS ENDPOINTS
# ============================================================================

@router.get("/reservations", response_model=List[RestaurantTableReservation])
async def list_table_reservations():
    """
    GET /api/v1/restaurant/reservations - Lista rezerwacji stolików.

    Returns:
        Lista wszystkich rezerwacji stolików z in-memory store
    """
    return list(TABLE_RESERVATIONS_STORE.values())


@router.get("/reservations/{id}", response_model=RestaurantTableReservation)
async def get_table_reservation(id: int):
    """
    GET /api/v1/restaurant/reservations/{id} - Szczegóły rezerwacji stolika.

    Args:
        id: Table reservation ID

    Returns:
        RestaurantTableReservation object lub 404 error envelope
    """
    if id in TABLE_RESERVATIONS_STORE:
        return TABLE_RESERVATIONS_STORE[id]

    return error_response(
        code="TABLE_RESERVATION_NOT_FOUND",
        message="Table reservation not found",
        status=404
    )


@router.post(
    "/reservations",
    response_model=RestaurantTableReservation,
    status_code=status.HTTP_201_CREATED
)
async def create_table_reservation(req: RestaurantTableCreateRequest):
    """
    POST /api/v1/restaurant/reservations - Rezerwuj stolik.

    Args:
        req: Table reservation creation data

    Returns:
        Created RestaurantTableReservation z auto-generowanym ID i status="CONFIRMED"
    """
    # Generate new ID
    new_id = restaurant_table_id_gen.next()

    # Create table reservation with defaults
    table_reservation = RestaurantTableReservation(
        id=new_id,
        date=req.date,
        time=req.time,
        guests=req.guests,
        status="CONFIRMED"  # Default status zgodnie z dokumentacją
    )

    # Store in memory
    TABLE_RESERVATIONS_STORE[new_id] = table_reservation

    return table_reservation


@router.put("/reservations/{id}", response_model=RestaurantTableReservation)
async def update_table_reservation(id: int, req: RestaurantTableUpdateRequest):
    """
    PUT /api/v1/restaurant/reservations/{id} - Aktualizuj rezerwację stolika.

    Args:
        id: Table reservation ID to update
        req: Partial update data

    Returns:
        Updated RestaurantTableReservation lub 404 error envelope
    """
    if id not in TABLE_RESERVATIONS_STORE:
        return error_response(
            code="TABLE_RESERVATION_NOT_FOUND",
            message="Table reservation not found",
            status=404
        )

    # Get existing reservation
    table_reservation = TABLE_RESERVATIONS_STORE[id]

    # Update fields (only if provided in request)
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(table_reservation, field, value)

    TABLE_RESERVATIONS_STORE[id] = table_reservation
    return table_reservation


@router.delete("/reservations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table_reservation(id: int):
    """
    DELETE /api/v1/restaurant/reservations/{id} - Anuluj rezerwację stolika.

    Args:
        id: Table reservation ID to cancel

    Returns:
        204 No Content if found, 404 envelope otherwise
    """
    if id in TABLE_RESERVATIONS_STORE:
        del TABLE_RESERVATIONS_STORE[id]
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return error_response(
        code="TABLE_RESERVATION_NOT_FOUND",
        message="Table reservation not found",
        status=404
    )
