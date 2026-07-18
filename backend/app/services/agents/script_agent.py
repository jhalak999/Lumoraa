from app.core.config import settings
from app.models.project import ContentTone
from app.schemas.agent import ResearchOutput, ScriptOutput
from app.services.agents.base import BaseLumoraAgent

_SYSTEM_PROMPT = """You are Lumora's Script Agent, an expert short-form video scriptwriter
who has written for top-performing educational and entertainment channels.

Rules:
- The `hook` (first line) must earn attention in under 3 seconds — no throat-clearing,
  no "In this video we'll talk about...". Start mid-action, with a question, or a
  surprising claim.
- Write for the EAR, not the eye: short clauses, natural spoken rhythm, no jargon unless
  the tone/audience calls for it.
- Respect the target duration: assume ~2.5 spoken words per second, and size total word
  count accordingly.
- Every line must earn its place — cut anything that doesn't build the narrative or payoff.
- End with a clear, natural call to action appropriate to the platform (follow, comment,
  watch next) — never salesy or robotic.
- Base the content on the provided research; do not invent facts that contradict it."""


class ScriptAgent(BaseLumoraAgent[ScriptOutput]):
    output_schema = ScriptOutput
    system_prompt = _SYSTEM_PROMPT
    model_name = settings.OPENROUTER_SCRIPT_MODEL
    agent_label = "ScriptAgent"

    def build_user_prompt(
        self,
        *,
        topic: str,
        tone: ContentTone,
        target_duration_seconds: int,
        research: ResearchOutput,
    ) -> str:
        facts_block = "\n".join(
            f"- {f.claim} ({f.supporting_detail})" for f in research.key_facts
        )
        return (
            f"Topic: {topic}\n"
            f"Tone: {tone.value}\n"
            f"Target duration: {target_duration_seconds} seconds "
            f"(~{int(target_duration_seconds * 2.5)} words)\n"
            f"Narrative angle: {research.suggested_angle}\n"
            f"Target audience: {research.target_audience}\n\n"
            f"Research facts to draw from:\n{facts_block}\n\n"
            "Write the full narration script as an ordered list of lines with delivery "
            "notes, plus a hook and a call to action. Set estimated_duration_seconds and "
            "word_count accurately based on the actual text you write."
        )
