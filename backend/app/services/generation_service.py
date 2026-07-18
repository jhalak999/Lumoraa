"""
Generation service.

This is where the agent/provider layers meet persistence. Each method
corresponds to exactly one pipeline stage, updates `project.status`
accordingly, and is written to be safely resumable — if step N fails, steps
1..N-1's outputs are already committed, so retrying only re-runs step N.

Called from Celery tasks (app/tasks/generation_tasks.py), never directly
from API route handlers — routes only enqueue tasks and read status.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import MediaProcessingError, ProjectStateError
from app.core.logging import get_logger
from app.models.asset import AssetType
from app.models.project import Project, ProjectStatus
from app.schemas.agent import ImagePromptOutput, ResearchOutput, ScenePlanOutput, ScriptOutput, SeoOutput
from app.services.agents.orchestrator import get_orchestrator
from app.services.media import subtitle_service, thumbnail_service, video_service
from app.services.project_service import ProjectService
from app.services.providers.image.fallback_manager import ImageFallbackManager
from app.services.providers.tts.fallback_manager import TTSFallbackManager
from app.services.storage_service import build_project_relative_path, get_storage_backend

logger = get_logger(__name__)


class GenerationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.project_service = ProjectService(db)
        self.orchestrator = get_orchestrator()
        self.storage = get_storage_backend()

    async def _get_project(self, project_id: uuid.UUID) -> Project:
        project = await self.db.get(Project, project_id)
        if not project:
            raise ProjectStateError("Project not found.")
        return project

    def _effective_target_duration(self, project: Project) -> int:
        if settings.DEMO_MODE:
            return min(project.target_duration_seconds, settings.DEMO_MAX_VIDEO_DURATION_SECONDS)
        return project.target_duration_seconds

    # ---------------------------------------------------------------- research
    async def generate_research(self, project_id: uuid.UUID) -> ResearchOutput:
        project = await self._get_project(project_id)
        project.status = ProjectStatus.RESEARCHING
        await self.db.flush()

        result = await self.orchestrator.run_research(
            topic=project.topic,
            tone=project.tone,
            target_duration_seconds=self._effective_target_duration(project),
        )
        project.research_data = result.model_dump()
        project.status = ProjectStatus.RESEARCH_READY
        await self.db.flush()
        return result

    # ------------------------------------------------------------------ script
    async def generate_script(self, project_id: uuid.UUID) -> ScriptOutput:
        project = await self._get_project(project_id)
        if not project.research_data:
            raise ProjectStateError("Research must be completed before generating a script.")

        project.status = ProjectStatus.SCRIPTING
        await self.db.flush()

        research = ResearchOutput.model_validate(project.research_data)
        result = await self.orchestrator.run_script(
            topic=project.topic,
            tone=project.tone,
            target_duration_seconds=self._effective_target_duration(project),
            research=research,
        )
        project.script_data = result.model_dump()
        project.status = ProjectStatus.SCRIPT_READY
        await self.db.flush()
        return result

    # ------------------------------------------------------------- scene plan
    async def generate_scene_plan(self, project_id: uuid.UUID) -> ScenePlanOutput:
        project = await self._get_project(project_id)
        if not project.script_data:
            raise ProjectStateError("Script must be completed before planning scenes.")

        project.status = ProjectStatus.PLANNING_SCENES
        await self.db.flush()

        script = ScriptOutput.model_validate(project.script_data)
        result = await self.orchestrator.run_scene_plan(script=script)
        if settings.DEMO_MODE:
            scenes = result.scenes[: settings.DEMO_MAX_SCENES]
            total_duration = sum(scene.duration_seconds for scene in scenes)
            if total_duration > settings.DEMO_MAX_VIDEO_DURATION_SECONDS:
                scale = settings.DEMO_MAX_VIDEO_DURATION_SECONDS / total_duration
                for scene in scenes:
                    scene.duration_seconds *= scale
                total_duration = settings.DEMO_MAX_VIDEO_DURATION_SECONDS
            result = ScenePlanOutput(
                scenes=scenes,
                total_duration_seconds=total_duration,
                visual_style=result.visual_style,
            )
        project.scene_plan = result.model_dump()
        project.status = ProjectStatus.SCENES_READY
        await self.db.flush()
        return result

    # --------------------------------------------------------- image prompts
    async def generate_image_prompts(self, project_id: uuid.UUID) -> ImagePromptOutput:
        project = await self._get_project(project_id)
        if not project.scene_plan:
            raise ProjectStateError("Scene plan must exist before generating image prompts.")

        project.status = ProjectStatus.GENERATING_IMAGE_PROMPTS
        await self.db.flush()

        scene_plan = ScenePlanOutput.model_validate(project.scene_plan)
        result = await self.orchestrator.run_image_prompts(scene_plan=scene_plan)
        project.image_prompts = result.model_dump()
        project.status = ProjectStatus.IMAGE_PROMPTS_READY
        await self.db.flush()
        return result

    # ------------------------------------------------------------- SEO / seo
    async def generate_seo(self, project_id: uuid.UUID) -> SeoOutput:
        project = await self._get_project(project_id)
        if not project.script_data:
            raise ProjectStateError("Script must exist before generating SEO metadata.")

        project.status = ProjectStatus.GENERATING_SEO
        await self.db.flush()

        script = ScriptOutput.model_validate(project.script_data)
        result = await self.orchestrator.run_seo(script=script, topic=project.topic)
        project.seo_metadata = result.model_dump()
        project.status = ProjectStatus.SEO_READY
        await self.db.flush()
        return result

    # ---------------------------------------------------------------- images
    async def generate_images(self, project_id: uuid.UUID) -> list[str]:
        project = await self._get_project(project_id)
        if not project.image_prompts:
            raise ProjectStateError("Image prompts must exist before generating images.")

        project.status = ProjectStatus.GENERATING_IMAGES
        await self.db.flush()

        prompts = ImagePromptOutput.model_validate(project.image_prompts)
        manager = ImageFallbackManager()
        urls: list[str] = []

        for prompt in prompts.prompts:
            full_prompt = f"{prompt.prompt}, {prompts.style_reference}"
            image_bytes, provider_used = await manager.generate(
                prompt=full_prompt,
                negative_prompt=prompt.negative_prompt,
                aspect_ratio=prompt.aspect_ratio,
            )
            relative_path = build_project_relative_path(
                project.id, "images", f"scene_{prompt.scene_order:03d}.png"
            )
            url = await self.storage.save(data=image_bytes, relative_path=relative_path)
            await self.project_service.add_asset(
                project_id=project.id,
                asset_type=AssetType.SCENE_IMAGE,
                storage_path=relative_path,
                public_url=url,
                sequence_index=prompt.scene_order,
                provider_used=provider_used,
                file_size_bytes=len(image_bytes),
            )
            urls.append(url)

        project.status = ProjectStatus.IMAGES_READY
        await self.db.flush()
        return urls

    # ----------------------------------------------------------------- voice
    async def generate_voice(self, project_id: uuid.UUID) -> str:
        project = await self._get_project(project_id)
        if not project.script_data:
            raise ProjectStateError("Script must exist before generating voice.")

        project.status = ProjectStatus.GENERATING_VOICE
        await self.db.flush()

        script = ScriptOutput.model_validate(project.script_data)
        full_text = script.hook + " " + " ".join(line.text for line in script.lines) + " " + script.call_to_action

        manager = TTSFallbackManager()
        audio_bytes, provider_used = await manager.synthesize(text=full_text)

        relative_path = build_project_relative_path(project.id, "audio", "narration.mp3")
        url = await self.storage.save(data=audio_bytes, relative_path=relative_path)
        await self.project_service.add_asset(
            project_id=project.id,
            asset_type=AssetType.VOICE_AUDIO,
            storage_path=relative_path,
            public_url=url,
            provider_used=provider_used,
            file_size_bytes=len(audio_bytes),
        )

        project.status = ProjectStatus.VOICE_READY
        await self.db.flush()
        return url

    # ------------------------------------------------------------- subtitles
    async def generate_subtitles(self, project_id: uuid.UUID) -> str:
        project = await self._get_project(project_id)
        audio_relative_path = build_project_relative_path(project.id, "audio", "narration.mp3")
        audio_path = self.storage.resolve_local_path(audio_relative_path)
        if not audio_path.exists():
            raise ProjectStateError("Voice audio must be generated before subtitles.")

        project.status = ProjectStatus.GENERATING_SUBTITLES
        await self.db.flush()

        srt_content = subtitle_service.generate_srt_from_audio(audio_path)
        relative_path = build_project_relative_path(project.id, "subtitles", "captions.srt")
        url = await self.storage.save(data=srt_content.encode("utf-8"), relative_path=relative_path)
        await self.project_service.add_asset(
            project_id=project.id,
            asset_type=AssetType.SUBTITLE_FILE,
            storage_path=relative_path,
            public_url=url,
        )

        project.status = ProjectStatus.SUBTITLES_READY
        await self.db.flush()
        return url

    # ------------------------------------------------------------------ video
    async def render_video(self, project_id: uuid.UUID) -> str:
        project = await self._get_project(project_id)
        if not project.scene_plan:
            raise ProjectStateError("Scene plan required before rendering video.")

        project.status = ProjectStatus.RENDERING_VIDEO
        await self.db.flush()

        scene_plan = ScenePlanOutput.model_validate(project.scene_plan)
        scenes_sorted = sorted(scene_plan.scenes, key=lambda s: s.order)

        image_paths: list[Path] = []
        for scene in scenes_sorted:
            rel = build_project_relative_path(project.id, "images", f"scene_{scene.order:03d}.png")
            path = self.storage.resolve_local_path(rel)
            if not path.exists():
                raise ProjectStateError(f"Missing generated image for scene {scene.order}.")
            image_paths.append(path)

        audio_path = self.storage.resolve_local_path(
            build_project_relative_path(project.id, "audio", "narration.mp3")
        )
        srt_path = self.storage.resolve_local_path(
            build_project_relative_path(project.id, "subtitles", "captions.srt")
        )
        if not audio_path.exists() or not srt_path.exists():
            raise ProjectStateError("Voice audio and subtitles must exist before rendering video.")

        output_relative_path = build_project_relative_path(project.id, "video", "final.mp4")
        output_path = self.storage.resolve_local_path(output_relative_path)

        try:
            await video_service.assemble_video(
                scene_image_paths=image_paths,
                scene_durations_seconds=[s.duration_seconds for s in scenes_sorted],
                audio_path=audio_path,
                srt_path=srt_path,
                output_path=output_path,
            )
        except MediaProcessingError:
            project.status = ProjectStatus.FAILED
            project.error_message = "Video rendering failed. See logs for FFmpeg output."
            await self.db.flush()
            raise

        public_url = f"{settings.PUBLIC_ASSET_BASE_URL.rstrip('/')}/{output_relative_path}"
        await self.project_service.add_asset(
            project_id=project.id,
            asset_type=AssetType.FINAL_VIDEO,
            storage_path=output_relative_path,
            public_url=public_url,
            file_size_bytes=output_path.stat().st_size,
        )

        project.status = ProjectStatus.VIDEO_READY
        await self.db.flush()
        return public_url

    # -------------------------------------------------------------- thumbnail
    async def generate_thumbnail(self, project_id: uuid.UUID) -> str:
        project = await self._get_project(project_id)
        if not project.scene_plan or not project.scene_plan.get("scenes"):
            raise ProjectStateError("Scene plan must exist before generating a thumbnail.")
        first_scene_order = min(s["order"] for s in project.scene_plan["scenes"])
        first_image_path = self.storage.resolve_local_path(
            build_project_relative_path(project.id, "images", f"scene_{first_scene_order:03d}.png")
        )
        if not first_image_path.exists():
            raise ProjectStateError("Scene images must exist before generating a thumbnail.")

        project.status = ProjectStatus.GENERATING_THUMBNAIL
        await self.db.flush()

        title_source = project.title
        if project.seo_metadata and project.seo_metadata.get("titles"):
            title_source = project.seo_metadata["titles"][0]

        thumbnail_bytes = thumbnail_service.generate_thumbnail(
            source_image_bytes=first_image_path.read_bytes(), title_text=title_source
        )
        relative_path = build_project_relative_path(project.id, "thumbnail", "thumbnail.jpg")
        url = await self.storage.save(data=thumbnail_bytes, relative_path=relative_path)
        await self.project_service.add_asset(
            project_id=project.id,
            asset_type=AssetType.THUMBNAIL,
            storage_path=relative_path,
            public_url=url,
            file_size_bytes=len(thumbnail_bytes),
        )

        project.status = ProjectStatus.COMPLETED
        await self.db.flush()
        return url
