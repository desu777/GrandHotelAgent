"""
Language detection service using Gemini lite model.
Returns strict BCP-47 language code for a given text input.
"""
from google import genai
from google.genai import types
from grandhotel_agent.config import GOOGLE_API_KEY, GEMINI_MODEL_LANG


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
            print("[Lang] No valid response from language detection model")
            return "en-US"

        code = resp.candidates[0].content.parts[0].text.strip()

        # Basic BCP-47 validation
        if 2 <= len(code) <= 8 and " " not in code and "\n" not in code:
            return code

        print(f"[Lang] Invalid language code format: {code}")
        return "en-US"

    except Exception as e:
        print(f"[Lang] Language detection error: {e}")
        return "en-US"  # Safe fallback

