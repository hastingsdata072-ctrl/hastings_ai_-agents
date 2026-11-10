"""
Document text extraction for Hastings RAG Studio.

Supports PDF (with page numbers), DOCX, TXT, and Markdown.
Returns a list of (page_number, text) tuples for each document.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ExtractedPage:
    """A single page or section of extracted text."""
    page_number: Optional[int]  # None for non-PDF formats
    text: str


@dataclass
class ExtractionResult:
    """Full result of extracting a document."""
    pages: list[ExtractedPage]
    page_count: int
    file_type: str
    content_hash: str  # SHA-256 of the raw file bytes


def _hash_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def extract_pdf(file_bytes: bytes) -> ExtractionResult:
    """Extract text from a PDF file with page numbers."""
    import fitz  # PyMuPDF

    pages: list[ExtractedPage] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    total_pages = len(doc)  # Capture before close — len(doc) returns 0 after close()

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:
            pages.append(ExtractedPage(page_number=page_num + 1, text=text))

    doc.close()
    return ExtractionResult(
        pages=pages,
        page_count=total_pages if pages else 0,
        file_type="pdf",
        content_hash=_hash_bytes(file_bytes),
    )


def extract_docx(file_bytes: bytes) -> ExtractionResult:
    """Extract text from a DOCX file."""
    import io
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text = "\n".join(paragraphs)

    pages = [ExtractedPage(page_number=None, text=full_text)] if full_text else []
    return ExtractionResult(
        pages=pages,
        page_count=1,
        file_type="docx",
        content_hash=_hash_bytes(file_bytes),
    )


def extract_text(file_bytes: bytes) -> ExtractionResult:
    """Extract text from a plain text file."""
    text = file_bytes.decode("utf-8", errors="replace").strip()
    pages = [ExtractedPage(page_number=None, text=text)] if text else []
    return ExtractionResult(
        pages=pages,
        page_count=1,
        file_type="txt",
        content_hash=_hash_bytes(file_bytes),
    )


def extract_markdown(file_bytes: bytes) -> ExtractionResult:
    """Extract text from a Markdown file (treated as plain text)."""
    result = extract_text(file_bytes)
    result = ExtractionResult(
        pages=result.pages,
        page_count=result.page_count,
        file_type="md",
        content_hash=result.content_hash,
    )
    return result


# Map file extensions to extractor functions
_EXTRACTORS = {
    ".pdf": extract_pdf,
    ".docx": extract_docx,
    ".txt": extract_text,
    ".md": extract_markdown,
    ".markdown": extract_markdown,
}

SUPPORTED_EXTENSIONS = list(_EXTRACTORS.keys())


def extract(filename: str, file_bytes: bytes) -> ExtractionResult:
    """
    Extract text from a file based on its extension.

    Args:
        filename: Original filename (used to determine type).
        file_bytes: Raw file content as bytes.

    Returns:
        ExtractionResult with pages, page count, type, and hash.

    Raises:
        ValueError: If the file type is not supported.
    """
    ext = Path(filename).suffix.lower()
    extractor = _EXTRACTORS.get(ext)
    if not extractor:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return extractor(file_bytes)
