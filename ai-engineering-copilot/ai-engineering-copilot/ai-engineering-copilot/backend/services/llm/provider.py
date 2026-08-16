"""
Concrete LLM provider implementations and a factory function that picks
one based on config.llm_provider. Swapping providers never requires
touching agents/ or rag/ — they only depend on BaseLLMProvider.
"""
import hashlib
import json
import re
from functools import lru_cache
from typing import Any

from config import get_settings
from services.llm.base import BaseLLMProvider, LLMError

settings = get_settings()


def _extract_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from a model response."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model did not return valid JSON: {exc}") from exc
    raise LLMError("Model response contained no JSON object.")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str, embedding_model: str):
        from openai import OpenAI  # imported lazily so the dependency is optional

        if not api_key:
            raise LLMError("LLM_API_KEY is not set for the OpenAI provider.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.embedding_model = embedding_model

    def generate(self, prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=max_tokens, temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise LLMError(f"OpenAI generate() failed: {exc}") from exc

    def generate_structured(
        self, prompt: str, schema_hint: str, system: str | None = None, max_tokens: int = 2048
    ) -> dict[str, Any]:
        full_system = (system or "") + (
            f"\n\nRespond ONLY with a single valid JSON object matching this shape, "
            f"with no markdown fences and no commentary:\n{schema_hint}"
        )
        raw = self.generate(prompt, system=full_system, max_tokens=max_tokens)
        return _extract_json(raw)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.embeddings.create(model=self.embedding_model, input=texts)
            return [item.embedding for item in response.data]
        except Exception as exc:
            raise LLMError(f"OpenAI embed() failed: {exc}") from exc


class AnthropicProvider(BaseLLMProvider):
    """
    Uses Claude for generation. Embeddings still require a dedicated
    embedding model/provider (Anthropic does not serve one), so this
    provider falls back to a local hash-based embedding unless a
    proper embedding provider is configured separately.
    """

    def __init__(self, api_key: str, model: str):
        import anthropic

        if not api_key:
            raise LLMError("LLM_API_KEY is not set for the Anthropic provider.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self._fallback_embedder = HashEmbeddingProvider()

    def generate(self, prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in response.content if hasattr(block, "text"))
        except Exception as exc:
            raise LLMError(f"Anthropic generate() failed: {exc}") from exc

    def generate_structured(
        self, prompt: str, schema_hint: str, system: str | None = None, max_tokens: int = 2048
    ) -> dict[str, Any]:
        full_system = (system or "") + (
            f"\n\nRespond ONLY with a single valid JSON object matching this shape, "
            f"with no markdown fences and no commentary:\n{schema_hint}"
        )
        raw = self.generate(prompt, system=full_system, max_tokens=max_tokens)
        return _extract_json(raw)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._fallback_embedder.embed(texts)


class HashEmbeddingProvider:
    """
    Deterministic, dependency-free embedding fallback used by the mock
    provider and as an Anthropic fallback. NOT semantically meaningful —
    intended only to keep the pipeline runnable without external keys.
    Swap in a real embedding provider (OpenAI, Cohere, local
    sentence-transformers) for real semantic retrieval quality.
    """

    DIM = 256

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vec = [0.0] * self.DIM
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower())
            for token in tokens:
                idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.DIM
                vec[idx] += 1.0
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


class MockLLMProvider(BaseLLMProvider):
    """Used for tests / local dev without any API key."""

    def __init__(self):
        self._embedder = HashEmbeddingProvider()

    def generate(self, prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
        return "I couldn't find enough information in the repository to answer that confidently."

    def generate_structured(
        self, prompt: str, schema_hint: str, system: str | None = None, max_tokens: int = 2048
    ) -> dict[str, Any]:
        return {"summary": "Mock review — configure LLM_API_KEY for real analysis.", "issues": []}

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.embed(texts)


@lru_cache
def get_llm_provider() -> BaseLLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings.llm_api_key, settings.llm_model, settings.embedding_model)
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(settings.llm_api_key, settings.llm_model)
    return MockLLMProvider()
