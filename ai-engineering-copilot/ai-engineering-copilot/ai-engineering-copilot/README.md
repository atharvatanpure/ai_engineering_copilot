# AI Engineering Copilot

An AI-powered developer assistant that imports a public GitHub repository,
indexes it with a code-aware RAG pipeline, answers questions about the
codebase with source citations, and runs a structured AI code review.

> "An AI engineering assistant that understands my entire codebase."

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [RAG pipeline](#rag-pipeline)
- [Setup](#setup)
- [Environment variables](#environment-variables)
- [Running locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [API documentation](#api-documentation)
- [Example queries](#example-queries)
- [Testing](#testing)
- [Limitations](#limitations)
- [Future improvements](#future-improvements)
- [Engineering decisions](#engineering-decisions)

---

## Features

- **Repository import** — paste a public GitHub URL; the backend validates it,
  clones it (shallow, depth 1), scans the tree, and ignores build artifacts,
  binaries, and generated files.
- **Code-aware RAG indexing** — structure-aware chunking (Python AST, heuristic
  declaration-boundary detection for other languages), embeddings, and storage
  in ChromaDB.
- **Repository-aware chat** — ask natural-language questions; answers are
  generated strictly from retrieved code context, never from general
  knowledge, with an explicit "I couldn't find enough information…" fallback.
- **Source citations** — every answer lists the exact files and line ranges it
  used; clicking a citation opens the code inline.
- **AI code review** — paste a diff/snippet or pick a repository file; get a
  structured report of bugs, security issues, performance concerns,
  maintainability problems, and best-practice suggestions with severities.
- **Dashboard** — repository stats (files, LOC, indexed chunks, languages),
  quick actions, and index status.

## Architecture

```
┌────────────┐     ┌──────────────┐     ┌───────────────────────┐
│  Next.js   │────▶│   FastAPI    │────▶│  PostgreSQL            │
│  frontend  │◀────│   backend    │◀────│  (repos, chats, review)│
└────────────┘     └──────┬───────┘     └───────────────────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
        ┌──────────┐ ┌───────────┐ ┌───────────┐
        │  GitHub  │ │  ChromaDB │ │    LLM    │
        │  (clone) │ │  (vectors)│ │ (OpenAI / │
        └──────────┘ └───────────┘ │ Anthropic)│
                                    └───────────┘
```

Backend layout:

```
backend/
├── api/            # FastAPI routers (repositories, chat, review)
├── agents/         # chat_agent (RAG Q&A), review_agent (structured review)
├── rag/            # chunker, embeddings, vector_store, retriever, indexer
├── services/       # github (clone), repository (scan), llm/ (provider abstraction)
├── database/       # SQLAlchemy models, Pydantic schemas, session management
├── utils/          # security (path traversal / URL validation), ignore rules
├── config.py       # env-driven settings
└── main.py         # FastAPI app, CORS, error handlers
```

## Tech stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy
- **Database**: PostgreSQL
- **Vector store**: ChromaDB (swappable — see [engineering decisions](#engineering-decisions))
- **LLM**: pluggable — OpenAI, Anthropic, or a dependency-free mock provider for local dev/tests

## RAG pipeline

```
GitHub Repository
      │  git clone --depth 1
      ▼
File Scanner            (services/repository.py — ignores binaries, node_modules,
                          .git, __pycache__, dist/build, generated/minified files)
      ▼
Code Parser / Chunker   (rag/chunker.py — Python AST; heuristic declaration
                          boundaries for JS/TS/Go/Java/Rust/etc.; fixed-window
                          fallback with overlap for unstructured text)
      ▼
Embeddings              (rag/embeddings.py — batched calls to the configured
                          LLM provider's embed())
      ▼
Vector Database         (rag/vector_store.py — ChromaDB, one collection per
                          repository)
      ▼
Retriever               (rag/retriever.py — embeds the question, fetches
                          top-k chunks, flags whether results are relevant
                          enough to answer confidently)
      ▼
LLM                     (agents/chat_agent.py — grounded generation with a
                          strict refusal fallback when context is insufficient)
```

Every chunk carries metadata: `repository`, `file_path`, `language`,
`start_line`, `end_line`, `symbol`.

## Setup

**Prerequisites**: Python 3.11+, Node.js 20+, PostgreSQL 16 (or Docker),
`git` on PATH.

```bash
git clone <this-repo>
cd ai-engineering-copilot
cp .env.example .env   # then fill in LLM_API_KEY, etc.
```

## Environment variables

See `.env.example` for the full list. The important ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `LLM_PROVIDER` | `openai` \| `anthropic` \| `mock` |
| `LLM_API_KEY` | API key for the chosen provider (unused for `mock`) |
| `LLM_MODEL` | Chat/completion model name |
| `EMBEDDING_MODEL` | Embedding model name (OpenAI provider) |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB connection |
| `MAX_REPO_SIZE_MB` / `MAX_INDEXED_FILES` | Import limits |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend |

Never hard-code API keys — they are only ever read from the environment.

## Running locally

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Running with Docker

```bash
docker compose up --build
```

This starts PostgreSQL, ChromaDB, the FastAPI backend (port 8000), and the
Next.js frontend (port 3000).

## API documentation

Interactive docs are auto-generated by FastAPI at `/docs` once the backend
is running (e.g. http://localhost:8000/docs).

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/repositories` | Import a repository (clone + scan) |
| `GET` | `/api/repositories` | List repositories |
| `GET` | `/api/repositories/{id}` | Repository detail |
| `POST` | `/api/repositories/{id}/index` | (Re-)index a repository |
| `GET` | `/api/repositories/{id}/files` | List indexed files |
| `GET` | `/api/repositories/{id}/files/{path}` | Fetch file content |
| `POST` | `/api/repositories/{id}/chat` | Ask a question (RAG) |
| `POST` | `/api/review` | Run AI code review on a diff/file |

## Example queries

- "How does authentication work in this project?"
- "Where is the database connection configured?"
- "What happens if the API rate limit is exceeded?"
- "Which functions call `authenticate_user`?"

If the retrieved context doesn't cover the question, the assistant responds:
> "I couldn't find enough information in the repository to answer that confidently."

## Testing

```bash
pip install -r backend/requirements.txt
LLM_PROVIDER=mock DATABASE_URL=sqlite:///:memory: pytest
```

The suite covers GitHub URL validation, repository scanning/ignore rules,
chunking (including malformed Python source), the embedding pipeline,
retrieval logic, review JSON schema validation, and full API integration
tests (import → index → chat, and the review endpoint) using SQLite and a
mock LLM provider — no external services or API keys required. 34 tests,
all passing as of this build; run the command above to reproduce.

## Limitations

- Only public GitHub repositories are supported (no OAuth/private repos yet).
- The mock LLM provider (default when no API key is set) returns placeholder
  answers — real chat/review quality requires a configured OpenAI or
  Anthropic key.
- Chunking heuristics for non-Python languages are regex-based, not full
  parsers; unusual formatting can produce coarser chunks.
- No background job queue — cloning/indexing runs synchronously within the
  request (fine for MVP-sized repositories, not ideal for very large ones).
- No authentication/multi-tenancy — anyone with access to the deployment can
  see all imported repositories.

## Future improvements

Architected for, not yet implemented: GitHub OAuth, PR integration and
webhooks, automatic PR reviews, multi-agent workflows, automated test
generation, documentation/architecture-diagram generation, dependency
vulnerability analysis, repository comparison, GitHub Actions integration,
a Redis-backed background job queue, streaming LLM responses, and user
accounts.

## Engineering decisions

- **ChromaDB for the MVP vector store, behind an interface.** `rag/vector_store.py`
  defines an abstract `VectorStore`; `ChromaVectorStore` is the only
  implementation today. Swapping to Qdrant later means implementing that one
  interface and changing `get_vector_store()` — nothing else in the app
  depends on Chroma directly.
- **Pluggable LLM provider.** `services/llm/base.py` defines `generate()`,
  `generate_structured()`, and `embed()`; OpenAI and Anthropic
  implementations live behind it, plus a dependency-free mock used in tests
  and for running the app without an API key.
- **AST-based chunking for Python, heuristics elsewhere.** Python's `ast`
  module gives exact function/class boundaries. Other languages use
  regex-based declaration detection (a real tree-sitter integration would be
  the natural next step) with a fixed-window fallback so every file still
  gets reasonably-sized, overlapping chunks.
- **Strict grounding in chat.** The system prompt forbids answering from
  outside knowledge and mandates the literal refusal string when retrieved
  context is insufficient; the backend also treats that string as a signal
  to omit (possibly misleading) source citations.
- **Untrusted repository content.** Cloned repository code is only ever read
  as text — never executed, imported, or evaluated. `git clone` is the only
  subprocess invoked, with `--depth 1`, a timeout, and `GIT_TERMINAL_PROMPT=0`
  so a private/missing repo fails fast instead of hanging on a credential
  prompt. File reads are bounded by `safe_join()` to prevent path traversal,
  and per-file/repo size limits cap what gets indexed.
