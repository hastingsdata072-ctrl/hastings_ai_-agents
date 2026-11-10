"""
Configuration loader for Hastings RAG Studio.

Reads all settings from the .env file and exposes them as a typed Config object.
Raises a clear error if any required variable is missing.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
load_dotenv()


def _require(key: str) -> str:
    """Return the value of an environment variable or raise a clear error."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is missing or empty. "
            f"Copy .env.example to .env and fill in the value."
        )
    return value


def _optional_int(key: str, default: int) -> int:
    """Return an integer environment variable, or a default if not set."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise EnvironmentError(
            f"Environment variable '{key}' must be an integer, got: '{raw}'"
        )


@dataclass(frozen=True)
class Config:
    """Immutable application configuration."""

    groq_api_key: str
    groq_model: str
    database_url: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int


def load_config() -> Config:
    """Load and validate all configuration from environment variables."""
    return Config(
        groq_api_key=_require("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        database_url=_require("DATABASE_URL"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        chunk_size=_optional_int("CHUNK_SIZE", 1000),
        chunk_overlap=_optional_int("CHUNK_OVERLAP", 150),
        top_k=_optional_int("TOP_K", 5),
    )


# Module-level singleton — import this in other modules
config = load_config()
