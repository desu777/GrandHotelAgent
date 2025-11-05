"""
GrandHotel Mock Backend - FastAPI Application
Production-ready mockowy backend zgodny 1:1 z GrandHotelBackend.md
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import rooms, reservations, restaurant
from app.deps import config


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="GrandHotel Mock Backend",
    description="Mock API server dla testowania GrandHotel AI Agent (Gemini Function Calling)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev mode - allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """
    GET /health - Sprawdzenie stanu serwera.

    Returns:
        Status object z informacją o konfiguracji
    """
    return {
        "status": "ok",
        "mode": config.MODE,
        "strict_doc": config.STRICT_DOC
    }


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(rooms.router)
app.include_router(reservations.router)
app.include_router(restaurant.router)


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print("=" * 60)
    print("GrandHotel Mock Backend - Starting")
    print("=" * 60)
    print(f"Mode: {config.MODE}")
    print(f"STRICT_DOC: {config.STRICT_DOC}")
    print(f"Port: {config.PORT}")
    print(f"Docs: http://localhost:{config.PORT}/docs")
    print("=" * 60)
