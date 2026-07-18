from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import AllProvidersFailedError
from app.core.logging import get_logger
from app.services.providers.tts.base import TTSProvider
from app.services.providers.tts.elevenlabs_provider import ElevenLabsTTSProvider
from app.services.providers.tts.gtts_provider import GTTSProvider

logger = get_logger(__name__)

_PROVIDER_REGISTRY: dict[str, type[TTSProvider]] = {
    "elevenlabs": ElevenLabsTTSProvider,
    "gtts": GTTSProvider,
}


class TTSFallbackManager:
    def __init__(self, provider_order: list[str] | None = None) -> None:
        if provider_order is None:
            order = settings.DEMO_TTS_PROVIDER_ORDER if settings.DEMO_MODE else settings.TTS_PROVIDER_ORDER
        else:
            order = provider_order
        self._providers: list[TTSProvider] = [
            _PROVIDER_REGISTRY[name]() for name in order if name in _PROVIDER_REGISTRY
        ]
        if not self._providers:
            raise ValueError("No TTS providers configured.")

    async def synthesize(self, *, text: str, voice_id: str | None = None) -> tuple[bytes, str]:
        errors: list[str] = []
        for provider in self._providers:
            try:
                audio_bytes = await provider.synthesize(text=text, voice_id=voice_id)
                logger.info("Voice synthesized successfully via provider=%s", provider.name)
                return audio_bytes, provider.name
            except Exception as exc:  # noqa: BLE001
                logger.warning("TTS provider=%s failed, trying next: %s", provider.name, exc)
                errors.append(f"{provider.name}: {exc}")

        raise AllProvidersFailedError("All TTS providers failed.", details={"attempts": errors})
