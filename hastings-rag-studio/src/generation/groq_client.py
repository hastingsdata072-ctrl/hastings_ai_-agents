"""
Groq API client for Hastings RAG Studio.

Wraps the Groq SDK to generate answers from retrieved context.
The model is always read from config — never hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from groq import Groq

from src.config import config
from src.generation.prompts import (
    SYSTEM_PROMPT,
    build_context_block,
    build_user_prompt,
)

# Module-level client singleton
_client: Groq | None = None


def get_client() -> Groq:
    """Return the Groq client, creating it on first call."""
    global _client
    if _client is None:
        _client = Groq(api_key=config.groq_api_key)
    return _client


@dataclass
class GenerationResult:
    """The result of a single RAG generation call."""
    answer: str
    sources: list[dict[str, Any]]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def generate_answer(
    question: str,
    chunks: list[dict[str, Any]],
    model: str | None = None,
) -> GenerationResult:
    """
    Generate a grounded answer from retrieved chunks.

    Args:
        question: The user's question.
        chunks: Retrieved context chunks from vector search.
        model: Groq model name (defaults to config.groq_model).

    Returns:
        GenerationResult with answer, sources, and token usage.
    """
    if not chunks:
        return GenerationResult(
            answer="The documents in this knowledge base do not contain sufficient information to answer this question.",
            sources=[],
            model=model or config.groq_model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )

    context_text, sources = build_context_block(chunks)
    user_prompt = build_user_prompt(question, context_text)
    selected_model = model or config.groq_model

    client = get_client()
    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,  # Low temperature for factual, grounded answers
        max_tokens=2048,
    )

    answer = response.choices[0].message.content or ""
    usage = response.usage

    return GenerationResult(
        answer=answer,
        sources=sources,
        model=selected_model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
    )
