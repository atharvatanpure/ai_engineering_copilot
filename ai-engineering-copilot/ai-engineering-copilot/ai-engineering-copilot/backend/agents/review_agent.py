"""
AI code review agent. Analyzes a pasted diff or a single file's code
for bugs, security issues, performance concerns, maintainability, and
best-practice violations, returning a structured JSON result.
"""
from services.llm.base import LLMError
from services.llm.provider import get_llm_provider

_SCHEMA_HINT = """{
  "summary": "one or two sentence overview of the code's quality",
  "issues": [
    {
      "severity": "critical | high | medium | low | info",
      "category": "bug | security | performance | maintainability | best_practice",
      "file": "filename or null",
      "line": 42,
      "title": "short issue title",
      "description": "what the problem is",
      "recommendation": "how to fix it"
    }
  ]
}"""

_SYSTEM_PROMPT = """You are a senior software engineer performing a thorough code review. \
Analyze the given code or diff for:
- Bugs: logical errors, edge cases, incorrect assumptions.
- Security: injection, unsafe deserialization, secrets, path traversal, auth flaws, etc.
- Performance: unnecessary loops/allocations, N+1 queries, blocking calls, etc.
- Maintainability: poor structure, excessive complexity, unclear naming.
- Best practices: idiomatic usage, error handling, testing gaps.

Only report issues you can actually justify from the given code — do not invent problems \
that aren't present. If the code has no notable issues, return an empty issues array and \
say so in the summary. Respond only with the requested JSON."""


def review_code(*, file_path: str | None, code: str | None, diff: str | None) -> dict:
    content = diff or code or ""
    if not content.strip():
        return {"summary": "No code or diff was provided to review.", "issues": []}

    kind = "diff" if diff else "file"
    prompt = (
        f"Review the following {kind}"
        + (f" ({file_path})" if file_path else "")
        + f":\n\n```\n{content[:20000]}\n```"
    )

    provider = get_llm_provider()
    try:
        result = provider.generate_structured(
            prompt, schema_hint=_SCHEMA_HINT, system=_SYSTEM_PROMPT, max_tokens=2500
        )
    except LLMError as exc:
        return {
            "summary": f"The AI provider returned an error while reviewing this code: {exc}",
            "issues": [],
        }

    result.setdefault("summary", "")
    result.setdefault("issues", [])
    # Backfill missing `file` on issues when we know the target file.
    if file_path:
        for issue in result["issues"]:
            issue.setdefault("file", file_path)
    return result
