import asyncio
import io

from gtts import gTTS

from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.tts.base import TTSProvider

logger = get_logger(__name__)


class GTTSProvider(TTSProvider):
    """
    Free, no-API-key fallback. Lower quality than ElevenLabs but has no
    external dependency beyond Google's public TTS endpoint, so it keeps
    the pipeline functional even with zero paid API keys configured.
    """

    name = "gtts"

    async def synthesize(self, *, text: str, voice_id: str | None = None) -> bytes:
        # gTTS's synthesis call is blocking (network I/O without asyncio support),
        # so we push it to a thread to avoid blocking the event loop.
        def _generate() -> bytes:
            buffer = io.BytesIO()
            tts = gTTS(text=text, lang="en")
            tts.write_to_fp(buffer)
            return buffer.getvalue()

        try:
            return await asyncio.to_thread(_generate)
        except Exception as exc:  # noqa: BLE001
            logger.warning("gTTS synthesis failed: %s", exc)
            raise AgentExecutionError(f"gTTS provider failed: {exc}") from exc
