"""
LLM provider wrapper for Groq API interactions
"""
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from app.config import settings

try:
    from groq import Groq
except Exception:
    Groq = None


class GroqProvider:
    """Wrapper for Groq API interactions"""

    def __init__(self):
        """Initialize Groq client"""
        self.client = None
        if settings.GROQ_API_KEY and Groq:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[GROQ INIT] Failed to initialize Groq client: {e}")

    async def call_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 900,
        require_json: bool = False,
    ) -> str:
        """
        Run Groq chat completion asynchronously via thread pool.
        
        Args:
            system_prompt: System context for the model
            user_prompt: User query/instruction
            temperature: Sampling temperature (0-1)
            max_tokens: Max response tokens
            require_json: Enforce JSON mode output
            
        Returns:
            Model response text
        """
        if not self.client:
            return ""

        def _run_completion() -> str:
            request_payload = {
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if require_json:
                request_payload["response_format"] = {"type": "json_object"}

            try:
                response = self.client.chat.completions.create(**request_payload)
            except Exception as e:
                # Graceful fallback if endpoint doesn't support JSON mode
                if "response_format" in str(e) and require_json:
                    del request_payload["response_format"]
                    response = self.client.chat.completions.create(**request_payload)
                else:
                    raise

            return response.choices[0].message.content or ""

        # Run in thread pool executor to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(executor, _run_completion)
        return result


# Singleton instance
groq_provider = GroqProvider()
