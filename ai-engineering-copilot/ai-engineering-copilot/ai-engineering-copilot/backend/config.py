"""
Centralized application configuration.

All configuration is sourced from environment variables so that no
secrets or environment-specific values are ever hard-coded. See
.env.example at the project root for the full list of variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql+psycopg2://copilot:copilot@localhost:5432/copilot"

    # --- LLM provider ---
    llm_provider: str = "openai"  # "openai" | "anthropic" | "mock"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # --- Vector store (ChromaDB) ---
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = "./data/chroma"

    # --- Repository storage / limits ---
    repo_storage_dir: str = "./data/repositories"
    max_repo_size_mb: int = 250
    max_indexed_files: int = 3000
    max_file_size_kb: int = 500
    clone_timeout_seconds: int = 120

    # --- Chunking ---
    max_chunk_lines: int = 120
    chunk_overlap_lines: int = 10

    # --- App ---
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
