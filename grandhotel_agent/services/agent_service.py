"""
Main agent service with Gemini 2.5 Flash Function Calling loop.
Based on official Google AI docs: https://ai.google.dev/gemini-api/docs/function-calling
"""
import time
from pathlib import Path
from google import genai
from google.genai import types
from grandhotel_agent.config import GOOGLE_API_KEY, GEMINI_MODEL
from grandhotel_agent.tools.rooms import AVAILABLE_TOOLS
from grandhotel_agent.models.responses import ToolTrace


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
        user_message: str,
        jwt: str | None = None,
        language_code: str | None = None,
    ) -> tuple[str, list[ToolTrace]]:
        """
        Process user message with FC loop.

        Args:
            user_message: User's text input
            jwt: Optional JWT token for backend calls

        Returns:
            tuple: (final_reply, tool_traces)
        """
        tool_traces = []

        # Step 1: Setup tools
        tool_declarations = [
            tool_info["declaration"]
            for tool_info in AVAILABLE_TOOLS.values()
        ]

        tools = types.Tool(function_declarations=tool_declarations)
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
            system_instruction=f"{self.system_prompt}{runtime_lang_note}",
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"
                )
            )
        )

        # Build initial content (just user message, system is in config)
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
        ]

        # Step 2: Call model
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )

        # Step 3: Check for function_call in ALL parts (not just first)
        # Model may generate text before function_call
        func_call = None
        text_parts = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                func_call = part.function_call
                break  # Take first function_call found
            elif hasattr(part, 'text'):
                text_parts.append(part.text)

        if func_call:

            print(f"[FC] Tool called: {func_call.name} with args: {dict(func_call.args)}")

            # Step 4: Execute function
            start_time = time.time()

            try:
                tool_info = AVAILABLE_TOOLS.get(func_call.name)
                if not tool_info:
                    raise ValueError(f"Unknown tool: {func_call.name}")

                result = await tool_info["execute"](dict(func_call.args), jwt)
                status = "OK"

            except Exception as e:
                print(f"[FC] Error executing {func_call.name}: {e}")
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
            contents.append(response.candidates[0].content)

            func_response = types.Part.from_function_response(
                name=func_call.name,
                response=result
            )
            contents.append(types.Content(role="user", parts=[func_response]))

            # Get final response
            final_response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )

            final_text = final_response.candidates[0].content.parts[0].text
            return final_text, tool_traces

        # No function call - direct response
        # Join all text parts collected during iteration with space
        final_text = ' '.join(text_parts) if text_parts else ""
        return final_text, tool_traces
