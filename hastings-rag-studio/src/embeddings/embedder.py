"""
Embedding model wrapper for Hastings RAG Studio.

Wraps sentence-transformers to generate 384-dimensional embeddings.
Uses Streamlit's cache_resource so the model loads only once per session.
"""

from __future__ import annotations

import streamlit as st
from sentence_transformers import SentenceTransformer

from src.config import config


@st.cache_resource(show_spinner="Loading embedding model…")
def get_model() -> SentenceTransformer:
    """Return the embedding model, loading it once and caching it."""
    return SentenceTransformer(config.embedding_model)


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of strings to embed.
        batch_size: Number of texts to embed per batch.

    Returns:
        List of embedding vectors (each a list of 384 floats).
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 50,
        convert_to_numpy=True,
        normalize_embeddings=True,  # unit vectors for cosine similarity
    )
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """
    Generate an embedding for a single query string.

    Args:
        text: The query text.

    Returns:
        A single embedding vector (384 floats).
    """
    model = get_model()
    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embedding.tolist()
