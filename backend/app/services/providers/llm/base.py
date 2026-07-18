"""
Abstract LLM provider interface.

Every concrete LLM client (OpenRouter today, potentially direct
Anthropic/OpenAI later) implements this so Pydantic AI agents can be
configured against a uniform model interface without the agent code caring
which vendor is behind it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Return raw text completion."""
        raise NotImplementedError

    @abstractmethod
    def as_pydantic_ai_model(self, model_name: str) -> Any:
        """Return a model object usable as the `model=` arg of a pydantic_ai.Agent."""
        raise NotImplementedError
