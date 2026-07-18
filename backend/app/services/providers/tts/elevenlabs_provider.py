import httpx

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.tts.base import TTSProvider

logger = get_logger(__name__)


class ElevenLabsTTSProvider(TTSProvider):
    name = "elevenlabs"

    def __init__(self) -> None:
        self._api_key = settings.ELEVENLABS_API_KEY

    async def synthesize(self, *, text: str, voice_id: str | None = None) -> bytes:
        if not self._api_key:
            raise AgentExecutionError("ElevenLabs API key not configured.")

        voice = voice_id or settings.ELEVENLABS_DEFAULT_VOICE_ID
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    url,
                    headers={
                        "xi-api-key": self._api_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/mpeg",
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                    },
                )
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as exc:
                logger.warning("ElevenLabs TTS failed: %s", exc.response.text)
                raise AgentExecutionError(f"ElevenLabs provider failed: {exc}") from exc
            except httpx.HTTPError as exc:
                raise AgentExecutionError(f"ElevenLabs network error: {exc}") from exc
