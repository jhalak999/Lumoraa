"""
Thumbnail generation.

Takes the first (or a chosen) scene image and overlays a bold, high-contrast
title snippet + gradient for legibility — the standard "clickable thumbnail"
treatment — using Pillow. Kept independent of the video service since
thumbnails are generated from a still image, not the rendered video.
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from app.core.exceptions import MediaProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)

_THUMBNAIL_SIZE = (1080, 1920)  # matches default portrait video canvas
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_thumbnail(*, source_image_bytes: bytes, title_text: str) -> bytes:
    try:
        image = Image.open(io.BytesIO(source_image_bytes)).convert("RGB")
        image = image.resize(_THUMBNAIL_SIZE)

        # Darken the lower third slightly so overlaid text stays legible
        # regardless of the underlying scene's brightness.
        gradient = Image.new("L", image.size, 0)
        gradient_draw = ImageDraw.Draw(gradient)
        h = image.size[1]
        for y in range(h):
            fade_start = int(h * 0.55)
            if y >= fade_start:
                alpha = int(190 * (y - fade_start) / (h - fade_start))
                gradient_draw.line([(0, y), (image.size[0], y)], fill=alpha)
        black = Image.new("RGB", image.size, (0, 0, 0))
        image = Image.composite(black, image, gradient)

        image = ImageEnhance.Contrast(image).enhance(1.08)

        draw = ImageDraw.Draw(image)
        font = _load_font(size=88)
        max_width = int(image.size[0] * 0.88)
        lines = _wrap_text(draw, title_text.upper(), font, max_width)[:3]

        line_height = 100
        total_text_height = line_height * len(lines)
        y = image.size[1] - total_text_height - 90

        for line in lines:
            line_width = draw.textlength(line, font=font)
            x = (image.size[0] - line_width) / 2
            # Simple stroke outline for readability over any background.
            draw.text((x, y), line, font=font, fill="white", stroke_width=4, stroke_fill="black")
            y += line_height

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
    except Exception as exc:  # noqa: BLE001
        logger.error("Thumbnail generation failed: %s", exc)
        raise MediaProcessingError(f"Thumbnail generation failed: {exc}") from exc
