"""
Subtitle generation.

We already know the exact narration text (it came from our own ScriptAgent),
but TTS engines don't hand back word-level timestamps. Rather than trust a
naive "characters per second" estimate — which drifts badly with pauses and
punctuation — we run faster-whisper over the SYNTHESIZED audio to get real
word-level timestamps, then group words into subtitle cues. This is the same
forced-alignment-via-ASR approach used in production captioning tools.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.exceptions import MediaProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)

_MODEL_SIZE = "base"  # good accuracy/speed tradeoff for short-form clips
_MAX_WORDS_PER_CUE = 6
_MAX_CUE_DURATION_SECONDS = 3.5

_model_singleton: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model_singleton
    if _model_singleton is None:
        # CPU by default; set device="cuda" via env-driven config if a GPU worker is available.
        _model_singleton = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model_singleton


@dataclass
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str


def _format_srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _group_words_into_cues(words: list) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    current_words: list[str] = []
    cue_start: float | None = None
    cue_index = 1

    for word in words:
        if cue_start is None:
            cue_start = word.start
        current_words.append(word.word.strip())

        duration = word.end - cue_start
        if len(current_words) >= _MAX_WORDS_PER_CUE or duration >= _MAX_CUE_DURATION_SECONDS:
            cues.append(
                SubtitleCue(index=cue_index, start=cue_start, end=word.end, text=" ".join(current_words))
            )
            cue_index += 1
            current_words = []
            cue_start = None

    if current_words and cue_start is not None:
        cues.append(
            SubtitleCue(index=cue_index, start=cue_start, end=words[-1].end, text=" ".join(current_words))
        )

    return cues


def generate_cues_from_audio(audio_path: Path) -> list[SubtitleCue]:
    try:
        model = _get_model()
        segments, _info = model.transcribe(str(audio_path), word_timestamps=True)

        all_words = []
        for segment in segments:
            all_words.extend(segment.words or [])

        if not all_words:
            raise MediaProcessingError("Transcription produced no word-level timestamps.")

        return _group_words_into_cues(all_words)
    except Exception as exc:  # noqa: BLE001
        logger.error("Subtitle generation failed for %s: %s", audio_path, exc)
        raise MediaProcessingError(f"Subtitle generation failed: {exc}") from exc


def cues_to_srt(cues: list[SubtitleCue]) -> str:
    lines = []
    for cue in cues:
        lines.append(str(cue.index))
        lines.append(f"{_format_srt_timestamp(cue.start)} --> {_format_srt_timestamp(cue.end)}")
        lines.append(cue.text)
        lines.append("")
    return "\n".join(lines)


def generate_srt_from_audio(audio_path: Path) -> str:
    cues = generate_cues_from_audio(audio_path)
    return cues_to_srt(cues)
