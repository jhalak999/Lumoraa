"""
Pipeline orchestrator.

This is the single place that knows the ORDER agents run in and how each
agent's output feeds the next one's input. Individual agents stay ignorant
of the pipeline as a whole (single responsibility) — the orchestrator wires
them together. Each stage is exposed as its own method so the API/Celery
layer can call a single stage (e.g. "regenerate just the script") without
re-running the whole pipeline.
"""
from __future__ import annotations

from app.models.project import ContentTone
from app.schemas.agent import (
    ImagePromptOutput,
    ResearchOutput,
    ScenePlanOutput,
    ScriptOutput,
    SeoOutput,
)
from app.services.agents.image_prompt_agent import ImagePromptAgent
from app.services.agents.research_agent import ResearchAgent
from app.services.agents.scene_planner_agent import ScenePlannerAgent
from app.services.agents.script_agent import ScriptAgent
from app.services.agents.seo_agent import SeoAgent


class ContentPipelineOrchestrator:
    """Stateless coordinator — safe to instantiate per-request or per-task."""

    def __init__(self) -> None:
        self._research_agent = ResearchAgent()
        self._script_agent = ScriptAgent()
        self._scene_agent = ScenePlannerAgent()
        self._image_prompt_agent = ImagePromptAgent()
        self._seo_agent = SeoAgent()

    async def run_research(
        self, *, topic: str, tone: ContentTone, target_duration_seconds: int
    ) -> ResearchOutput:
        return await self._research_agent.run(
            topic=topic, tone=tone, target_duration_seconds=target_duration_seconds
        )

    async def run_script(
        self,
        *,
        topic: str,
        tone: ContentTone,
        target_duration_seconds: int,
        research: ResearchOutput,
    ) -> ScriptOutput:
        return await self._script_agent.run(
            topic=topic,
            tone=tone,
            target_duration_seconds=target_duration_seconds,
            research=research,
        )

    async def run_scene_plan(self, *, script: ScriptOutput) -> ScenePlanOutput:
        return await self._scene_agent.run(script=script)

    async def run_image_prompts(self, *, scene_plan: ScenePlanOutput) -> ImagePromptOutput:
        return await self._image_prompt_agent.run(scene_plan=scene_plan)

    async def run_seo(self, *, script: ScriptOutput, topic: str) -> SeoOutput:
        return await self._seo_agent.run(script=script, topic=topic)


_orchestrator_singleton: ContentPipelineOrchestrator | None = None


def get_orchestrator() -> ContentPipelineOrchestrator:
    global _orchestrator_singleton
    if _orchestrator_singleton is None:
        _orchestrator_singleton = ContentPipelineOrchestrator()
    return _orchestrator_singleton
