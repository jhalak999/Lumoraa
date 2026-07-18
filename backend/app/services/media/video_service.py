"""
FFmpeg-based video assembly.

Pipeline: for each scene image, apply a subtle Ken Burns zoom/pan for the
scene's duration, concatenate all scene clips, overlay the voice track, then
burn in subtitles from the generated .srt. All FFmpeg invocations run via
asyncio subprocess so the event loop isn't blocked, and every step writes to
a per-project temp workspace that's cleaned up after the final video is
persisted to storage.
"""
from __future__ import annotations

import asyncio
import shlex
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import MediaProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)

_VIDEO_RESOLUTION = settings.DEMO_VIDEO_RESOLUTION if settings.DEMO_MODE else settings.VIDEO_DEFAULT_RESOLUTION
_WIDTH, _HEIGHT = (int(x) for x in _VIDEO_RESOLUTION.split("x"))
_FPS = settings.DEMO_VIDEO_FPS if settings.DEMO_MODE else settings.VIDEO_DEFAULT_FPS


async def _run_ffmpeg(args: list[str], *, description: str) -> None:
    cmd = [settings.FFMPEG_BINARY, "-y", *args]
    logger.info("Running ffmpeg (%s): %s", description, shlex.join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise MediaProcessingError(
            f"ffmpeg failed during '{description}'",
            details={"stderr": stderr.decode(errors="ignore")[-2000:]},
        )


async def _probe_duration_seconds(path: Path) -> float:
    cmd = [
        settings.FFPROBE_BINARY,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise MediaProcessingError("ffprobe failed to read audio duration.")
    try:
        return float(stdout.decode().strip())
    except ValueError as exc:
        raise MediaProcessingError("Could not parse audio duration from ffprobe output.") from exc


async def _build_scene_clip(
    *, image_path: Path, duration_seconds: float, workdir: Path, index: int, zoom_in: bool
) -> Path:
    """Apply a Ken Burns zoom (alternating in/out per scene for visual variety)."""
    out_path = workdir / f"scene_{index:03d}.mp4"
    total_frames = max(int(duration_seconds * _FPS), 1)

    # zoompan needs an upscaled source to zoom into without pixelation artifacts.
    zoom_expr = "1+0.0015*in" if zoom_in else "1.3-0.0015*in"
    filter_chain = (
        f"scale=8000:-1,"
        f"zoompan=z='{zoom_expr}':d={total_frames}:s={_WIDTH}x{_HEIGHT}:fps={_FPS}"
    )

    await _run_ffmpeg(
        [
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-vf",
            filter_chain,
            "-t",
            str(duration_seconds),
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ],
        description=f"ken-burns scene {index}",
    )
    return out_path


async def _concat_clips(clip_paths: list[Path], workdir: Path) -> Path:
    concat_list_path = workdir / "concat_list.txt"
    concat_list_path.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in clip_paths), encoding="utf-8"
    )
    silent_video_path = workdir / "silent_concatenated.mp4"
    await _run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list_path),
            "-c",
            "copy",
            str(silent_video_path),
        ],
        description="concat scenes",
    )
    return silent_video_path


async def _mux_audio(*, video_path: Path, audio_path: Path, workdir: Path) -> Path:
    out_path = workdir / "with_audio.mp4"
    await _run_ffmpeg(
        [
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(out_path),
        ],
        description="mux audio",
    )
    return out_path


async def _burn_subtitles(*, video_path: Path, srt_path: Path, workdir: Path) -> Path:
    out_path = workdir / "final.mp4"
    # Style: bold white text, black outline, positioned in the lower-middle third —
    # readable over any background image.
    style = (
        "FontName=Arial,FontSize=14,Bold=1,PrimaryColour=&HFFFFFF&,"
        "OutlineColour=&H000000&,BorderStyle=1,Outline=2,Alignment=2,MarginV=80"
    )
    await _run_ffmpeg(
        [
            "-i",
            str(video_path),
            "-vf",
            f"subtitles={shlex.quote(str(srt_path))}:force_style='{style}'",
            "-c:a",
            "copy",
            str(out_path),
        ],
        description="burn subtitles",
    )
    return out_path


async def assemble_video(
    *,
    scene_image_paths: list[Path],
    scene_durations_seconds: list[float],
    audio_path: Path,
    srt_path: Path,
    output_path: Path,
) -> Path:
    """
    Full assembly: images -> Ken Burns clips -> concat -> + audio -> + burned subtitles.
    Returns the path to the final rendered video (already copied to `output_path`).
    """
    if len(scene_image_paths) != len(scene_durations_seconds):
        raise MediaProcessingError("Mismatched scene image count vs duration count.")

    workdir = output_path.parent / f"_tmp_{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        clip_paths = []
        for i, (image_path, duration) in enumerate(zip(scene_image_paths, scene_durations_seconds)):
            clip = await _build_scene_clip(
                image_path=image_path,
                duration_seconds=duration,
                workdir=workdir,
                index=i,
                zoom_in=(i % 2 == 0),
            )
            clip_paths.append(clip)

        silent_video = await _concat_clips(clip_paths, workdir)
        with_audio = await _mux_audio(video_path=silent_video, audio_path=audio_path, workdir=workdir)
        final = await _burn_subtitles(video_path=with_audio, srt_path=srt_path, workdir=workdir)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final.replace(output_path)
        return output_path
    finally:
        # Best-effort cleanup of intermediate files; failures here shouldn't fail the job.
        import shutil

        shutil.rmtree(workdir, ignore_errors=True)
