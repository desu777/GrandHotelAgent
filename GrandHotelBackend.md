# Hotel API: Detailed Endpoint & Schema Reference

This document provides a comprehensive, detailed reference for all backend API endpoints, including exact request and response payload examples as provided in the documentation.

# 1. Rooms - Endpoints related to rooms management and availability

# GET: /api/v1/rooms/{id} - Get room details 

Params: id (integer $int32)

Response:

Code 200(Room details):
{
  "roomType": "Deluxe Suite",
  "pricePerNight": 220,
  "capacity": 3,
  "amenities": [
    "WiFi",
    "Air Conditioning",
    "Balcony",
    "TV"
  ]
}

Code 404(Room not found):
{
  "code": "ROOM_NOT_FOUND",
  "message": "Room not found",
  "status": 404
}

# PUT: /api/v1/rooms/{id} - Update room details(admin)

Params: id

Request body:
{
  "roomType": "Deluxe Suite",
  "pricePerNight": 220,
  "capacity": 3,
  "amenities": [
    "WiFi",
    "Air Conditioning",
    "Balcony",
    "TV"
  ]
}

Responses:

Code 200 (Room updated)

# DELETE /api/v1/rooms/{id} - Delete room (admin)

Params: id 

Response:

Code 204(Room deleted)

# GET /api/v1/rooms - Get all rooms (public or admin)

Params: no 

Response:

Code 200 (List of all rooms):
[
  {
    "roomType": "Deluxe Suite",
    "pricePerNight": 220,
    "capacity": 3,
    "amenities": [
      "WiFi",
      "Air Conditioning",
      "Balcony",
      "TV"
    ]
  }
]

# POST /api/v1/rooms - Add new room (admin)

Params: no

Request body: 
{
  "roomType": "Deluxe Suite",
  "pricePerNight": 220,
  "capacity": 3,
  "amenities": [
    "WiFi",
    "Air Conditioning",
    "Balcony",
    "TV"
  ]
}

Responses:

Code 201(Room created):
{
  "roomType": "Deluxe Suite",
  "pricePerNight": 220,
  "capacity": 3,
  "amenities": [
    "WiFi",
    "Air Conditioning",
    "Balcony",
    "TV"
  ]
}

# POST /api/v1/rooms/filter - Get available rooms based on filters 

Returns available list of rooms matching criteria

Params: no

Req body: 
{
  "checkInDate": "2025-10-15",
  "checkOutDate": "2025-10-18",
  "numberOfAdults": 2,
  "numberOfChildren": 1
}

Responses: 

Code 200(List of rooms matching filters):
[
  {
    "roomType": "Deluxe Suite",
    "pricePerNight": 220,
    "capacity": 3,
    "amenities": [
      "WiFi",
      "Air Conditioning",
      "Balcony",
      "TV"
    ]
  }
]

Code 500(Server Error):
{
  "code": "ROOM_NOT_FOUND",
  "message": "Room not found",
  "status": 404
}

# 2.Reservations Endpoints related to room reservations

# GET /api/v1/reservations/{id} - Get reservation details 

Params: id

Responses: 

Code 200(Reservation details):
{
  "status": "PENDING",
  "checkInDate": "2025-10-15",
  "checkOutDate": "2025-10-18",
  "numberOfAdults": 2,
  "numberOfChildren": 1,
  "id": "205",
  "roomId": 101,
  "totalPrice": 670.99
}

Code 404(Reservation not found):
{
  "code": "ROOM_NOT_FOUND",
  "message": "Room not found",
  "status": 404
}

# PUT /api/v1/reservations/{id} - Update reservation (dates, guests, status)

Params: id 

Req body: 
{
  "checkInDate": "2025-10-15",
  "checkOutDate": "2025-10-18",
  "numberOfAdults": 2,
  "numberOfChildren": 1,
  "status": "PENDING"
}

Responses:
Code 200(Reservation updated):
{
  "status": "PENDING",
  "checkInDate": "2025-10-15",
  "checkOutDate": "2025-10-18",
  "numberOfAdults": 2,
  "numberOfChildren": 1,
  "id": "205",
  "roomId": 101,
  "totalPrice": 670.99
}


# DELETE /api/v1/reservations/{id} - Cancel reservation 

Params: id 

Responses:

Code 204(Reservation canceled)

# GET /api/v1/reservations - Admin: returns all reservations - Guest: returns only own reservations 

Params: no

Responses:

Code 200(List of reservations):
[
  {
    "status": "PENDING",
    "checkInDate": "2025-10-15",
    "checkOutDate": "2025-10-18",
    "numberOfAdults": 2,
    "numberOfChildren": 1,
    "id": "205",
    "roomId": 101,
    "totalPrice": 670.99
  }
]

# POST /api/v1/reservations - Create a new reservation 

Params: no

Req body:
{
  "checkInDate": "2025-10-15",
  "checkOutDate": "2025-10-18",
  "numberOfAdults": 2,
  "numberOfChildren": 1,
  "roomId": 101
}

Responses:

Code 201(Reservation created):
{
  "status": "PENDING",
  "checkInDate": "2025-10-15",
  "checkOutDate": "2025-10-18",
  "numberOfAdults": 2,
  "numberOfChildren": 1,
  "id": "205",
  "roomId": 101,
  "totalPrice": 670.99
}


# 3. Reservations - Endpoints related to room reservations

## Restaurant - Endpoints related to restaurant menu, table reservations, and orders

# GET: /api/v1/restaurant/reservations/{id} - Get table reservation details

Parameters: id (integer)

Responses: 

Code 200(Table reservation details):
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4,
  "status": "CONFIRMED",
  "id": 12
}

Code 404(Table reservation not found):
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4,
  "status": "CONFIRMED",
  "id": 12
}

# PUT /api/v1/restaurant/reservations/{id} - Update restaurant table reservation (admin only)

Description: Allows admin to change date, time, guests, or status 

Request body: 
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4,
  "status": "CONFIRMED"
}

Responses: 

Code 200 (Table reservation updated):
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4,
  "status": "CONFIRMED"
}

Code 404(Table reservation not found):
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4,
  "status": "CONFIRMED"
}

# DELETE /api/v1/restaurant/reservations/{id} - Cancel restaurant table reservation 

Responses: 

Code(204):	
Table reservation canceled


# GET /api/v1/restaurant/reservations - Get restaurant table reservations 

Guest: returns only own table reservations - Admin: returns all reservations

No Parameters. 

Responses: 

Code 200(List of table reservations):
[
  {
    "date": "2025-10-15",
    "time": "19:30",
    "guests": 4,
    "status": "CONFIRMED",
    "id": 12
  }
]

# POST /api/v1/restaurant/reservations - Reserve a restaurant table 

No parameters.

Request body: 
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4
}

Responses:

Code 201 (Table reserved):
{
  "date": "2025-10-15",
  "time": "19:30",
  "guests": 4,
  "status": "CONFIRMED",
  "id": 12
}

# GET /api/v1/restaurant/menu - Get restaurant menu 

No parameters

Responses:

Code 200 (List of menu items):
[
  {
    "id": 12,
    "name": "Grilled Salmon",
    "description": "Fresh Atlantic salmon served with roasted vegetables and lemon sauce",
    "price": 24.99
  }
]