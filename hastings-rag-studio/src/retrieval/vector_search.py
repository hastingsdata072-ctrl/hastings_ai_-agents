"""
Vector search retrieval for Hastings RAG Studio.

Thin orchestration layer that combines the embedder and the DB query.
"""

from __future__ import annotations

from typing import Any

from src.config import config
from src.db.connection import get_connection
from src.db.queries import vector_search
from src.embeddings.embedder import embed_query


def retrieve(
    kb_id: int,
    question: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    Embed a question and retrieve the most relevant chunks.

    Args:
        kb_id: Knowledge base to search.
        question: Natural language question.
        top_k: Number of chunks to return (defaults to config.top_k).

    Returns:
        List of chunk dicts: content, score, filename, page_number.
    """
    k = top_k or config.top_k
    query_embedding = embed_query(question)

    with get_connection() as conn:
        results = vector_search(conn, kb_id, query_embedding, k)

    return results
