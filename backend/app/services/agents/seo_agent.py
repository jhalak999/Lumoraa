from app.core.config import settings
from app.schemas.agent import ScriptOutput, SeoOutput
from app.services.agents.base import BaseLumoraAgent

_SYSTEM_PROMPT = """You are Lumora's SEO Agent, specializing in discoverability optimization
for short-form video platforms (YouTube Shorts, TikTok, Instagram Reels).

Rules:
- Titles must be under 100 characters, front-load the payoff/curiosity hook, and avoid
  clickbait that the content doesn't deliver on.
- Provide 3-5 title variants ordered strongest-first, covering different angles (curiosity,
  direct benefit, bold claim).
- Description should include the core value proposition in the first line (before any
  "read more" cutoff), naturally include 2-3 keywords, and end with a soft call to action.
- Hashtags: mix of broad-reach and niche-specific tags, no spaces, no more than 15.
- Keywords: search-intent phrases a viewer might type, not just topic nouns."""


class SeoAgent(BaseLumoraAgent[SeoOutput]):
    output_schema = SeoOutput
    system_prompt = _SYSTEM_PROMPT
    model_name = settings.OPENROUTER_SEO_MODEL
    agent_label = "SeoAgent"

    def build_user_prompt(self, *, script: ScriptOutput, topic: str) -> str:
        return (
            f"Topic: {topic}\n"
            f"Video hook: {script.hook}\n"
            f"Call to action: {script.call_to_action}\n"
            f"Approx duration: {script.estimated_duration_seconds}s\n\n"
            "Generate SEO-optimized titles, a description, hashtags, and keywords for this "
            "short-form video."
        )
