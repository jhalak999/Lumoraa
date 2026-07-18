"""
Base class for all Pydantic AI-powered agents in the Lumora pipeline.

Each concrete agent (ResearchAgent, ScriptAgent, ScenePlannerAgent,
ImagePromptAgent, SeoAgent) subclasses `BaseLumoraAgent`, declares:
  - `output_schema`: the Pydantic model the LLM must return
  - `system_prompt`: role + instructions
  - `model_name`: which OpenRouter model to use for this task

...and implements `build_user_prompt(**kwargs)`. This keeps prompt
engineering localized per-agent while sharing retry/validation/error
handling logic in one place (SOLID: single responsibility + open/closed —
new agents extend this base rather than modifying shared logic).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent

from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.services.providers.llm.openrouter_client import get_openrouter_provider

TOutput = TypeVar("TOutput", bound=BaseModel)

logger = get_logger(__name__)


class BaseLumoraAgent(ABC, Generic[TOutput]):
    output_schema: type[TOutput]
    system_prompt: str
    model_name: str
    agent_label: str = "agent"

    def __init__(self) -> None:
        provider = get_openrouter_provider()
        model = provider.as_pydantic_ai_model(self.model_name)
        self._agent: Agent[None, TOutput] = Agent(
            model=model,
            output_type=self.output_schema,
            system_prompt=self.system_prompt,
            retries=2,
        )

    @abstractmethod
    def build_user_prompt(self, **kwargs) -> str:
        """Construct the task-specific user prompt from pipeline context."""
        raise NotImplementedError

    async def run(self, **kwargs) -> TOutput:
        prompt = self.build_user_prompt(**kwargs)
        logger.info("Running %s | prompt_chars=%d", self.agent_label, len(prompt))
        try:
            result = await self._agent.run(prompt)
            return result.output
        except Exception as exc:  # noqa: BLE001
            logger.error("%s failed: %s", self.agent_label, exc)
            raise AgentExecutionError(
                f"{self.agent_label} failed to produce a valid result.",
                details={"underlying_error": str(exc)},
            ) from exc
