from app.core.config import settings
from app.schemas.agent import ScenePlanOutput, ScriptOutput
from app.services.agents.base import BaseLumoraAgent

_SYSTEM_PROMPT = """You are Lumora's Scene Planner Agent, a visual storytelling specialist
who converts narration scripts into shot-by-shot scene breakdowns for AI-generated video.

Rules:
- Every scene must map to one or more contiguous script lines (script_line_orders).
- Scene durations must sum to approximately the script's estimated_duration_seconds.
- Vary camera_motion across scenes (don't repeat "static" for every scene) to keep the
  video visually dynamic, but keep motion choices realistic for AI image-to-video pipelines
  (slow zoom in/out, gentle pan, static hold with subtle parallax).
- visual_description must describe a single, concrete, renderable image — not an abstract
  concept. Ground abstract narration in a specific visual metaphor or scene.
- Pick ONE consistent visual_style for the whole plan (e.g. 'cinematic photorealism, warm
  golden-hour lighting') so all generated images look like they belong to the same video."""


class ScenePlannerAgent(BaseLumoraAgent[ScenePlanOutput]):
    output_schema = ScenePlanOutput
    system_prompt = _SYSTEM_PROMPT
    model_name = settings.OPENROUTER_SCENE_MODEL
    agent_label = "ScenePlannerAgent"

    def build_user_prompt(self, *, script: ScriptOutput) -> str:
        lines_block = "\n".join(f"[{l.order}] ({l.speaker_note}) {l.text}" for l in script.lines)
        return (
            f"Hook: {script.hook}\n"
            f"Script lines:\n{lines_block}\n"
            f"Call to action: {script.call_to_action}\n"
            f"Total estimated duration: {script.estimated_duration_seconds} seconds\n\n"
            "Break this script into a shot-by-shot scene plan suitable for AI image "
            "generation followed by ken-burns-style video assembly."
        )
