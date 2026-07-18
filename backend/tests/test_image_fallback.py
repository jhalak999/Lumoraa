import pytest

from app.core.exceptions import AllProvidersFailedError
from app.services.providers.image.base import ImageProvider
from app.services.providers.image.fallback_manager import ImageFallbackManager


class _FailingProvider(ImageProvider):
    name = "failing"

    async def generate_image(self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16") -> bytes:
        raise RuntimeError("simulated provider outage")


class _WorkingProvider(ImageProvider):
    name = "working"

    async def generate_image(self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16") -> bytes:
        return b"fake-image-bytes"


@pytest.mark.anyio
async def test_falls_back_to_second_provider_on_first_failure():
    manager = ImageFallbackManager.__new__(ImageFallbackManager)
    manager._providers = [_FailingProvider(), _WorkingProvider()]

    image_bytes, provider_used = await manager.generate(prompt="a red fox in a forest")

    assert image_bytes == b"fake-image-bytes"
    assert provider_used == "working"


@pytest.mark.anyio
async def test_raises_when_all_providers_fail():
    manager = ImageFallbackManager.__new__(ImageFallbackManager)
    manager._providers = [_FailingProvider(), _FailingProvider()]

    with pytest.raises(AllProvidersFailedError):
        await manager.generate(prompt="a red fox in a forest")
