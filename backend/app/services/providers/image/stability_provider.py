import httpx

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.image.base import ImageProvider

logger = get_logger(__name__)

_ASPECT_TO_DIMENSIONS = {
    "9:16": (768, 1344),
    "16:9": (1344, 768),
    "1:1": (1024, 1024),
}


class StabilityImageProvider(ImageProvider):
    name = "stability"

    def __init__(self) -> None:
        self._api_key = settings.STABILITY_API_KEY
        self._base_url = "https://api.stability.ai/v2beta/stable-image/generate/core"

    async def generate_image(
        self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16"
    ) -> bytes:
        if not self._api_key:
            raise AgentExecutionError("Stability API key not configured.")

        aspect_ratio_param = aspect_ratio if aspect_ratio in ("9:16", "16:9", "1:1") else "9:16"

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    self._base_url,
                    headers={"Authorization": f"Bearer {self._api_key}", "Accept": "image/*"},
                    files={"none": ""},
                    data={
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "aspect_ratio": aspect_ratio_param,
                        "output_format": "png",
                    },
                )
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as exc:
                logger.warning("Stability image generation failed: %s", exc.response.text)
                raise AgentExecutionError(f"Stability provider failed: {exc}") from exc
            except httpx.HTTPError as exc:
                raise AgentExecutionError(f"Stability provider network error: {exc}") from exc
