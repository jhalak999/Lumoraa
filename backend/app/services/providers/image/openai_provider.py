import base64

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.image.base import ImageProvider

logger = get_logger(__name__)

_ASPECT_TO_SIZE = {"9:16": "1024x1792", "16:9": "1792x1024", "1:1": "1024x1024"}


class OpenAIImageProvider(ImageProvider):
    """Last-resort fallback using DALL-E 3. No native negative_prompt support,
    so we fold exclusions into the main prompt text."""

    name = "openai"

    def __init__(self) -> None:
        # Client is constructed lazily (see _client property) so that simply
        # instantiating this provider — e.g. as part of a fallback chain —
        # doesn't fail when OPENAI_API_KEY isn't configured. It only needs to
        # exist if this provider is actually reached.
        self.__client: AsyncOpenAI | None = None

    @property
    def _client(self) -> AsyncOpenAI:
        if self.__client is None:
            if not settings.OPENAI_API_KEY:
                raise AgentExecutionError("OpenAI API key not configured.")
            self.__client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self.__client

    async def generate_image(
        self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16"
    ) -> bytes:
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f". Do not include: {negative_prompt}"

        size = _ASPECT_TO_SIZE.get(aspect_ratio, "1024x1792")

        try:
            response = await self._client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size=size,
                quality="standard",
                response_format="b64_json",
                n=1,
            )
            b64 = response.data[0].b64_json
            return base64.b64decode(b64)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI image generation failed: %s", exc)
            raise AgentExecutionError(f"OpenAI image provider failed: {exc}") from exc
