"""
GrandHotel Agent - FastAPI application.
Main entry point for the service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from grandhotel_agent.routers import agent
from grandhotel_agent.logging_config import setup_logging, get_logger

# Configure logging FIRST (before app creation)
setup_logging()
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title="GrandHotel Agent API",
    description="AI hotel concierge powered by Gemini 2.5 Flash with Function Calling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(agent.router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info(
        "GrandHotel Agent API starting",
        extra={
            "event": "startup",
            "version": "1.0.0",
            "endpoints": [
                "POST /agent/chat - Main chat endpoint",
                "GET /agent/health - Health check",
                "GET /docs - Swagger UI"
            ]
        }
    )


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from grandhotel_agent.services.redis_store import _store
    if _store:
        await _store.disconnect()
    logger.info("GrandHotel Agent API stopped", extra={"event": "shutdown"})


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "service": "GrandHotel Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }
