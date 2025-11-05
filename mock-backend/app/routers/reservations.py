"""
Reservations router - 5 endpoints for room reservations.
"""

from typing import Dict, List

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from app.models import Reservation, ReservationCreateRequest, ReservationUpdateRequest
from app.utils.errors import error_response
from app.utils.ids import reservation_id_gen


router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])

# In-memory storage for reservations (dict[id, Reservation])
RESERVATIONS_STORE: Dict[int, Reservation] = {}


@router.get("", response_model=List[Reservation])
async def list_reservations():
    """
    GET /api/v1/reservations - Lista wszystkich rezerwacji.

    Note: Mock nie rozróżnia admin vs guest - zwraca wszystkie.

    Returns:
        Lista wszystkich rezerwacji z in-memory store
    """
    return list(RESERVATIONS_STORE.values())


@router.get("/{id}", response_model=Reservation)
async def get_reservation(id: int):
    """
    GET /api/v1/reservations/{id} - Szczegóły rezerwacji.

    Args:
        id: Reservation ID

    Returns:
        Reservation object lub 404 error envelope
    """
    if id in RESERVATIONS_STORE:
        return RESERVATIONS_STORE[id]

    return error_response(
        code="RESERVATION_NOT_FOUND",
        message="Reservation not found",
        status=404
    )


@router.post("", response_model=Reservation, status_code=status.HTTP_201_CREATED)
async def create_reservation(req: ReservationCreateRequest):
    """
    POST /api/v1/reservations - Utwórz rezerwację.

    Args:
        req: Reservation creation data

    Returns:
        Created Reservation z auto-generowanym ID, status, totalPrice (deterministyczna stała)
    """
    # Generate new ID (STRICT_DOC: może być str lub int, używamy str jak w przykładzie)
    new_id = str(reservation_id_gen.next())

    # Create reservation with defaults
    reservation = Reservation(
        id=new_id,
        status="PENDING",
        checkInDate=req.checkInDate,
        checkOutDate=req.checkOutDate,
        numberOfAdults=req.numberOfAdults,
        numberOfChildren=req.numberOfChildren,
        roomId=req.roomId,
        totalPrice=670.99  # Deterministyczna stała zgodnie z planem
    )

    # Store in memory (use int key for storage)
    RESERVATIONS_STORE[int(new_id)] = reservation

    return reservation


@router.put("/{id}", response_model=Reservation)
async def update_reservation(id: int, req: ReservationUpdateRequest):
    """
    PUT /api/v1/reservations/{id} - Aktualizuj rezerwację.

    Args:
        id: Reservation ID to update
        req: Partial update data

    Returns:
        Updated Reservation lub 404 error envelope
    """
    if id not in RESERVATIONS_STORE:
        return error_response(
            code="RESERVATION_NOT_FOUND",
            message="Reservation not found",
            status=404
        )

    # Get existing reservation
    reservation = RESERVATIONS_STORE[id]

    # Update fields (only if provided in request)
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)

    RESERVATIONS_STORE[id] = reservation
    return reservation


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(id: int):
    """
    DELETE /api/v1/reservations/{id} - Anuluj rezerwację.

    Args:
        id: Reservation ID to cancel

    Returns:
        204 No Content if found, 404 envelope otherwise
    """
    if id in RESERVATIONS_STORE:
        del RESERVATIONS_STORE[id]
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return error_response(
        code="RESERVATION_NOT_FOUND",
        message="Reservation not found",
        status=404
    )
