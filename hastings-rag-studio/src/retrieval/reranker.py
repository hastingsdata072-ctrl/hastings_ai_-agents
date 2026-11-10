"""
Cross-encoder reranking for Hastings RAG Studio.

Uses a sentence-transformers cross-encoder to rerank retrieved chunks.
A cross-encoder scores (query, passage) pairs jointly, giving better
precision than bi-encoder cosine similarity alone.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
  - Fast and accurate for passage reranking
  - ~66 MB download on first use
"""

from __future__ import annotations

from typing import Any

import streamlit as st


@st.cache_resource(show_spinner="Loading reranker model…")
def _get_reranker():
    """Load and cache the cross-encoder model."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    Rerank retrieved chunks using a cross-encoder.

    Args:
        query: The user question.
        chunks: Chunks from initial retrieval (vector or hybrid).
        top_k: Return this many top results. Defaults to all.

    Returns:
        Reranked list with rerank_score added to each chunk.
    """
    if not chunks:
        return chunks

    model = _get_reranker()

    # Build (query, passage) pairs
    pairs = [(query, chunk["content"]) for chunk in chunks]
    scores = model.predict(pairs)

    # Attach scores
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)
        chunk["score"] = round(float(score), 4)

    # Sort by rerank score descending
    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

    return reranked[:top_k] if top_k else reranked
