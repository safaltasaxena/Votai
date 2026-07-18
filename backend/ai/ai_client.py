import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None

# Primary model — fast, reliable, good at structured JSON tasks
_PRIMARY_MODEL = "openai/gpt-4o-mini"
# Fallback model — free tier on OpenRouter
_FALLBACK_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

def get_openai_client() -> OpenAI:
    """Lazily initialize and return a singleton OpenAI client."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            logger.error("OPENROUTER_API_KEY is not set — AI calls will fail")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
    return _client

def generate_content(
    user_prompt: str,
    system_prompt: str = "",
    max_tokens: int = 800,
) -> str:
    """
    Generate content from the AI model using OpenRouter.

    Args:
        user_prompt: User prompt.
        system_prompt: System instructions (loaded from openai.md).
        max_tokens: Maximum response tokens.

    Returns:
        Generated response text.
    """

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": user_prompt,
        }
    )

    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model=_PRIMARY_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            timeout=15.0,
        )

        return response.choices[0].message.content

    except Exception as primary_err:

        logger.warning(
            "Primary AI model (%s) failed: %s — trying fallback model",
            _PRIMARY_MODEL,
            primary_err,
        )

        client = get_openai_client()

        response = client.chat.completions.create(
            model=_FALLBACK_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            timeout=20.0,
        )

        return response.choices[0].message.content