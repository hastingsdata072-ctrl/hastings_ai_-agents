"""
Ingestion pipeline for Hastings RAG Studio.

Orchestrates the full upload flow:
  extract → chunk → embed → store
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.db.connection import get_connection
from src.db.queries import (
    create_document,
    document_exists,
    store_chunks,
)
from src.embeddings.embedder import embed_texts
from src.ingestion.chunker import chunk_pages
from src.ingestion.extractor import extract


@dataclass
class IngestionResult:
    """Result of ingesting a single document."""
    success: bool
    filename: str
    message: str
    chunk_count: int = 0
    document_id: int | None = None
    duplicate: bool = False


def ingest_document(
    kb_id: int,
    filename: str,
    file_bytes: bytes,
) -> IngestionResult:
    """
    Run the full ingestion pipeline for a single document.

    Steps:
    1. Extract text (with page numbers for PDFs)
    2. Check for duplicate (SHA-256 hash)
    3. Split into chunks
    4. Generate embeddings in batches
    5. Store document and chunks in the database

    Args:
        kb_id: Target knowledge base ID.
        filename: Original filename (determines extractor).
        file_bytes: Raw file content.

    Returns:
        IngestionResult describing success or failure.
    """
    # ── Step 1: Extract ───────────────────────────────────────────────────────
    try:
        extraction = extract(filename, file_bytes)
    except ValueError as e:
        return IngestionResult(success=False, filename=filename, message=str(e))
    except Exception as e:
        return IngestionResult(
            success=False,
            filename=filename,
            message=f"Extraction failed: {e}",
        )

    if not extraction.pages:
        return IngestionResult(
            success=False,
            filename=filename,
            message="No text could be extracted from this file.",
        )

    # ── Step 2: Duplicate check ───────────────────────────────────────────────
    with get_connection() as conn:
        if document_exists(conn, kb_id, extraction.content_hash):
            return IngestionResult(
                success=False,
                filename=filename,
                message="This file has already been uploaded to this knowledge base.",
                duplicate=True,
            )

    # ── Step 3: Chunk ─────────────────────────────────────────────────────────
    chunks = chunk_pages(extraction.pages)
    if not chunks:
        return IngestionResult(
            success=False,
            filename=filename,
            message="Document produced no chunks after splitting.",
        )

    # ── Step 4: Embed ─────────────────────────────────────────────────────────
    try:
        texts = [c.content for c in chunks]
        embeddings = embed_texts(texts)
    except Exception as e:
        return IngestionResult(
            success=False,
            filename=filename,
            message=f"Embedding failed: {e}",
        )

    # ── Step 5: Store ─────────────────────────────────────────────────────────
    try:
        with get_connection() as conn:
            doc = create_document(
                conn,
                kb_id=kb_id,
                filename=filename,
                file_type=extraction.file_type,
                content_hash=extraction.content_hash,
                page_count=extraction.page_count,
            )
            store_chunks(conn, doc["id"], kb_id, chunks, embeddings)
    except Exception as e:
        return IngestionResult(
            success=False,
            filename=filename,
            message=f"Database storage failed: {e}",
        )

    return IngestionResult(
        success=True,
        filename=filename,
        message=f"Indexed {len(chunks)} chunks from {extraction.page_count} page(s).",
        chunk_count=len(chunks),
        document_id=doc["id"],
    )
