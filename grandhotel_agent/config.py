"""
Configuration from environment variables.
All secrets through ENV, no hardcoding.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_LANG = os.getenv("GEMINI_MODEL_LANG", "gemini-2.5-flash-lite")

# Backend API
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8081")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL_MIN = int(os.getenv("SESSION_TTL_MIN", "60"))
SESSION_MAX_MESSAGES = int(os.getenv("SESSION_MAX_MESSAGES", "30"))

# Rate limiting
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))

# Logging
APP_ENV = os.getenv("APP_ENV", "development")  # development / production
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if APP_ENV == "development" else "INFO")
