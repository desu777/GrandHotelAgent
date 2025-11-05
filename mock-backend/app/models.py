"""
Pydantic models for GrandHotel Mock Backend.
STRICT_DOC=true - 1:1 zgodność z GrandHotelBackend.md
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorEnvelope(BaseModel):
    """Standard error response envelope."""
    code: str = Field(..., description="Error code constant (e.g. ROOM_NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    status: int = Field(..., description="HTTP status code")


# ============================================================================
# ROOM MODELS
# ============================================================================

class Room(BaseModel):
    """
    Room model - UWAGA: brak pola 'id' w response zgodnie z dokumentacją.
    Identyfikacja tylko przez URL parameter.
    """
    roomType: str = Field(..., description="Type of room (e.g. Deluxe Suite)")
    pricePerNight: float = Field(..., description="Price per night in currency units")
    capacity: int = Field(..., description="Maximum number of guests")
    amenities: List[str] = Field(..., description="List of room amenities")


class RoomsFilterRequest(BaseModel):
    """Request body for POST /api/v1/rooms/filter"""
    checkInDate: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkOutDate: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    numberOfAdults: int = Field(..., description="Number of adult guests")
    numberOfChildren: int = Field(..., description="Number of children")


# ============================================================================
# RESERVATION MODELS
# ============================================================================

class Reservation(BaseModel):
    """
    Reservation model - STRICT_DOC: id może być string lub int (niespójność w dokumentacji).
    """
    status: str = Field(..., description="Reservation status (PENDING, CONFIRMED, CANCELLED)")
    checkInDate: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkOutDate: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    numberOfAdults: int = Field(..., description="Number of adult guests")
    numberOfChildren: int = Field(..., description="Number of children")
    id: Union[str, int] = Field(..., description="Reservation ID (string or int)")
    roomId: int = Field(..., description="ID of reserved room")
    totalPrice: float = Field(..., description="Total price for the stay")


class ReservationCreateRequest(BaseModel):
    """Request body for POST /api/v1/reservations"""
    checkInDate: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkOutDate: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    numberOfAdults: int = Field(..., description="Number of adult guests")
    numberOfChildren: int = Field(..., description="Number of children")
    roomId: int = Field(..., description="ID of room to reserve")


class ReservationUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/reservations/{id} - all fields optional"""
    checkInDate: Optional[str] = Field(None, description="Check-in date (YYYY-MM-DD)")
    checkOutDate: Optional[str] = Field(None, description="Check-out date (YYYY-MM-DD)")
    numberOfAdults: Optional[int] = Field(None, description="Number of adult guests")
    numberOfChildren: Optional[int] = Field(None, description="Number of children")
    status: Optional[str] = Field(None, description="Reservation status")


# ============================================================================
# RESTAURANT MODELS
# ============================================================================

class RestaurantMenuItem(BaseModel):
    """Restaurant menu item"""
    id: int = Field(..., description="Menu item ID")
    name: str = Field(..., description="Dish name")
    description: str = Field(..., description="Dish description")
    price: float = Field(..., description="Price in currency units")


class RestaurantTableReservation(BaseModel):
    """Restaurant table reservation"""
    date: str = Field(..., description="Reservation date (YYYY-MM-DD)")
    time: str = Field(..., description="Reservation time (HH:MM)")
    guests: int = Field(..., description="Number of guests")
    status: str = Field(..., description="Reservation status (CONFIRMED, PENDING, CANCELLED)")
    id: int = Field(..., description="Table reservation ID")


class RestaurantTableCreateRequest(BaseModel):
    """Request body for POST /api/v1/restaurant/reservations"""
    date: str = Field(..., description="Reservation date (YYYY-MM-DD)")
    time: str = Field(..., description="Reservation time (HH:MM)")
    guests: int = Field(..., description="Number of guests")


class RestaurantTableUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/restaurant/reservations/{id} - all fields optional"""
    date: Optional[str] = Field(None, description="Reservation date (YYYY-MM-DD)")
    time: Optional[str] = Field(None, description="Reservation time (HH:MM)")
    guests: Optional[int] = Field(None, description="Number of guests")
    status: Optional[str] = Field(None, description="Reservation status")
