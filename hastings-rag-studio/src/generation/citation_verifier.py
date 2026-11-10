"""
Citation verification for Hastings RAG Studio.

Checks each sentence in the generated answer against the retrieved
evidence and flags statements that are not supported by any source.

Uses embedding similarity to detect support — no extra API calls needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class VerifiedSentence:
    """A single sentence from the answer with its verification result."""
    text: str
    supported: bool
    best_source: str | None
    confidence: float


@dataclass
class VerificationResult:
    """Full verification result for an answer."""
    sentences: list[VerifiedSentence]
    unsupported_count: int
    support_rate: float  # 0.0 to 1.0


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering out citation tags and short fragments."""
    # Remove citation tags like [S1], [S2]
    clean = re.sub(r"\[S\d+\]", "", text)
    sentences = re.split(r"(?<=[.!?])\s+", clean.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 30]


def verify_citations(
    answer: str,
    chunks: list[dict[str, Any]],
    support_threshold: float = 0.35,
) -> VerificationResult:
    """
    Verify each sentence in the answer against retrieved evidence.

    Args:
        answer: The generated answer text.
        chunks: Retrieved chunks used to generate the answer.
        support_threshold: Minimum cosine similarity to count as supported.

    Returns:
        VerificationResult with per-sentence support status.
    """
    from src.embeddings.embedder import embed_texts

    sentences = _split_sentences(answer)
    if not sentences or not chunks:
        return VerificationResult(sentences=[], unsupported_count=0, support_rate=1.0)

    # Embed all sentences and all chunk contents
    all_texts = sentences + [c["content"] for c in chunks]
    all_embeddings = embed_texts(all_texts)

    sentence_embeddings = all_embeddings[:len(sentences)]
    chunk_embeddings = all_embeddings[len(sentences):]

    verified: list[VerifiedSentence] = []

    for i, sentence in enumerate(sentences):
        best_score = 0.0
        best_source = None

        for j, chunk in enumerate(chunks):
            score = _cosine(sentence_embeddings[i], chunk_embeddings[j])
            if score > best_score:
                best_score = score
                best_source = chunk.get("filename", "unknown")

        supported = best_score >= support_threshold
        verified.append(VerifiedSentence(
            text=sentence,
            supported=supported,
            best_source=best_source if supported else None,
            confidence=round(best_score, 3),
        ))

    unsupported = sum(1 for s in verified if not s.supported)
    support_rate = (len(verified) - unsupported) / len(verified) if verified else 1.0

    return VerificationResult(
        sentences=verified,
        unsupported_count=unsupported,
        support_rate=round(support_rate, 2),
    )
