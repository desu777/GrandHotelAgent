"""
Dependencies and configuration for the mock backend.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # Server configuration
    PORT: int = int(os.getenv("PORT", "8081"))

    # Mock mode configuration
    MODE: str = os.getenv("MODE", "mock")  # "mock" or "proxy"
    STRICT_DOC: bool = os.getenv("STRICT_DOC", "false").lower() == "true"

    # Backend URL for proxy mode (future use)
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:9000")


# Global config instance
config = Config()
