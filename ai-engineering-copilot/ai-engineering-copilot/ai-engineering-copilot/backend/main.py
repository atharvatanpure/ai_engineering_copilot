import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import chat, repositories, review
from config import get_settings
from database.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_engineering_copilot")

settings = get_settings()

app = FastAPI(
    title="AI Engineering Copilot",
    description="Repository-aware AI developer assistant: code-aware RAG chat and AI code review.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
    except Exception as exc:  # database not reachable at boot
        logger.error("Database initialization failed: %s", exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(repositories.router)
app.include_router(chat.router)
app.include_router(review.router)
