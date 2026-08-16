"""
Thin wrapper around the configured LLM provider's embed() method,
batching requests to stay within provider limits.
"""
from services.llm.provider import get_llm_provider

_BATCH_SIZE = 64


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    provider = get_llm_provider()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i:i + _BATCH_SIZE]
        vectors.extend(provider.embed(batch))
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
