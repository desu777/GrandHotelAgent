# Mock Backend (Python 3) — GrandHotel API kompatybilny z dokumentacją

Cel: Minimalny serwis HTTP odtwarzający produkcyjne endpointy (ścieżki, metody, kody) oraz identyczne kształty payloadów jak w dokumentacji (`GrandHotelBackend.md`). Zero bazy danych — odpowiedzi deterministyczne (mock), z opcją lekkiego stanu w pamięci procesu.

## 1) Technologia i uruchamianie
- Język: Python 3.11+
- Framework: FastAPI + Uvicorn
- Walidacja: Pydantic v2 (modele request/response)
- CORS: włączony (domyślnie `*` na potrzeby lokalnych testów FC)
- Uruchamianie: `uvicorn app.main:app --reload --port 8081`

## 2) Tryby pracy (konfig przez env)
- `MODE=mock` (domyślny): zwraca odpowiedzi z fixture/deterministyczne mocki.
- `MODE=proxy` (opcjonalnie później): przekazuje żądania do prawdziwego backendu (`BACKEND_URL`) i ewentualnie normalizuje payload do kształtów z dokumentacji.
- `STRICT_DOC=true` (opcjonalnie): tryb „identyczny jak w dokumentach”, nawet jeśli dokument zawiera niespójność; domyślnie zwracamy spójny envelope błędów.

## 3) Struktura projektu
```
app/
  main.py               # tworzy FastAPI, rejestruje routery, CORS
  deps.py               # (opcjonalnie) wspólne zależności, konfig
  models.py             # Pydantic modele request/response
  data/
    rooms.json          # fixture przykładowych pokoi
    menu.json           # fixture menu restauracji
  routers/
    rooms.py            # /api/v1/rooms, /api/v1/rooms/{id}, /filter
    reservations.py     # /api/v1/reservations*, CRUD bez DB (in‑memory)
    restaurant.py       # /api/v1/restaurant/*
  utils/
    errors.py           # helper do envelope błędów
    ids.py              # prosty generator ID w pamięci
```

## 4) Kontrakty — modele zgodne z dokumentacją

Uwaga: Trzymamy się kształtów jak w `GrandHotelBackend.md`. W miejscach niejednoznacznych stosujemy typy luźniejsze (np. `float|int`).

```py
# app/models.py (szkic)
from typing import List, Optional
from pydantic import BaseModel, Field

class ErrorEnvelope(BaseModel):
    code: str
    message: str
    status: int

class Room(BaseModel):
    roomType: str
    pricePerNight: float
    capacity: int
    amenities: List[str]

class RoomsFilterRequest(BaseModel):
    checkInDate: str
    checkOutDate: str
    numberOfAdults: int
    numberOfChildren: int

class Reservation(BaseModel):
    status: str
    checkInDate: str
    checkOutDate: str
    numberOfAdults: int
    numberOfChildren: int
    id: str | int
    roomId: int
    totalPrice: float

class ReservationCreateRequest(BaseModel):
    checkInDate: str
    checkOutDate: str
    numberOfAdults: int
    numberOfChildren: int
    roomId: int

class ReservationUpdateRequest(BaseModel):
    checkInDate: Optional[str] = None
    checkOutDate: Optional[str] = None
    numberOfAdults: Optional[int] = None
    numberOfChildren: Optional[int] = None
    status: Optional[str] = None

class RestaurantMenuItem(BaseModel):
    id: int
    name: str
    description: str
    price: float

class RestaurantTableReservation(BaseModel):
    date: str
    time: str
    guests: int
    status: str
    id: int

class RestaurantTableCreateRequest(BaseModel):
    date: str
    time: str
    guests: int

class RestaurantTableUpdateRequest(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    guests: Optional[int] = None
    status: Optional[str] = None
```

## 5) Endpointy i zachowanie (identyczne ścieżki i kody)

Podstawowa zasada: zwracać kształty JSON zgodne z przykładami w `GrandHotelBackend.md`. Poniżej spec w skrócie (bez powtarzania pełnych przykładów):

- Rooms
  - `GET /api/v1/rooms` → 200: `List[Room]`
  - `GET /api/v1/rooms/{id}` → 200: `Room`; 404: `ErrorEnvelope(code=ROOM_NOT_FOUND, ...)`
  - `POST /api/v1/rooms` (admin) → 201: `Room`
  - `PUT /api/v1/rooms/{id}` (admin) → 200: `Room`
  - `DELETE /api/v1/rooms/{id}` (admin) → 204, brak body
  - `POST /api/v1/rooms/filter` → 200: `List[Room]`; w razie braku dopasowań — 200 z pustą listą (prościej niż 404/500); opcjonalnie `STRICT_DOC=true` może zwrócić envelope z dokumentu

- Reservations
  - `GET /api/v1/reservations` → 200: `List[Reservation]`
  - `GET /api/v1/reservations/{id}` → 200: `Reservation`; 404: `ErrorEnvelope(ROOM_NOT_FOUND, ...)` (jak w dok.)
  - `POST /api/v1/reservations` → 201: `Reservation`
  - `PUT /api/v1/reservations/{id}` → 200: `Reservation`
  - `DELETE /api/v1/reservations/{id}` → 204, brak body

- Restaurant
  - `GET /api/v1/restaurant/menu` → 200: `List[RestaurantMenuItem]`
  - `GET /api/v1/restaurant/reservations` → 200: `List[RestaurantTableReservation]`
  - `GET /api/v1/restaurant/reservations/{id}` → 200: `RestaurantTableReservation`; 404: envelope błędu; w `STRICT_DOC` można zwrócić „jak w dok.”
  - `POST /api/v1/restaurant/reservations` → 201: `RestaurantTableReservation`
  - `PUT /api/v1/restaurant/reservations/{id}` → 200: `RestaurantTableReservation`
  - `DELETE /api/v1/restaurant/reservations/{id}` → 204, brak body

Kody błędów: jeżeli nie określono inaczej — envelope:
```json
{ "code": "STRING_CONST", "message": "Opis", "status": 4xx/5xx }
```

## 6) Dane mockowe i logika minimalna

- Rooms (`data/rooms.json`): lista kilku pokoi (np. „Deluxe Suite”, „Standard Room”) dokładnie z polami: `roomType, pricePerNight, capacity, amenities`.
  - `GET /rooms` zwraca całą listę.
  - `GET /rooms/{id}` mapuje `id` na indeks lub słownik w pamięci (brak pola `id` w odpowiedzi, zgodnie z dokumentem).
  - `POST /rooms`/`PUT /rooms/{id}`: echo payloadu + prosta walidacja pól; brak trwałości (opcjonalnie zapis w pamięci procesu).
  - `DELETE /rooms/{id}`: zawsze 204, jeśli `id` w zakresie; poza zakresem → 404 envelope.
  - `POST /rooms/filter`: prosta filtracja po `capacity >= numberOfAdults + numberOfChildren` i stałej dostępności; brak kalkulacji ceny.

- Reservations: stan w pamięci procesu (słownik `{id: Reservation}`); generator ID w `utils/ids.py` (np. zaczynając od 205 jak w przykładzie).
  - `POST /reservations`: wylicza `totalPrice` jako `pricePerNight * nights` (z pierwszego pasującego pokoju `roomId`) lub stałą wartość z dokumentu w `STRICT_DOC`.
  - `GET/PUT/DELETE /reservations/{id}`: operacje na słowniku; 404 envelope, gdy brak.
  - `GET /reservations`: zwraca listę wszystkich (brak rozróżnienia roli admin/gość — to mock).

- Restaurant
  - Menu: `data/menu.json` z kilkoma pozycjami (dokładnie: `id, name, description, price`).
  - Rezerwacje stolików: w pamięci procesu, ID liczone od 12.
  - Tworzenie/aktualizacja: echo + minimalna walidacja formatu daty/godziny (`YYYY-MM-DD`, `HH:MM`).

## 7) Routery — szkic FastAPI

```py
# app/main.py (szkic)
from fastapi import FastAPI
from app.routers import rooms, reservations, restaurant
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GrandHotel Mock Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

app.include_router(rooms.router, prefix="/api/v1/rooms", tags=["rooms"])
app.include_router(reservations.router, prefix="/api/v1/reservations", tags=["reservations"])
app.include_router(restaurant.router, prefix="/api/v1/restaurant", tags=["restaurant"])
```

```py
# app/routers/rooms.py (szkic)
from fastapi import APIRouter, HTTPException
from app.models import Room, RoomsFilterRequest, ErrorEnvelope

router = APIRouter()

@router.get("")
def rooms_list() -> list[Room]:
    ...

@router.get("/{id}")
def rooms_get(id: int) -> Room:
    ...  # 404 -> ErrorEnvelope

@router.post("")
def rooms_create(room: Room) -> Room:
    ...

@router.put("/{id}")
def rooms_update(id: int, room: Room) -> Room:
    ...

@router.delete("/{id}", status_code=204)
def rooms_delete(id: int):
    return

@router.post("/filter")
def rooms_filter(body: RoomsFilterRequest) -> list[Room]:
    ...
```

Analogicznie `reservations.py`, `restaurant.py` wg sekcji 5.

## 8) Zgodność z Function Calling

- Endpointy i payloady dokładnie odpowiadają mapowaniu z README/README_pl (sekcja „Function Calling — tools → backend”).
- Dzięki FastAPI generuje się OpenAPI — można użyć do walidacji FC.
- Zalecenie: dodać testowe „traceId” z nagłówka do logów, ale nie jest wymagane przez mock.

## 9) Walidacja i testy ręczne

- Uruchom: `uvicorn app.main:app --reload --port 8081`
- `GET /api/v1/rooms` — lista pokoi
- `POST /api/v1/rooms/filter` z przykładem z dokumentu — lista dopasowanych
- `POST /api/v1/reservations` z przykładem — 201 i payload z dokumentu
- `GET /api/v1/restaurant/menu` — lista pozycji menu

Przykładowe curl (skrót):
```
curl -s http://localhost:8081/api/v1/rooms | jq
curl -s -X POST http://localhost:8081/api/v1/rooms/filter \
  -H 'Content-Type: application/json' \
  -d '{"checkInDate":"2025-10-15","checkOutDate":"2025-10-18","numberOfAdults":2,"numberOfChildren":1}' | jq
```

## 10) Kryteria akceptacji
- [ ] Wszystkie ścieżki, metody i kody statusów zgodne z `GrandHotelBackend.md`.
- [ ] Kształty odpowiedzi (klucze/typy) 1:1 z dokumentacją; wątpliwości rozstrzygane przez `STRICT_DOC`.
- [ ] Brak bazy danych — dane z fixture lub pamięci procesu.
- [ ] Deterministyczne wartości w odpowiedziach tak, by testy FC były powtarzalne.
- [ ] Błędy zwracane w envelope (`code/message/status`), chyba że `STRICT_DOC=true` wymusza inaczej.
- [ ] OpenAPI generuje się poprawnie; brak walidacyjnych 422 przy przykładowych payloadach z dokumentu.

## 11) Dalsze kroki (opcjonalnie)
- `MODE=proxy` do rzeczywistego backendu (forward + normalizacja payloadu do formatu dokumentu).
- Parametry „chaosu” (np. `X-Mock-Latency: 120`) do symulacji opóźnień i błędów.
- Seedowane dane per `sessionId` dla stabilności konwersacji agenta.

## 12) Konteneryzacja (Docker)

### 12.1 Pliki i struktura
- `Dockerfile` — obraz dla FastAPI/uvicorn.
- `docker-compose.yml` — lokalne uruchamianie i healthcheck.
- `.dockerignore` — ograniczenie kontekstu builda.
- `requirements.txt` — zależności aplikacji.
- `.env.example` — przykład konfiguracji środowiskowej.

### 12.2 Dockerfile (propozycja)
```
# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Nierootowy użytkownik
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app

# Zależności
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kod aplikacji
COPY app/ ./app/

EXPOSE 8081
USER appuser

ENV PORT=8081 MODE=mock STRICT_DOC=false

# Healthcheck sprawdza /health
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:${PORT}/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
```

Uwaga: W `app/main.py` dodaj prosty endpoint zdrowia:
```
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
```

### 12.3 docker-compose.yml (propozycja)
```
# docker-compose.yml
version: "3.9"
services:
  mock-backend:
    build: .
    image: grandhotel-mock:dev
    container_name: grandhotel-mock
    ports:
      - "8081:8081"
    environment:
      - PORT=8081
      - MODE=${MODE:-mock}
      - STRICT_DOC=${STRICT_DOC:-false}
      - BACKEND_URL=${BACKEND_URL:-http://backend:8080}
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8081/health || exit 1"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

### 12.4 .dockerignore (propozycja)
```
# .dockerignore
.git
.gitignore
.env
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
build/
dist/
*.egg-info/
**/.DS_Store
```

### 12.5 requirements.txt (propozycja)
Zależności zgodne z Pydantic v2 i FastAPI:
```
# requirements.txt
fastapi>=0.110,<1.0
pydantic>=2.4,<3.0
uvicorn[standard]>=0.27,<0.30
python-dotenv>=1.0,<2.0
```

### 12.6 .env.example (propozycja)
```
# .env.example
MODE=mock
STRICT_DOC=false
PORT=8081
# Dla trybu proxy (opcjonalnie):
BACKEND_URL=http://localhost:9000
```

### 12.7 Budowanie i uruchamianie
- Build obrazu: `docker build -t grandhotel-mock:dev .`
- Uruchomienie: `docker run --rm -p 8081:8081 --env-file .env grandhotel-mock:dev`
- Compose: `docker compose up --build`

Weryfikacja:
- `curl -s http://localhost:8081/health | jq`
- `curl -s http://localhost:8081/api/v1/rooms | jq`

### 12.8 Uwagi dot. bezpieczeństwa i produkcji
- Użytkownik nierootowy w kontenerze (`appuser`).
- Ogranicz CORS na produkcji do znanych originów.
- Rozważ pinning wersji w `requirements.txt` (w ramach CI) i skanowanie SCA.
- W produkcji zwiększ `--workers` i dodaj reverse proxy (np. Nginx) oraz obserwowalność (Prometheus/Grafana lub logs).
