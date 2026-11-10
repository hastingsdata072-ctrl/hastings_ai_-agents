"""
Text chunking for Hastings RAG Studio.

Splits extracted text into overlapping chunks suitable for embedding.
Preserves page number metadata from the source pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.config import config
from src.ingestion.extractor import ExtractedPage


@dataclass
class Chunk:
    """A single text chunk ready for embedding."""
    chunk_index: int
    content: str
    page_number: Optional[int]


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Split text into overlapping chunks by character count.

    Tries to break at sentence or word boundaries to avoid cutting
    mid-sentence. Falls back to hard character splits if needed.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            # Last chunk — take whatever remains
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Try to break at a sentence boundary (. ! ?)
        break_pos = -1
        for sep in (". ", "! ", "? ", "\n\n", "\n"):
            pos = text.rfind(sep, start, end)
            if pos > start:
                break_pos = pos + len(sep)
                break

        # Fall back to word boundary
        if break_pos == -1:
            pos = text.rfind(" ", start, end)
            break_pos = pos + 1 if pos > start else end

        chunk = text[start:break_pos].strip()
        if chunk:
            chunks.append(chunk)

        # Move start back by overlap amount
        start = break_pos - chunk_overlap
        if start < 0:
            start = 0

    return chunks


def chunk_pages(
    pages: list[ExtractedPage],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    """
    Split a list of extracted pages into chunks.

    Args:
        pages: Extracted pages from the document.
        chunk_size: Max characters per chunk (defaults to config value).
        chunk_overlap: Characters of overlap between chunks (defaults to config).

    Returns:
        Ordered list of Chunk objects with index and page metadata.
    """
    size = chunk_size or config.chunk_size
    overlap = chunk_overlap or config.chunk_overlap

    all_chunks: list[Chunk] = []
    chunk_index = 0

    for page in pages:
        text_chunks = _split_text(page.text, size, overlap)
        for text in text_chunks:
            all_chunks.append(
                Chunk(
                    chunk_index=chunk_index,
                    content=text,
                    page_number=page.page_number,
                )
            )
            chunk_index += 1

    return all_chunks
