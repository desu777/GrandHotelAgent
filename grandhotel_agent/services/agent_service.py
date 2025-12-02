"""
Main agent service with Gemini 2.5 Flash Function Calling loop.
Based on official Google AI docs: https://ai.google.dev/gemini-api/docs/function-calling
"""
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from google import genai
from google.genai import types
from grandhotel_agent.config import GOOGLE_API_KEY, GEMINI_MODEL, APP_ENV
from grandhotel_agent.tools import AVAILABLE_TOOLS
from grandhotel_agent.models.responses import ToolTrace
from grandhotel_agent.logging_config import get_logger

logger = get_logger(__name__)

# Retry configuration for transient empty responses (known Gemini 2.5 bug)
MAX_RETRIES = 3
RETRY_DELAY_BASE = 0.5  # seconds


def _extract_response_content(
    response: Any,
) -> tuple[types.FunctionCall | None, list[str], str | None]:
    """
    Safely extract function_call and text parts from Gemini response.

    Handles known issues:
    - Empty candidates (transient API bug)
    - Safety blocks (finish_reason=SAFETY)
    - Prompt blocks (promptFeedback.blockReason)
    - Empty content/parts (transient API bug)

    Returns:
        tuple: (function_call, text_parts, error_message)
        - function_call: FunctionCall object or None
        - text_parts: list of text strings from parts
        - error_message: user-friendly error if response is invalid, else None
    """
    # Check candidates exist
    if not response.candidates:
        # Check prompt feedback for block reason
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            block_reason = getattr(response.prompt_feedback, 'block_reason', None)
            if block_reason:
                logger.warning("Prompt blocked", extra={"block_reason": str(block_reason)})
                return None, [], "Przepraszam, nie mogę odpowiedzieć na to pytanie."
        logger.warning("Empty candidates in response")
        return None, [], None  # Transient error - can retry

    candidate = response.candidates[0]

    # Check finish_reason for safety block
    finish_reason = getattr(candidate, 'finish_reason', None)
    if finish_reason and str(finish_reason) == "SAFETY":
        logger.warning("Response blocked by safety filter", extra={
            "safety_ratings": str(getattr(candidate, 'safety_ratings', []))
        })
        return None, [], "Przepraszam, nie mogę odpowiedzieć na to pytanie."

    # Check content exists
    if not candidate.content:
        logger.warning("Empty content in candidate", extra={"finish_reason": str(finish_reason)})
        return None, [], None  # Transient - can retry

    # Check parts exist
    if not candidate.content.parts:
        logger.warning("Empty parts in content", extra={"finish_reason": str(finish_reason)})
        return None, [], None  # Transient - can retry

    # Extract function_call and text parts
    func_call = None
    text_parts = []

    for part in candidate.content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            func_call = part.function_call
            break  # Function call takes precedence
        elif hasattr(part, 'text') and part.text:
            text_parts.append(part.text)

    return func_call, text_parts, None


async def _generate_with_retry(
    client: genai.Client,
    model: str,
    contents: list,
    config: types.GenerateContentConfig,
    max_retries: int = MAX_RETRIES
) -> tuple[Any, types.FunctionCall | None, list[str], str | None]:
    """
    Call Gemini API with retry logic for transient empty responses.

    Known issue: Gemini 2.5 sometimes returns empty Content without parts
    despite finish_reason=STOP. Retry with exponential backoff helps.

    Returns:
        tuple: (raw_response, function_call, text_parts, error_message)
    """
    for attempt in range(max_retries):
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        func_call, text_parts, error_msg = _extract_response_content(response)

        # If we got content or a definitive error (safety block), return
        if func_call or text_parts or error_msg:
            return response, func_call, text_parts, error_msg

        # Transient empty response - retry with exponential backoff
        if attempt < max_retries - 1:
            delay = RETRY_DELAY_BASE * (2 ** attempt)
            logger.warning(
                f"Empty response from Gemini, retrying in {delay}s",
                extra={"attempt": attempt + 1, "max_retries": max_retries}
            )
            await asyncio.sleep(delay)

    # All retries failed
    logger.error("All retries failed - empty response from Gemini")
    return response, None, [], "Przepraszam, wystąpił problem z połączeniem. Spróbuj ponownie."


class AgentService:
    """
    Gemini agent with Function Calling support.

    Implements full FC loop:
    1. Call model with tools
    2. Check for function_call
    3. Execute function
    4. Send function_response back
    5. Get final text response
    """

    def __init__(self):
        """Initialize Gemini client"""
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.model = GEMINI_MODEL

        # Load system prompt
        prompt_path = Path(__file__).parent.parent / "prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

    async def chat(
        self,
        user_message: str | None,
        jwt: str | None = None,
        language_code: str | None = None,
        history: list[dict] | None = None,
        audio_bytes: bytes | None = None,
        audio_mime_type: str | None = None,
    ) -> tuple[str, list[ToolTrace], str | None]:
        """
        Process user message with FC loop. Supports text and/or audio input.

        Args:
            user_message: User's text input (optional if audio provided)
            jwt: Optional JWT token for backend calls
            language_code: BCP-47 language code for response
            history: Optional conversation history as list of dicts with keys:
                     - "role": "user" | "assistant"
                     - "content": str
                     - "ts": str (ISO8601, optional)
            audio_bytes: Raw audio data (WebM/Opus, WAV, MP3)
            audio_mime_type: MIME type of audio (e.g. "audio/webm")

        Returns:
            tuple: (final_reply, tool_traces, transcription)
            - transcription: extracted text from audio input (if audio was provided)
        """
        tool_traces = []

        # Step 1: Setup tools
        tool_declarations = [
            tool_info["declaration"]
            for tool_info in AVAILABLE_TOOLS.values()
        ]

        tools = types.Tool(function_declarations=tool_declarations)

        # Runtime datetime context for time-aware responses
        now_utc = datetime.now(timezone.utc)
        runtime_datetime_note = (
            f"\n\n[Runtime Context]\n"
            f"CURRENT_DATETIME_UTC = {now_utc.isoformat()}\n"
            f"Today's date (UTC): {now_utc.strftime('%Y-%m-%d')}\n"
        )

        # Combine static system prompt with runtime language directive
        runtime_lang_note = ""
        if language_code:
            runtime_lang_note = (
                f"\n\n[Runtime Instruction]\nLANG = {language_code}\n"
                f"Odpowiadaj wyłącznie w LANG. Nie mieszaj języków.\n"
            )

        # Configure generation with tools and proper system instruction
        # system_instruction should be a string, not types.Part
        config = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=f"{self.system_prompt}{runtime_datetime_note}{runtime_lang_note}",
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"
                )
            )
        )

        # Build contents list starting with conversation history
        contents: list[types.Content] = []

        # Add conversation history if available
        if history:
            for msg in history:
                # Validate message structure
                if not isinstance(msg, dict) or "content" not in msg or "role" not in msg:
                    continue  # Skip invalid entries

                role = msg["role"]
                content_text = msg["content"]

                # Map 'assistant' to 'model' for Gemini API
                if role == "assistant":
                    role = "model"
                elif role != "user":
                    continue  # Skip unknown roles

                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=content_text)]
                    )
                )

        # Add current user input (text and/or audio)
        user_parts: list[types.Part] = []

        # Audio input (multimodal)
        if audio_bytes and audio_mime_type:
            logger.debug(
                "Adding audio input to request",
                extra={
                    "component": "agent",
                    "audio_size_bytes": len(audio_bytes),
                    "mime_type": audio_mime_type,
                }
            )
            audio_part = types.Part.from_bytes(
                mime_type=audio_mime_type,
                data=audio_bytes,
            )
            user_parts.append(audio_part)

        # Text input (or hint alongside audio)
        if user_message:
            user_parts.append(types.Part(text=user_message))

        if user_parts:
            contents.append(
                types.Content(
                    role="user",
                    parts=user_parts,
                )
            )

        # Step 2: Call model with retry logic for transient empty responses
        response, func_call, text_parts, error_msg = await _generate_with_retry(
            self.client, self.model, contents, config
        )

        # Track transcription from audio input
        transcription: str | None = None

        # Handle definitive errors (safety block, prompt block)
        if error_msg and not func_call and not text_parts:
            return error_msg, tool_traces, transcription

        # Step 3: Handle function call if present
        if func_call:
            # Log tool invocation (args only in dev mode to avoid sensitive data exposure)
            extra_log = {
                "component": "fc",
                "tool": func_call.name
            }
            if APP_ENV == "development":
                extra_log["tool_args"] = dict(func_call.args)

            logger.info("Function calling: tool invoked", extra=extra_log)

            # Step 4: Execute function
            start_time = time.time()

            try:
                tool_info = AVAILABLE_TOOLS.get(func_call.name)
                if not tool_info:
                    raise ValueError(f"Unknown tool: {func_call.name}")

                result = await tool_info["execute"](dict(func_call.args), jwt)
                status = "OK"

            except Exception as e:
                logger.error(
                    "Function calling: tool execution failed",
                    exc_info=True,
                    extra={"component": "fc", "tool": func_call.name}
                )
                result = {"error": str(e)}
                status = "ERROR"

            duration_ms = int((time.time() - start_time) * 1000)

            # Record trace
            tool_traces.append(ToolTrace(
                name=func_call.name,
                status=status,
                durationMs=duration_ms
            ))

            # Step 5: Send function_response back to model
            # Note: response.candidates[0].content is guaranteed to exist here
            # because _generate_with_retry validates it before returning func_call
            contents.append(response.candidates[0].content)

            func_response = types.Part.from_function_response(
                name=func_call.name,
                response=result
            )
            contents.append(types.Content(role="user", parts=[func_response]))

            # Get final response with retry logic
            final_response, _, final_text_parts, final_error = await _generate_with_retry(
                self.client, self.model, contents, config
            )

            if final_error:
                return final_error, tool_traces, transcription

            final_text = ' '.join(final_text_parts) if final_text_parts else "Przepraszam, nie udało się przetworzyć odpowiedzi."

            # Extract transcription for audio input (from first response text)
            if audio_bytes and text_parts:
                # When audio is provided, model often includes transcription in initial response
                # We save it for history persistence
                transcription = ' '.join(text_parts)

            return final_text, tool_traces, transcription

        # No function call - direct response
        final_text = ' '.join(text_parts) if text_parts else "Przepraszam, nie udało się uzyskać odpowiedzi."

        # For audio-only input without FC, the text response often includes transcription
        if audio_bytes and not user_message and text_parts:
            transcription = final_text

        return final_text, tool_traces, transcription
