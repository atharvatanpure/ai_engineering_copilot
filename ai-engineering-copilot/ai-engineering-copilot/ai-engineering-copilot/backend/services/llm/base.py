"""
Provider-agnostic interface for LLM interactions.

Any concrete provider (OpenAI, Anthropic, a local model, or a mock for
tests) implements this interface so the rest of the application never
depends on a specific vendor SDK.
"""
from abc import ABC, abstractmethod
from typing import Any


class LLMError(Exception):
    """Raised for any provider failure (network, auth, rate limit, etc.)."""


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
        """Generate a free-text completion."""

    @abstractmethod
    def generate_structured(
        self, prompt: str, schema_hint: str, system: str | None = None, max_tokens: int = 2048
    ) -> dict[str, Any]:
        """
        Generate a JSON object conforming to `schema_hint` (a human-readable
        description of the expected JSON shape). Returns a parsed dict.
        Raises LLMError if the response cannot be parsed as JSON.
        """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
