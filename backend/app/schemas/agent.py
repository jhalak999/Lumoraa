"""
Structured output contracts for every agent in the pipeline.

These are used as the `output_type` for Pydantic AI agents, meaning the LLM
provider is instructed (via tool-calling / JSON mode) to return data that
validates against these models directly. This is what makes the multi-agent
pipeline reliable in production instead of "hope the model returns valid
JSON and pray during json.loads()".
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchFact(BaseModel):
    claim: str = Field(description="A single fact or insight relevant to the topic.")
    supporting_detail: str = Field(description="One or two sentences of supporting context.")
    relevance_score: float = Field(ge=0, le=1, description="How central this is to the topic, 0-1.")


class ResearchOutput(BaseModel):
    topic_summary: str = Field(description="2-3 sentence synthesis of the topic.")
    key_facts: list[ResearchFact] = Field(min_length=3, max_length=12)
    suggested_angle: str = Field(
        description="The most compelling narrative angle for a short-form video on this topic."
    )
    target_audience: str


class ScriptLine(BaseModel):
    order: int
    speaker_note: str = Field(description="Delivery guidance, e.g. 'energetic', 'pause for effect'.")
    text: str = Field(description="The exact narration text to be spoken aloud.")


class ScriptOutput(BaseModel):
    hook: str = Field(description="The first line — must grab attention in under 3 seconds when read aloud.")
    lines: list[ScriptLine] = Field(min_length=1)
    call_to_action: str
    estimated_duration_seconds: int
    word_count: int


class Scene(BaseModel):
    order: int
    script_line_orders: list[int] = Field(
        description="Which ScriptLine.order values this scene visually covers."
    )
    visual_description: str = Field(description="What should be shown on screen, in plain language.")
    duration_seconds: float
    camera_motion: str = Field(description="e.g. 'slow zoom in', 'static', 'pan left'.")


class ScenePlanOutput(BaseModel):
    scenes: list[Scene] = Field(min_length=1)
    total_duration_seconds: float
    visual_style: str = Field(description="Overall art direction, e.g. 'cinematic realism, warm tones'.")


class ImagePrompt(BaseModel):
    scene_order: int
    prompt: str = Field(description="Full text-to-image prompt, self-contained, no scene numbers inside it.")
    negative_prompt: str = Field(default="", description="What to avoid generating.")
    aspect_ratio: str = Field(default="9:16")


class ImagePromptOutput(BaseModel):
    prompts: list[ImagePrompt] = Field(min_length=1)
    style_reference: str = Field(description="Shared style descriptor appended across all prompts for consistency.")


class SeoOutput(BaseModel):
    titles: list[str] = Field(min_length=3, max_length=5, description="Candidate titles, strongest first.")
    description: str = Field(max_length=5000)
    hashtags: list[str] = Field(min_length=3, max_length=15)
    keywords: list[str] = Field(min_length=3, max_length=20)
