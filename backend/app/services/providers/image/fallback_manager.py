"""
Fallback manager for image generation.

Tries providers in the order configured by `settings.IMAGE_PROVIDER_ORDER`,
moving to the next provider on ANY failure (auth error, rate limit, timeout,
content policy rejection). This is what makes image generation resilient in
production — a single provider outage doesn't take down the pipeline.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import AllProvidersFailedError
from app.core.logging import get_logger
from app.services.providers.image.base import ImageProvider
from app.services.providers.image.openai_provider import OpenAIImageProvider
from app.services.providers.image.replicate_provider import ReplicateImageProvider
from app.services.providers.image.stability_provider import StabilityImageProvider

logger = get_logger(__name__)

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "stability": StabilityImageProvider,
    "replicate": ReplicateImageProvider,
    "openai": OpenAIImageProvider,
}


class ImageFallbackManager:
    def __init__(self, provider_order: list[str] | None = None) -> None:
        if provider_order is None:
            order = settings.DEMO_IMAGE_PROVIDER_ORDER if settings.DEMO_MODE else settings.IMAGE_PROVIDER_ORDER
        else:
            order = provider_order
        self._providers: list[ImageProvider] = [
            _PROVIDER_REGISTRY[name]() for name in order if name in _PROVIDER_REGISTRY
        ]
        if not self._providers:
            raise ValueError("No image providers configured.")

    async def generate(
        self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16"
    ) -> tuple[bytes, str]:
        """Returns (image_bytes, provider_name_used)."""
        errors: list[str] = []
        for provider in self._providers:
            try:
                image_bytes = await provider.generate_image(
                    prompt=prompt, negative_prompt=negative_prompt, aspect_ratio=aspect_ratio
                )
                logger.info("Image generated successfully via provider=%s", provider.name)
                return image_bytes, provider.name
            except Exception as exc:  # noqa: BLE001
                logger.warning("Image provider=%s failed, trying next: %s", provider.name, exc)
                errors.append(f"{provider.name}: {exc}")

        raise AllProvidersFailedError(
            "All image providers failed.", details={"attempts": errors}
        )
