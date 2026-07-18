from abc import ABC, abstractmethod


class TTSProvider(ABC):
    name: str

    @abstractmethod
    async def synthesize(self, *, text: str, voice_id: str | None = None) -> bytes:
        """Return raw MP3 audio bytes for the given text."""
        raise NotImplementedError
