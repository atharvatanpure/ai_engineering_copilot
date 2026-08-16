"""
Repository-aware chat agent. Strictly grounds answers in retrieved
code chunks and refuses to speculate when context is insufficient.
"""
from dataclasses import dataclass

from database import models
from rag.retriever import retrieve_relevant_chunks
from services.llm.base import LLMError
from services.llm.provider import get_llm_provider

_INSUFFICIENT_CONTEXT_MESSAGE = (
    "I couldn't find enough information in the repository to answer that confidently."
)

_SYSTEM_PROMPT = """You are an AI engineering assistant answering questions about a \
specific, indexed GitHub repository. You must answer ONLY using the provided code \
context below. Do not use outside knowledge about libraries, frameworks, or the \
repository's likely purpose beyond what the context shows.

Rules:
- If the context does not contain enough information to answer confidently, respond \
EXACTLY with: "I couldn't find enough information in the repository to answer that confidently."
- Never invent file paths, function names, or behavior that is not shown in the context.
- Reference specific files and functions from the context when relevant.
- Keep answers concise and technical, written for a software engineer.
"""


@dataclass
class ChatAnswer:
    answer: str
    sources: list[dict]
    grounded: bool


def answer_question(repository: models.Repository, question: str) -> ChatAnswer:
    retrieval = retrieve_relevant_chunks(repository.id, question, top_k=8)

    if not retrieval.chunks:
        return ChatAnswer(answer=_INSUFFICIENT_CONTEXT_MESSAGE, sources=[], grounded=False)

    context_blocks = []
    sources = []
    for chunk in retrieval.chunks:
        meta = chunk.metadata
        context_blocks.append(
            f"### {meta.get('file_path')} (lines {meta.get('start_line')}-{meta.get('end_line')}, "
            f"symbol: {meta.get('symbol') or 'n/a'})\n```{meta.get('language') or ''}\n{chunk.text}\n```"
        )
        sources.append(
            {
                "file_path": meta.get("file_path"),
                "start_line": meta.get("start_line"),
                "end_line": meta.get("end_line"),
                "symbol": meta.get("symbol"),
                "snippet": meta.get("snippet"),
            }
        )

    prompt = (
        f"Repository: {repository.owner}/{repository.name}\n\n"
        f"Retrieved code context:\n\n" + "\n\n".join(context_blocks) +
        f"\n\nQuestion: {question}\n\nAnswer:"
    )

    provider = get_llm_provider()
    try:
        answer = provider.generate(prompt, system=_SYSTEM_PROMPT, max_tokens=800)
    except LLMError as exc:
        return ChatAnswer(
            answer=f"The AI provider returned an error while answering: {exc}",
            sources=[],
            grounded=False,
        )

    grounded = _INSUFFICIENT_CONTEXT_MESSAGE not in answer
    return ChatAnswer(answer=answer.strip(), sources=sources if grounded else [], grounded=grounded)
