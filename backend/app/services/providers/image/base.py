from abc import ABC, abstractmethod


class ImageProvider(ABC):
    name: str

    @abstractmethod
    async def generate_image(
        self, *, prompt: str, negative_prompt: str = "", aspect_ratio: str = "9:16"
    ) -> bytes:
        """Generate an image and return raw PNG/JPEG bytes. Raise on failure."""
        raise NotImplementedError
