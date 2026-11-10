"""
Health-check module for Hastings RAG Studio.

Runs live checks against every critical component and returns a
structured result dict. Nothing is hardcoded — every status reflects
the real state of the system at call time.
"""

from __future__ import annotations

import os
from typing import TypedDict

from src.config import config


class CheckResult(TypedDict):
    status: str   # "ok" or "error"
    message: str


HealthReport = dict[str, CheckResult]


def check_database() -> CheckResult:
    """Verify that the database is reachable and responds to a query."""
    try:
        from src.db.connection import get_connection
        with get_connection() as conn:
            row = conn.execute("SELECT version() AS v").fetchone()
            version = row["v"] if row else "unknown"
        return {"status": "ok", "message": f"Connected. {version}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def check_pgvector() -> CheckResult:
    """Verify that the pgvector extension is installed and active."""
    try:
        from src.db.connection import get_connection
        with get_connection() as conn:
            # Check the extension is available in this PostgreSQL build
            available = conn.execute(
                "SELECT default_version FROM pg_available_extensions "
                "WHERE name = 'vector';"
            ).fetchone()

            if not available:
                return {
                    "status": "error",
                    "message": "pgvector extension is not available in this PostgreSQL build.",
                }

            # Check the extension is actually enabled in this database
            active = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
            ).fetchone()

            if not active:
                return {
                    "status": "error",
                    "message": (
                        f"pgvector {available['default_version']} is available "
                        "but not yet enabled. Run init_db to enable it."
                    ),
                }

            return {
                "status": "ok",
                "message": f"pgvector {active['extversion']} is active.",
            }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def check_embedding_model() -> CheckResult:
    """Load the embedding model and encode a test string to confirm it works."""
    try:
        from src.embeddings.embedder import get_model
        model = get_model()
        embedding = model.encode("health check")
        dim = len(embedding)
        return {
            "status": "ok",
            "message": f"Model '{config.embedding_model}' loaded. Output dimension: {dim}.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def check_groq_key() -> CheckResult:
    """Verify that a Groq API key is configured (does not call the API)."""
    key = config.groq_api_key
    if not key:
        return {"status": "error", "message": "GROQ_API_KEY is not set."}
    if not key.startswith("gsk_"):
        return {
            "status": "error",
            "message": "GROQ_API_KEY is set but does not look like a valid Groq key (expected 'gsk_' prefix).",
        }
    # Show only a short prefix so the key is never exposed in the UI
    preview = key[:12] + "..." + key[-4:]
    return {
        "status": "ok",
        "message": f"API key present ({preview}). Model: {config.groq_model}.",
    }


def run_health_checks() -> HealthReport:
    """
    Run all health checks and return a combined report.

    Returns:
        A dict with keys 'database', 'pgvector', 'embedding_model', 'groq_key'.
        Each value has 'status' ("ok" or "error") and 'message'.
    """
    return {
        "database": check_database(),
        "pgvector": check_pgvector(),
        "embedding_model": check_embedding_model(),
        "groq_key": check_groq_key(),
    }
