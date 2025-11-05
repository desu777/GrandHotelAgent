"""
Rooms router - 6 endpoints for room management.
"""

import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from app.models import Room, RoomsFilterRequest
from app.utils.errors import error_response


router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])

# Load room fixtures at startup
ROOMS_FILE = Path(__file__).parent.parent / "data" / "rooms.json"
with open(ROOMS_FILE, "r") as f:
    ROOMS_DATA: List[Room] = [Room(**room) for room in json.load(f)]


@router.get("", response_model=List[Room])
async def list_rooms():
    """
    GET /api/v1/rooms - Lista wszystkich pokoi.

    Returns:
        Lista pokoi z fixtures
    """
    return ROOMS_DATA


@router.get("/{id}", response_model=Room)
async def get_room(id: int):
    """
    GET /api/v1/rooms/{id} - Szczegóły pokoju.

    Args:
        id: Room ID (1-indexed)

    Returns:
        Room object lub 404 error envelope
    """
    # ID is 1-indexed in API, 0-indexed in list
    if 1 <= id <= len(ROOMS_DATA):
        return ROOMS_DATA[id - 1]

    return error_response(
        code="ROOM_NOT_FOUND",
        message="Room not found",
        status=404
    )


@router.post("", response_model=Room, status_code=status.HTTP_201_CREATED)
async def create_room(room: Room):
    """
    POST /api/v1/rooms - Dodaj pokój (admin endpoint).

    Args:
        room: Room data to create

    Returns:
        Echo of created room (no persistence in mock)
    """
    return room


@router.put("/{id}", response_model=Room)
async def update_room(id: int, room: Room):
    """
    PUT /api/v1/rooms/{id} - Aktualizuj pokój (admin endpoint).

    Args:
        id: Room ID to update
        room: Updated room data

    Returns:
        Echo of updated room (no persistence in mock)
    """
    # Mock: simply echo back the payload
    return room


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(id: int):
    """
    DELETE /api/v1/rooms/{id} - Usuń pokój (admin endpoint).

    Args:
        id: Room ID to delete

    Returns:
        204 No Content if ID in valid range, 404 envelope otherwise
    """
    if 1 <= id <= len(ROOMS_DATA):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return error_response(
        code="ROOM_NOT_FOUND",
        message="Room not found",
        status=404
    )


@router.post("/filter", response_model=List[Room])
async def filter_rooms(filter_req: RoomsFilterRequest):
    """
    POST /api/v1/rooms/filter - Filtruj dostępne pokoje.

    Args:
        filter_req: Filter criteria (dates, guests)

    Returns:
        Lista pokoi spełniających kryteria (capacity >= total guests)
    """
    # Mock logic: filter by capacity only (ignore dates for simplicity)
    total_guests = filter_req.numberOfAdults + filter_req.numberOfChildren

    filtered_rooms = [
        room for room in ROOMS_DATA
        if room.capacity >= total_guests
    ]

    return filtered_rooms
