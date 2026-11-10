"""
Query rewriting for Hastings RAG Studio.

Uses the Groq LLM to rewrite a user question into a form that
retrieves better results — expanding abbreviations, adding context,
and making implicit terms explicit.
"""

from __future__ import annotations

from groq import Groq

from src.config import config


def rewrite_query(question: str, model: str | None = None) -> str:
    """
    Rewrite a question to improve retrieval quality.

    The rewritten query is designed to match document language better.
    If rewriting fails for any reason, the original question is returned.

    Args:
        question: The original user question.
        model: Groq model to use (defaults to config.groq_model).

    Returns:
        Rewritten query string (or original if rewriting fails).
    """
    prompt = f"""You are a search query optimizer for a document retrieval system.

Rewrite the following question into a better search query that will find relevant passages in documents.

Rules:
- Expand abbreviations
- Add relevant synonyms or related terms
- Make implicit concepts explicit
- Keep it concise (one sentence or short phrase)
- Return ONLY the rewritten query, nothing else

Original question: {question}

Rewritten query:"""

    try:
        client = Groq(api_key=config.groq_api_key)
        response = client.chat.completions.create(
            model=model or config.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100,
        )
        rewritten = response.choices[0].message.content.strip()
        # Sanity check — if rewrite is empty or too long, fall back
        if rewritten and len(rewritten) < 500:
            return rewritten
        return question
    except Exception:
        return question
