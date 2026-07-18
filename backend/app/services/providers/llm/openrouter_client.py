"""
OpenRouter client.

OpenRouter exposes an OpenAI-compatible /chat/completions endpoint that
proxies to many underlying models. We use it two ways:

1. Directly via httpx for simple raw-text completions (used by nothing
   critical — kept for flexibility / health checks).
2. Via `pydantic_ai.models.openai.OpenAIModel` pointed at OpenRouter's
   base_url, which is how our agents actually run — this gives us
   structured, validated output for free.
"""
from __future__ import annotations

import httpx
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.llm.base import LLMProvider

logger = get_logger(__name__)


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self) -> None:
        self.__client: AsyncOpenAI | None = None

    @property
    def _client(self) -> AsyncOpenAI:
        if self.__client is None:
            self.__client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY or "unset",
                base_url=str(settings.OPENROUTER_BASE_URL),
                default_headers={
                    # OpenRouter uses these for its leaderboard / rate-limit attribution.
                    "HTTP-Referer": "https://lumora.app",
                    "X-Title": "Lumora AI Content Studio",
                },
            )
        return self.__client

    @retry(
        reraise=True,
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    )
    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        if not settings.OPENROUTER_API_KEY:
            raise AgentExecutionError("OpenRouter API key not configured.")
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
            )
            content = response.choices[0].message.content
            if not content:
                raise AgentExecutionError("LLM returned an empty completion.")
            return content
        except Exception as exc:  # noqa: BLE001
            logger.error("OpenRouter completion failed for model=%s: %s", model, exc)
            raise AgentExecutionError(f"OpenRouter request failed: {exc}") from exc

    def as_pydantic_ai_model(self, model_name: str) -> OpenAIChatModel:
        """
        Build a Pydantic AI model bound to OpenRouter. Pydantic AI's OpenAI-
        compatible chat model works unmodified against OpenRouter because
        OpenRouter mirrors the OpenAI chat completions schema.

        Note: this only *constructs* the model wrapper — it doesn't make a
        network call — so it's safe to call even before OPENROUTER_API_KEY
        is set. The key is validated lazily on first actual agent run by the
        underlying OpenAI client, which will surface a clear 401 from
        OpenRouter if the key is missing or invalid.
        """
        provider = OpenAIProvider(
            base_url=str(settings.OPENROUTER_BASE_URL),
            api_key=settings.OPENROUTER_API_KEY or "unset",
        )
        return OpenAIChatModel(model_name, provider=provider)


_openrouter_singleton: OpenRouterProvider | None = None


def get_openrouter_provider() -> OpenRouterProvider:
    global _openrouter_singleton
    if _openrouter_singleton is None:
        _openrouter_singleton = OpenRouterProvider()
    return _openrouter_singleton
