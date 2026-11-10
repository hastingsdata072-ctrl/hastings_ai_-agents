"""
BM25 keyword search for Hastings RAG Studio.

Loads all chunks for a knowledge base and runs BM25 ranking
using the rank-bm25 library. Used as the keyword leg of hybrid retrieval.
"""

from __future__ import annotations

from typing import Any

from rank_bm25 import BM25Okapi

from src.db.connection import get_connection


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()


def bm25_search(
    kb_id: int,
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Run BM25 keyword search over all chunks in a knowledge base.

    Args:
        kb_id: Knowledge base to search.
        query: The search query.
        top_k: Number of results to return.

    Returns:
        List of chunk dicts with content, filename, page_number, and bm25_score.
    """
    # Load all chunks for this KB
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.content, c.page_number, c.chunk_index, d.filename
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.kb_id = %s
            ORDER BY c.id
            """,
            (kb_id,),
        ).fetchall()

    if not rows:
        return []

    chunks = [dict(r) for r in rows]
    corpus = [_tokenize(c["content"]) for c in chunks]
    bm25 = BM25Okapi(corpus)

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    # Attach scores and sort
    # Also set a normalised 'score' key for consistency with vector search results
    max_score = float(max(scores)) if scores.max() > 0 else 1.0
    for i, chunk in enumerate(chunks):
        raw = float(scores[i])
        chunk["bm25_score"] = raw
        chunk["score"] = round(raw / max_score, 4)  # Normalised 0–1

    ranked = sorted(chunks, key=lambda x: x["bm25_score"], reverse=True)
    return ranked[:top_k]
