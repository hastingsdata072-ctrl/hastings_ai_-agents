"""
Evaluation runner for Hastings RAG Studio.

Runs a labelled question set through the retrieval pipeline
and computes precision@k, recall@k, and MRR.

The labelled set is a list of dicts:
  {"question": str, "relevant_chunk_ids": [int, ...]}

Relevant chunk IDs can be found by querying the database and
manually marking which chunks are relevant for each question.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import config
from src.evaluation.metrics import (
    AggregateMetrics,
    RetrievalMetrics,
    aggregate_metrics,
    evaluate_query,
)


@dataclass
class EvalResult:
    """Complete evaluation result."""
    per_query: list[RetrievalMetrics]
    aggregate: AggregateMetrics
    retrieval_mode: str
    k: int


def run_evaluation(
    kb_id: int,
    labelled_questions: list[dict[str, Any]],
    retrieval_mode: str = "vector",
    k: int | None = None,
) -> EvalResult:
    """
    Evaluate retrieval quality on a labelled question set.

    Args:
        kb_id: Knowledge base to evaluate.
        labelled_questions: List of {"question": str, "relevant_chunk_ids": [int]}.
        retrieval_mode: "vector", "hybrid", or "hybrid_rerank".
        k: Evaluation cutoff (defaults to config.top_k).

    Returns:
        EvalResult with per-query and aggregate metrics.
    """
    eval_k = k or config.top_k
    per_query: list[RetrievalMetrics] = []

    for item in labelled_questions:
        question = item["question"]
        relevant_ids = item.get("relevant_chunk_ids", [])

        # Retrieve chunks
        if retrieval_mode == "hybrid":
            from src.retrieval.hybrid_search import hybrid_retrieve
            chunks = hybrid_retrieve(kb_id, question, top_k=eval_k)
        elif retrieval_mode == "hybrid_rerank":
            from src.retrieval.hybrid_search import hybrid_retrieve
            from src.retrieval.reranker import rerank
            candidates = hybrid_retrieve(kb_id, question, top_k=eval_k * 2)
            chunks = rerank(question, candidates, top_k=eval_k)
        else:
            from src.retrieval.vector_search import retrieve
            chunks = retrieve(kb_id, question, top_k=eval_k)

        metrics = evaluate_query(question, chunks, relevant_ids, eval_k)
        per_query.append(metrics)

    agg = aggregate_metrics(per_query)
    return EvalResult(
        per_query=per_query,
        aggregate=agg,
        retrieval_mode=retrieval_mode,
        k=eval_k,
    )
