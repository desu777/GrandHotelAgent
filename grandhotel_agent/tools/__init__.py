"""Function Calling tools for Gemini"""
from .rooms import ROOMS_TOOLS
from .reservations import RESERVATIONS_TOOLS
from .restaurant import RESTAURANT_TOOLS

# Central registry for agent_service.py
AVAILABLE_TOOLS = {
    **ROOMS_TOOLS,
    **RESERVATIONS_TOOLS,
    **RESTAURANT_TOOLS
}
