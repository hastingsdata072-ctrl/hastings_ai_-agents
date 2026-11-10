"""
Hybrid retrieval for Hastings RAG Studio.

Combines vector search and BM25 keyword search using
Reciprocal Rank Fusion (RRF) to merge the two ranked lists.

RRF score = sum of 1 / (k + rank) for each list where k=60 (standard).
Higher score = more relevant.
"""

from __future__ import annotations

from typing import Any

from src.config import config
from src.embeddings.embedder import embed_query
from src.db.connection import get_connection
from src.db.queries import vector_search
from src.retrieval.bm25_search import bm25_search


# RRF constant — 60 is the standard value from the original paper
_RRF_K = 60


def reciprocal_rank_fusion(
    vector_results: list[dict[str, Any]],
    bm25_results: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.

    Args:
        vector_results: Chunks ranked by vector similarity.
        bm25_results: Chunks ranked by BM25 score.
        top_k: Number of results to return.

    Returns:
        Merged and re-ranked list of chunks with rrf_score added.
    """
    scores: dict[int, float] = {}
    chunk_map: dict[int, dict[str, Any]] = {}

    # Score from vector ranking
    for rank, chunk in enumerate(vector_results, start=1):
        cid = chunk["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank)
        chunk_map[cid] = chunk

    # Score from BM25 ranking
    for rank, chunk in enumerate(bm25_results, start=1):
        cid = chunk["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank)
        if cid not in chunk_map:
            chunk_map[cid] = chunk

    # Sort by combined RRF score
    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    results = []
    for cid in sorted_ids[:top_k]:
        chunk = dict(chunk_map[cid])
        chunk["rrf_score"] = scores[cid]
        # Use rrf_score as the display score
        chunk["score"] = round(scores[cid], 4)
        results.append(chunk)

    return results


def hybrid_retrieve(
    kb_id: int,
    question: str,
    top_k: int | None = None,
    vector_k_multiplier: int = 3,
) -> list[dict[str, Any]]:
    """
    Retrieve chunks using hybrid vector + BM25 search with RRF fusion.

    Fetches more candidates than needed from each source, then merges
    them with RRF and returns the top_k best results.

    Args:
        kb_id: Knowledge base to search.
        question: The user question.
        top_k: Final number of results (defaults to config.top_k).
        vector_k_multiplier: Fetch this many × top_k from each source.

    Returns:
        Merged ranked list of chunk dicts.
    """
    k = top_k or config.top_k
    fetch_k = k * vector_k_multiplier

    # Vector search
    query_embedding = embed_query(question)
    with get_connection() as conn:
        vector_results = vector_search(conn, kb_id, query_embedding, fetch_k)

    # BM25 search
    bm25_results = bm25_search(kb_id, question, fetch_k)

    # Merge with RRF
    return reciprocal_rank_fusion(vector_results, bm25_results, k)
