"""
Prompt builder for Hastings RAG Studio.

Constructs the system and user prompts sent to the Groq LLM.
The LLM is instructed to answer only from the provided context
and to cite sources using [S1], [S2] notation.
"""

from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are a precise document intelligence assistant for Hastings RAG Studio.

Your rules:
1. Answer ONLY using the provided context passages. Do not use outside knowledge.
2. Cite every factual claim with a source tag like [S1], [S2], etc., matching the passage numbers.
3. If the context does not contain enough information to answer the question, say clearly:
   "The documents in this knowledge base do not contain sufficient information to answer this question."
4. Never guess, fabricate, or extrapolate beyond what the context explicitly states.
5. Keep answers clear, structured, and grounded in evidence.
"""


def build_context_block(chunks: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """
    Build the numbered context block and the citation map.

    Args:
        chunks: Retrieved chunks from vector search.

    Returns:
        Tuple of (context_text, sources) where sources maps [S1]... to metadata.
    """
    lines: list[str] = []
    sources: list[dict[str, Any]] = []

    for i, chunk in enumerate(chunks, start=1):
        label = f"[S{i}]"
        page_info = f", page {chunk['page_number']}" if chunk.get("page_number") else ""
        header = f"{label} Source: {chunk['filename']}{page_info} (score: {chunk['score']:.3f})"
        lines.append(f"{header}\n{chunk['content']}")
        sources.append({
            "label": label,
            "filename": chunk["filename"],
            "page_number": chunk.get("page_number"),
            "score": chunk["score"],
            "content": chunk["content"],
        })

    context_text = "\n\n---\n\n".join(lines)
    return context_text, sources


def build_user_prompt(question: str, context_text: str) -> str:
    """Build the user turn prompt with context and question."""
    return f"""Here are the relevant passages from the knowledge base:

{context_text}

---

Question: {question}

Answer using only the passages above. Cite each source as [S1], [S2], etc."""
