"""
Database query functions for Hastings RAG Studio.

All database operations live here — creating knowledge bases, storing
documents and chunks, retrieval, and deletion.
"""

from __future__ import annotations

from typing import Any, Optional

import psycopg

from src.ingestion.chunker import Chunk


# ── Knowledge Bases ───────────────────────────────────────────────────────────

def create_knowledge_base(
    conn: psycopg.Connection,
    name: str,
    description: str = "",
) -> dict[str, Any]:
    """Create a new knowledge base and return its record."""
    row = conn.execute(
        """
        INSERT INTO knowledge_bases (name, description)
        VALUES (%s, %s)
        RETURNING id, name, description, created_at
        """,
        (name, description),
    ).fetchone()
    return dict(row)


def list_knowledge_bases(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """Return all knowledge bases ordered by creation date."""
    rows = conn.execute(
        "SELECT id, name, description, created_at FROM knowledge_bases ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_knowledge_base(
    conn: psycopg.Connection, kb_id: int
) -> Optional[dict[str, Any]]:
    """Return a single knowledge base by ID, or None if not found."""
    row = conn.execute(
        "SELECT id, name, description, created_at FROM knowledge_bases WHERE id = %s",
        (kb_id,),
    ).fetchone()
    return dict(row) if row else None


def delete_knowledge_base(conn: psycopg.Connection, kb_id: int) -> None:
    """Delete a knowledge base and cascade-delete all documents and chunks."""
    conn.execute("DELETE FROM knowledge_bases WHERE id = %s", (kb_id,))


# ── Documents ─────────────────────────────────────────────────────────────────

def document_exists(
    conn: psycopg.Connection, kb_id: int, content_hash: str
) -> bool:
    """Return True if a document with this hash already exists in the KB."""
    row = conn.execute(
        "SELECT id FROM documents WHERE kb_id = %s AND content_hash = %s",
        (kb_id, content_hash),
    ).fetchone()
    return row is not None


def create_document(
    conn: psycopg.Connection,
    kb_id: int,
    filename: str,
    file_type: str,
    content_hash: str,
    page_count: int,
) -> dict[str, Any]:
    """Insert a document record and return it."""
    row = conn.execute(
        """
        INSERT INTO documents (kb_id, filename, file_type, content_hash, page_count)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, kb_id, filename, file_type, content_hash, page_count, created_at
        """,
        (kb_id, filename, file_type, content_hash, page_count),
    ).fetchone()
    return dict(row)


def list_documents(
    conn: psycopg.Connection, kb_id: int
) -> list[dict[str, Any]]:
    """Return all documents in a knowledge base."""
    rows = conn.execute(
        """
        SELECT d.id, d.filename, d.file_type, d.page_count, d.created_at,
               COUNT(c.id) AS chunk_count
        FROM documents d
        LEFT JOIN chunks c ON c.document_id = d.id
        WHERE d.kb_id = %s
        GROUP BY d.id
        ORDER BY d.created_at DESC
        """,
        (kb_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def delete_document(conn: psycopg.Connection, document_id: int) -> None:
    """Delete a document and all its chunks."""
    conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))


# ── Chunks ────────────────────────────────────────────────────────────────────

def store_chunks(
    conn: psycopg.Connection,
    document_id: int,
    kb_id: int,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> int:
    """
    Bulk-insert chunks with their embeddings.

    Args:
        conn: Open database connection.
        document_id: Parent document ID.
        kb_id: Parent knowledge base ID.
        chunks: List of Chunk objects.
        embeddings: Parallel list of embedding vectors.

    Returns:
        Number of chunks inserted.
    """
    if not chunks:
        return 0

    rows = [
        (
            document_id,
            kb_id,
            chunk.chunk_index,
            chunk.content,
            chunk.page_number,
            embeddings[i],
        )
        for i, chunk in enumerate(chunks)
    ]

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (document_id, kb_id, chunk_index, content, page_number, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            rows,
        )
    return len(rows)


def get_chunk_count(
    conn: psycopg.Connection, kb_id: int
) -> int:
    """Return the total number of chunks in a knowledge base."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM chunks WHERE kb_id = %s", (kb_id,)
    ).fetchone()
    return row["n"] if row else 0


# ── Vector retrieval ──────────────────────────────────────────────────────────

def vector_search(
    conn: psycopg.Connection,
    kb_id: int,
    query_embedding: list[float],
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Retrieve the top-k most similar chunks using cosine distance.

    Args:
        conn: Open database connection.
        kb_id: Knowledge base to search within.
        query_embedding: Query vector (384 floats).
        top_k: Number of results to return.

    Returns:
        List of chunk dicts with content, score, filename, page_number.
    """
    rows = conn.execute(
        """
        SELECT
            c.id,
            c.content,
            c.page_number,
            c.chunk_index,
            d.filename,
            1 - (c.embedding <=> %s::vector) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.kb_id = %s
          AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, kb_id, query_embedding, top_k),
    ).fetchall()
    return [dict(r) for r in rows]
