from app.core.config import settings
from app.models.project import ContentTone
from app.schemas.agent import ResearchOutput
from app.services.agents.base import BaseLumoraAgent

_SYSTEM_PROMPT = """You are Lumora's Research Agent, a specialist in rapidly synthesizing
accurate, engaging factual grounding for short-form video content.

Rules:
- Every fact must be plausible, specific, and non-generic. Avoid vague statements.
- Do NOT fabricate statistics with false precision; if unsure of an exact number, describe
  the magnitude qualitatively instead.
- Prioritize facts that are surprising, emotionally resonant, or highly shareable — this
  research will drive a video meant to capture attention within 3 seconds.
- Tailor tone and depth to the requested audience and content tone.
- Return ONLY the structured fields requested. No preamble, no meta-commentary."""


class ResearchAgent(BaseLumoraAgent[ResearchOutput]):
    output_schema = ResearchOutput
    system_prompt = _SYSTEM_PROMPT
    model_name = settings.OPENROUTER_RESEARCH_MODEL
    agent_label = "ResearchAgent"

    def build_user_prompt(self, *, topic: str, tone: ContentTone, target_duration_seconds: int) -> str:
        return (
            f"Topic: {topic}\n"
            f"Content tone: {tone.value}\n"
            f"Target video length: {target_duration_seconds} seconds\n\n"
            "Research this topic and return: a topic summary, 3-12 key facts ranked by "
            "relevance, the single most compelling narrative angle for a short video, and "
            "the likely target audience for this content."
        )
