"""
Language detection service using Gemini lite model.
Returns strict BCP-47 language code for a given text input.
"""
from google import genai
from google.genai import types
from grandhotel_agent.config import GOOGLE_API_KEY, GEMINI_MODEL_LANG
from grandhotel_agent.logging_config import get_logger

logger = get_logger(__name__)


async def detect_language_bcp47(text: str | None) -> str:
    """Detect language code in BCP-47 using a lightweight Gemini model.

    For empty/None input, return a safe default "en-US".
    """
    if not text or not text.strip():
        return "en-US"

    client = genai.Client(api_key=GOOGLE_API_KEY)

    # system_instruction should be a string, not types.Part
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are a strict language detector. "
            "Return ONLY the primary BCP-47 language code of the provided text. "
            "Examples: 'en-US', 'pl-PL', 'de-DE'. Do not add explanations."
        )
    )

    contents = [types.Content(role="user", parts=[types.Part(text=text)])]

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL_LANG,
            contents=contents,
            config=config
        )

        # Safe access to response with error handling
        if not resp.candidates or not resp.candidates[0].content.parts:
            logger.warning(
                "Language detection: no valid response from model",
                extra={"component": "lang", "fallback": "en-US"}
            )
            return "en-US"

        code = resp.candidates[0].content.parts[0].text.strip()

        # Basic BCP-47 validation
        if 2 <= len(code) <= 8 and " " not in code and "\n" not in code:
            return code

        logger.warning(
            "Language detection: invalid code format",
            extra={"component": "lang", "code": code, "fallback": "en-US"}
        )
        return "en-US"

    except Exception as e:
        logger.error(
            "Language detection error",
            exc_info=True,
            extra={"component": "lang", "fallback": "en-US"}
        )
        return "en-US"  # Safe fallback

