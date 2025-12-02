"""
Text-to-Speech service using ElevenLabs API.
"""
from grandhotel_agent.config import (
    ELEVEN_LABS_API_KEY,
    ELEVEN_LABS_MODEL_ID,
    ELEVEN_LABS_VOICE_ID,
)
from grandhotel_agent.logging_config import get_logger

logger = get_logger(__name__)

# Lazy-initialized client
_client = None


class TTSError(Exception):
    """TTS synthesis failed"""
    pass


class TTSUnavailableError(TTSError):
    """TTS service not configured (missing API key)"""
    pass


def _get_client():
    """Lazy init ElevenLabs client"""
    global _client
    if _client is None:
        if not ELEVEN_LABS_API_KEY:
            raise TTSUnavailableError("ELEVEN_LABS_API_KEY not configured")
        from elevenlabs.client import ElevenLabs
        _client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)
    return _client


async def synthesize_speech(
    text: str,
    model_id: str | None = None,
    voice_id: str | None = None,
) -> bytes:
    """
    Convert text to MP3 audio using ElevenLabs API.

    Args:
        text: Text to synthesize
        model_id: ElevenLabs model ID (default from config)
        voice_id: ElevenLabs voice ID (default from config)

    Returns:
        bytes: MP3 audio data (audio/mpeg, mp3_44100_128)

    Raises:
        TTSUnavailableError: API key not configured
        TTSError: Synthesis failed
    """
    if not text or not text.strip():
        raise TTSError("Empty text provided for TTS")

    model = model_id or ELEVEN_LABS_MODEL_ID
    voice = voice_id or ELEVEN_LABS_VOICE_ID

    logger.debug(
        "TTS synthesis starting",
        extra={
            "component": "tts",
            "model": model,
            "voice": voice,
            "text_length": len(text),
        }
    )

    try:
        client = _get_client()

        def _convert() -> bytes:
            """Synchronous TTS call - run in thread pool."""
            result = client.text_to_speech.convert(
                text=text,
                voice_id=voice,
                model_id=model,
                output_format="mp3_44100_128",
            )
            # SDK może zwrócić bytes lub generator chunków
            if isinstance(result, (bytes, bytearray)):
                return bytes(result)
            # Generator - złącz chunki (tylko bytes)
            return b"".join(
                chunk for chunk in result
                if isinstance(chunk, (bytes, bytearray))
            )

        # Run sync SDK call in thread pool to avoid blocking event loop
        import asyncio
        audio_bytes = await asyncio.to_thread(_convert)

        logger.info(
            "TTS synthesis completed",
            extra={
                "component": "tts",
                "audio_size_bytes": len(audio_bytes),
            }
        )

        return audio_bytes

    except TTSUnavailableError:
        raise
    except Exception as e:
        logger.error(
            "TTS synthesis failed",
            exc_info=True,
            extra={"component": "tts"}
        )
        raise TTSError(f"TTS synthesis failed: {e}") from e
