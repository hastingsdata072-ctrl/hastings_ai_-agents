"""
Context compression for Hastings RAG Studio.

Trims retrieved chunks to keep only the sentences most relevant
to the query. Reduces token usage and focuses the LLM on evidence.

Uses a simple sentence-scoring approach with the embedding model
(no extra model downloads needed).
"""

from __future__ import annotations

from typing import Any

import numpy as np


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    va = np.array(a)
    vb = np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def compress_chunks(
    query: str,
    chunks: list[dict[str, Any]],
    max_sentences: int = 5,
    min_chars: int = 100,
) -> list[dict[str, Any]]:
    """
    Compress each chunk by keeping only the most relevant sentences.

    Args:
        query: The user question (used to score sentence relevance).
        chunks: Retrieved chunks to compress.
        max_sentences: Max sentences to keep per chunk.
        min_chars: Don't compress chunks shorter than this.

    Returns:
        Chunks with content replaced by compressed versions.
        Original content preserved in 'original_content'.
    """
    from src.embeddings.embedder import embed_query, embed_texts

    query_embedding = embed_query(query)
    compressed = []

    for chunk in chunks:
        content = chunk["content"]

        # Skip compression for short chunks
        if len(content) < min_chars:
            compressed.append({**chunk, "original_content": content, "compressed": False})
            continue

        # Split into sentences
        import re
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if len(sentences) <= max_sentences:
            compressed.append({**chunk, "original_content": content, "compressed": False})
            continue

        # Score each sentence by similarity to query
        sentence_embeddings = embed_texts(sentences)
        scores = [_cosine(query_embedding, emb) for emb in sentence_embeddings]

        # Keep top sentences, preserving original order
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        top_indices = sorted([i for i, _ in indexed[:max_sentences]])
        kept = " ".join(sentences[i] for i in top_indices)

        compressed.append({
            **chunk,
            "content": kept,
            "original_content": content,
            "compressed": True,
            "sentences_kept": len(top_indices),
            "sentences_total": len(sentences),
        })

    return compressed
