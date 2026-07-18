from app.core.config import settings
from app.schemas.agent import ImagePromptOutput, ScenePlanOutput
from app.services.agents.base import BaseLumoraAgent

_SYSTEM_PROMPT = """You are Lumora's Image Prompt Agent, an expert prompt engineer for
text-to-image diffusion models (Stable Diffusion / FLUX family).

Rules:
- Each prompt must be a single, dense, comma-separated descriptor string: subject,
  setting, lighting, composition, camera/lens detail, art style, mood. No full sentences,
  no "a picture of", no scene numbers or narrative text inside the prompt itself.
- Apply the shared visual_style consistently across every prompt so the set of images
  looks cohesive, while varying subject/composition per scene.
- Always include a negative_prompt excluding common diffusion artifacts relevant to the
  subject (e.g. 'text, watermark, extra limbs, blurry, distorted proportions').
- Default aspect_ratio to 9:16 for short-form vertical video unless told otherwise."""


class ImagePromptAgent(BaseLumoraAgent[ImagePromptOutput]):
    output_schema = ImagePromptOutput
    system_prompt = _SYSTEM_PROMPT
    model_name = settings.OPENROUTER_SCENE_MODEL
    agent_label = "ImagePromptAgent"

    def build_user_prompt(self, *, scene_plan: ScenePlanOutput) -> str:
        scenes_block = "\n".join(
            f"[{s.order}] {s.visual_description} (camera: {s.camera_motion}, "
            f"{s.duration_seconds:.1f}s)"
            for s in scene_plan.scenes
        )
        return (
            f"Overall visual style: {scene_plan.visual_style}\n"
            f"Scenes:\n{scenes_block}\n\n"
            "Generate one text-to-image prompt per scene, matching scene_order to the "
            "scene numbers above, plus a shared style_reference string summarizing the "
            "consistent art direction applied across all prompts."
        )
