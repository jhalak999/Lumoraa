import asyncio

import httpx

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.image.base import ImageProvider

logger = get_logger(__name__)

_ASPECT_TO_SIZE = {"9:16": "768x1344", "16:9": "1344x768", "1:1": "1024x1024"}

# FLUX schnell is fast + cheap; good second-choice fallback behind Stability.
_MODEL_VERSION_ENDPOINT = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"


class ReplicateImageProvider(ImageProvider):
    name = "replicate"

    def __init__(self) -> None:
        self._api_token = settings.REPLICATE_API_TOKEN

    async def generate_image(
        self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16"
    ) -> bytes:
        if not self._api_token:
            raise AgentExecutionError("Replicate API token not configured.")

        headers = {
            "Authorization": f"Token {self._api_token}",
            "Content-Type": "application/json",
            "Prefer": "wait",  # ask Replicate to block until done, up to 60s
        }
        payload = {
            "input": {
                "prompt": f"{prompt}. Avoid: {negative_prompt}" if negative_prompt else prompt,
                "aspect_ratio": aspect_ratio if aspect_ratio in _ASPECT_TO_SIZE else "9:16",
                "output_format": "png",
            }
        }

        async with httpx.AsyncClient(timeout=90) as client:
            try:
                response = await client.post(_MODEL_VERSION_ENDPOINT, headers=headers, json=payload)
                response.raise_for_status()
                prediction = response.json()

                # If not synchronously completed, poll.
                status = prediction.get("status")
                get_url = prediction.get("urls", {}).get("get")
                attempts = 0
                while status not in ("succeeded", "failed", "canceled") and get_url and attempts < 20:
                    await asyncio.sleep(2)
                    poll = await client.get(get_url, headers=headers)
                    poll.raise_for_status()
                    prediction = poll.json()
                    status = prediction.get("status")
                    attempts += 1

                if status != "succeeded":
                    raise AgentExecutionError(f"Replicate prediction did not succeed: status={status}")

                output = prediction.get("output")
                image_url = output[0] if isinstance(output, list) else output
                image_resp = await client.get(image_url)
                image_resp.raise_for_status()
                return image_resp.content
            except httpx.HTTPStatusError as exc:
                logger.warning("Replicate image generation failed: %s", exc.response.text)
                raise AgentExecutionError(f"Replicate provider failed: {exc}") from exc
            except httpx.HTTPError as exc:
                raise AgentExecutionError(f"Replicate provider network error: {exc}") from exc
